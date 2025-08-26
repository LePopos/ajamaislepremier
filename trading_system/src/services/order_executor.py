from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models.stock_models import (
    TradingSignal, TradingOrder, Position, Stock,
    get_session_factory, SignalType, OrderStatus
)
from ..brokers.base_broker import BaseBroker, OrderSide, OrderType
from ..services.notification_service import NotificationService
from ..config.config import config

logger = logging.getLogger(__name__)

class OrderExecutor:
    """Service for executing trading orders based on signals"""
    
    def __init__(self, broker: BaseBroker, notification_service: Optional[NotificationService] = None):
        self.broker = broker
        self.notification_service = notification_service
        self.session_factory = get_session_factory(config.database_url)
        
        # Execution parameters
        self.max_position_size = config.max_position_size
        self.max_daily_trades = config.max_daily_trades
        self.dry_run = config.get('dry_run', True)  # Safety: default to dry run
    
    def execute_signal(self, signal_id: int) -> bool:
        """Execute a trading signal"""
        
        try:
            with self.session_factory() as db:
                # Get signal and stock info
                signal = db.query(TradingSignal).filter(TradingSignal.id == signal_id).first()
                if not signal or not signal.is_active:
                    logger.warning(f"Signal {signal_id} not found or inactive")
                    return False
                
                stock = db.query(Stock).filter(Stock.id == signal.stock_id).first()
                if not stock:
                    logger.error(f"Stock not found for signal {signal_id}")
                    return False
                
                # Check daily trade limits
                if not self._check_daily_limits(db):
                    logger.warning("Daily trade limit reached")
                    return False
                
                # Execute based on signal type
                if signal.signal_type == SignalType.BUY.value:
                    return self._execute_buy_signal(db, signal, stock)
                elif signal.signal_type == SignalType.SELL.value:
                    return self._execute_sell_signal(db, signal, stock)
                else:
                    logger.info(f"HOLD signal for {stock.ticker} - no action taken")
                    return True
                    
        except Exception as e:
            logger.error(f"Error executing signal {signal_id}: {e}")
            return False
    
    def _execute_buy_signal(self, db: Session, signal: TradingSignal, stock: Stock) -> bool:
        """Execute a BUY signal"""
        
        try:
            # Get current market price
            quote = self.broker.get_quote(stock.ticker)
            if not quote or 'price' not in quote:
                logger.error(f"Cannot get current price for {stock.ticker}")
                return False
            
            current_price = quote['price']
            
            # Calculate position size
            target_amount = min(signal.position_size_usd or self.max_position_size, self.max_position_size)
            quantity = self.broker.calculate_position_size(stock.ticker, target_amount, current_price)
            
            if quantity <= 0:
                logger.warning(f"Cannot calculate valid position size for {stock.ticker}")
                return False
            
            # Create order record in database first
            order_record = TradingOrder(
                stock_id=stock.id,
                signal_id=signal.id,
                order_type="BUY",
                quantity=quantity,
                price=current_price,
                status="PENDING"
            )
            db.add(order_record)
            db.commit()
            db.refresh(order_record)
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would buy {quantity} shares of {stock.ticker} at ~${current_price:.2f}")
                order_record.status = "FILLED"  # Simulate successful execution
                order_record.executed_price = current_price
                order_record.executed_at = datetime.utcnow()
                db.commit()
                
                # Create simulated position
                self._create_position(db, stock, quantity, current_price, signal)
                return True
            
            # Place actual order
            broker_order = self.broker.place_order(
                symbol=stock.ticker,
                quantity=quantity,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET
            )
            
            if broker_order:
                # Update order record with broker order ID
                order_record.broker_order_id = broker_order.id
                order_record.executed_price = broker_order.filled_price if broker_order.filled_price > 0 else current_price
                order_record.status = broker_order.status.value.upper()
                
                if broker_order.status.value in ['filled', 'partial_fill']:
                    order_record.executed_at = datetime.utcnow()
                    # Create position record
                    self._create_position(db, stock, broker_order.filled_qty or quantity, 
                                        broker_order.filled_price or current_price, signal)
                
                db.commit()
                
                logger.info(f"Buy order placed: {quantity} shares of {stock.ticker}")
                
                # Send notification
                if self.notification_service:
                    self._send_execution_notification(signal, stock, "BUY", quantity, current_price)
                
                return True
            else:
                # Order failed
                order_record.status = "FAILED"
                order_record.error_message = "Failed to place order with broker"
                db.commit()
                return False
                
        except Exception as e:
            logger.error(f"Error executing buy signal: {e}")
            return False
    
    def _execute_sell_signal(self, db: Session, signal: TradingSignal, stock: Stock) -> bool:
        """Execute a SELL signal"""
        
        try:
            # Check if we have a position to sell
            position = db.query(Position).filter(
                Position.stock_id == stock.id,
                Position.is_open == True
            ).first()
            
            if not position:
                logger.warning(f"No open position found for {stock.ticker} - cannot sell")
                return False
            
            # Get current market price
            quote = self.broker.get_quote(stock.ticker)
            if not quote or 'price' not in quote:
                logger.error(f"Cannot get current price for {stock.ticker}")
                return False
            
            current_price = quote['price']
            quantity = position.quantity
            
            # Create order record
            order_record = TradingOrder(
                stock_id=stock.id,
                signal_id=signal.id,
                order_type="SELL",
                quantity=quantity,
                price=current_price,
                status="PENDING"
            )
            db.add(order_record)
            db.commit()
            db.refresh(order_record)
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would sell {quantity} shares of {stock.ticker} at ~${current_price:.2f}")
                order_record.status = "FILLED"
                order_record.executed_price = current_price
                order_record.executed_at = datetime.utcnow()
                
                # Close position
                position.is_open = False
                position.exit_date = datetime.utcnow()
                position.exit_price = current_price
                position.pnl = (current_price - position.entry_price) * quantity
                position.pnl_percent = (position.pnl / (position.entry_price * quantity)) * 100
                
                db.commit()
                return True
            
            # Place actual sell order
            broker_order = self.broker.place_order(
                symbol=stock.ticker,
                quantity=quantity,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET
            )
            
            if broker_order:
                order_record.broker_order_id = broker_order.id
                order_record.executed_price = broker_order.filled_price if broker_order.filled_price > 0 else current_price
                order_record.status = broker_order.status.value.upper()
                
                if broker_order.status.value in ['filled', 'partial_fill']:
                    order_record.executed_at = datetime.utcnow()
                    
                    # Close position
                    filled_price = broker_order.filled_price or current_price
                    position.is_open = False
                    position.exit_date = datetime.utcnow()
                    position.exit_price = filled_price
                    position.pnl = (filled_price - position.entry_price) * quantity
                    position.pnl_percent = (position.pnl / (position.entry_price * quantity)) * 100
                
                db.commit()
                
                logger.info(f"Sell order placed: {quantity} shares of {stock.ticker}")
                
                # Send notification
                if self.notification_service:
                    pnl = (current_price - position.entry_price) * quantity
                    self._send_execution_notification(signal, stock, "SELL", quantity, current_price, pnl)
                
                return True
            else:
                order_record.status = "FAILED"
                order_record.error_message = "Failed to place sell order with broker"
                db.commit()
                return False
                
        except Exception as e:
            logger.error(f"Error executing sell signal: {e}")
            return False
    
    def _create_position(self, db: Session, stock: Stock, quantity: float, 
                        entry_price: float, signal: TradingSignal):
        """Create a new position record"""
        
        position = Position(
            stock_id=stock.id,
            quantity=quantity,
            entry_price=entry_price,
            entry_date=datetime.utcnow(),
            stop_loss_price=signal.stop_loss_price,
            is_open=True
        )
        
        db.add(position)
        db.commit()
    
    def _check_daily_limits(self, db: Session) -> bool:
        """Check if we haven't exceeded daily trading limits"""
        
        today = datetime.utcnow().date()
        daily_orders = db.query(TradingOrder).filter(
            TradingOrder.created_at >= today,
            TradingOrder.status == "FILLED"
        ).count()
        
        return daily_orders < self.max_daily_trades
    
    def _send_execution_notification(self, signal: TradingSignal, stock: Stock, 
                                   action: str, quantity: float, price: float, 
                                   pnl: Optional[float] = None):
        """Send notification about order execution"""
        
        try:
            if not self.notification_service:
                return
            
            subject = f"🎯 Order Executed: {action} {stock.ticker}"
            
            pnl_text = ""
            if pnl is not None:
                pnl_text = f"\nP&L: ${pnl:+.2f} ({(pnl/(price*quantity))*100:+.1f}%)"
            
            dry_run_text = "\n⚠️ DRY RUN MODE - No actual trades executed" if self.dry_run else ""
            
            message = f"""
Order Executed Successfully!

Action: {action}
Symbol: {stock.ticker}
Quantity: {quantity} shares
Price: ${price:.2f}
Total: ${price * quantity:.2f}{pnl_text}

Signal Confidence: {signal.confidence:.1%}
Reasoning: {signal.reasoning}{dry_run_text}

Executed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
            """
            
            # Send via webhook if configured (simpler than full email for executions)
            if hasattr(self.notification_service, 'webhook_url') and self.notification_service.webhook_url:
                webhook_data = {
                    'text': subject,
                    'attachments': [{
                        'color': 'good' if action == 'BUY' else 'warning',
                        'title': f"{action} Order Executed",
                        'text': message,
                        'footer': 'Trading System',
                        'ts': int(datetime.utcnow().timestamp())
                    }]
                }
                self.notification_service.send_webhook_notification(webhook_data)
                
        except Exception as e:
            logger.error(f"Error sending execution notification: {e}")
    
    def check_stop_losses(self) -> List[int]:
        """Check all open positions for stop loss triggers"""
        
        triggered_signals = []
        
        try:
            with self.session_factory() as db:
                # Get all open positions with stop losses
                positions = db.query(Position, Stock).join(Stock).filter(
                    Position.is_open == True,
                    Position.stop_loss_price.isnot(None)
                ).all()
                
                for position, stock in positions:
                    # Get current price
                    quote = self.broker.get_quote(stock.ticker)
                    if not quote or 'price' not in quote:
                        continue
                    
                    current_price = quote['price']
                    
                    # Check if stop loss is triggered
                    if current_price <= position.stop_loss_price:
                        logger.warning(f"Stop loss triggered for {stock.ticker}: "
                                     f"${current_price:.2f} <= ${position.stop_loss_price:.2f}")
                        
                        # Create emergency sell signal
                        emergency_signal = TradingSignal(
                            stock_id=stock.id,
                            signal_type=SignalType.SELL.value,
                            confidence=1.0,
                            reasoning=f"STOP LOSS TRIGGERED at ${current_price:.2f}",
                            price_when_generated=current_price,
                            position_size_usd=current_price * position.quantity,
                            generated_at=datetime.utcnow(),
                            expires_at=datetime.utcnow() + timedelta(hours=1)
                        )
                        
                        db.add(emergency_signal)
                        db.commit()
                        db.refresh(emergency_signal)
                        
                        # Execute immediately
                        if self.execute_signal(emergency_signal.id):
                            triggered_signals.append(emergency_signal.id)
                
        except Exception as e:
            logger.error(f"Error checking stop losses: {e}")
        
        return triggered_signals
    
    def auto_execute_signals(self) -> Dict[str, int]:
        """Automatically execute all pending high-confidence signals"""
        
        results = {
            'executed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            with self.session_factory() as db:
                # Get active signals above confidence threshold
                min_confidence = config.get('auto_execute_confidence', 0.8)
                
                active_signals = db.query(TradingSignal).filter(
                    TradingSignal.is_active == True,
                    TradingSignal.confidence >= min_confidence,
                    TradingSignal.signal_type.in_([SignalType.BUY.value, SignalType.SELL.value])
                ).all()
                
                for signal in active_signals:
                    # Check if already executed
                    existing_order = db.query(TradingOrder).filter(
                        TradingOrder.signal_id == signal.id
                    ).first()
                    
                    if existing_order:
                        results['skipped'] += 1
                        continue
                    
                    # Execute signal
                    if self.execute_signal(signal.id):
                        results['executed'] += 1
                        signal.is_active = False  # Deactivate after execution
                    else:
                        results['failed'] += 1
                
                db.commit()
                
        except Exception as e:
            logger.error(f"Error in auto-execute signals: {e}")
        
        return results