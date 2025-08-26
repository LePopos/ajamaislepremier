from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from sqlalchemy.orm import Session

from ..models.stock_models import (
    Stock, PriceData, Recommendation, TradingSignal, Position,
    SignalType, TradingSignalCreate
)
from ..api.tipranks_client import TipRanksClient
from ..api.alpha_vantage_client import AlphaVantageClient
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class SignalGenerator:
    """Generate trading signals based on TipRanks recommendations and technical analysis"""
    
    def __init__(self, tipranks_client: TipRanksClient, alpha_vantage_client: AlphaVantageClient, 
                 config: Dict, notification_service: Optional[NotificationService] = None):
        self.tipranks = tipranks_client
        self.alpha_vantage = alpha_vantage_client
        self.config = config
        self.notification_service = notification_service
        
        # Signal generation parameters
        self.min_smart_score_buy = config.get('min_smart_score', 8)
        self.max_smart_score_sell = config.get('max_smart_score', 3)
        self.min_confidence = config.get('min_confidence', 0.7)
        self.max_position_size = config.get('max_position_size', 1000.0)
        self.stop_loss_percentage = config.get('stop_loss_percentage', -5.0)
    
    def generate_signals_for_watchlist(self, db: Session, tickers: List[str]) -> List[TradingSignal]:
        """Generate signals for a list of tickers"""
        signals = []
        
        for ticker in tickers:
            try:
                signal = self.generate_signal(db, ticker)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating signal for {ticker}: {e}")
                continue
        
        return signals
    
    def generate_signal(self, db: Session, ticker: str) -> Optional[TradingSignal]:
        """Generate a trading signal for a single ticker"""
        try:
            # Get or create stock record
            stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
            if not stock:
                stock = Stock(ticker=ticker.upper())
                db.add(stock)
                db.commit()
                db.refresh(stock)
            
            # Get latest recommendation and price data
            latest_recommendation = self._get_latest_recommendation(db, stock.id)
            current_price = self._get_current_price(db, ticker)
            
            if not latest_recommendation or not current_price:
                logger.warning(f"Missing data for {ticker}: rec={latest_recommendation is not None}, price={current_price is not None}")
                return None
            
            # Check if we already have an active signal
            active_signal = db.query(TradingSignal).filter(
                TradingSignal.stock_id == stock.id,
                TradingSignal.is_active == True
            ).first()
            
            # Generate new signal based on current conditions
            signal_data = self._analyze_conditions(
                latest_recommendation, 
                current_price, 
                stock, 
                db
            )
            
            if not signal_data:
                return None
            
            # If we have an active signal, check if we should update or replace it
            if active_signal:
                if signal_data['signal_type'] != SignalType(active_signal.signal_type):
                    # Deactivate old signal and create new one
                    active_signal.is_active = False
                    db.commit()
                else:
                    # Keep existing signal if it's the same type
                    return active_signal
            
            # Create new signal
            new_signal = TradingSignal(
                stock_id=stock.id,
                signal_type=signal_data['signal_type'].value,
                confidence=signal_data['confidence'],
                reasoning=signal_data['reasoning'],
                price_when_generated=current_price,
                target_price=signal_data.get('target_price'),
                stop_loss_price=signal_data.get('stop_loss_price'),
                position_size_usd=signal_data.get('position_size_usd'),
                expires_at=datetime.utcnow() + timedelta(hours=24)  # Signal expires in 24h
            )
            
            db.add(new_signal)
            db.commit()
            db.refresh(new_signal)
            
            logger.info(f"Generated {signal_data['signal_type'].value} signal for {ticker} "
                       f"with confidence {signal_data['confidence']:.2f}")
            
            # Send notification if enabled
            if self.notification_service and self.config.get('send_signal_alerts', True):
                try:
                    recommendation = self._get_latest_recommendation(db, stock.id)
                    self.notification_service.send_signal_alert(new_signal, stock, recommendation)
                except Exception as e:
                    logger.error(f"Failed to send notification for {ticker}: {e}")
            
            return new_signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {ticker}: {e}")
            db.rollback()
            return None
    
    def _get_latest_recommendation(self, db: Session, stock_id: int) -> Optional[Recommendation]:
        """Get the most recent recommendation for a stock"""
        return db.query(Recommendation).filter(
            Recommendation.stock_id == stock_id
        ).order_by(Recommendation.timestamp.desc()).first()
    
    def _get_current_price(self, db: Session, ticker: str) -> Optional[float]:
        """Get current price for a ticker"""
        # First try to get from database (recent price data)
        stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
        if stock:
            recent_price = db.query(PriceData).filter(
                PriceData.stock_id == stock.id,
                PriceData.timestamp > datetime.utcnow() - timedelta(minutes=30)
            ).order_by(PriceData.timestamp.desc()).first()
            
            if recent_price:
                return recent_price.price
        
        # If no recent price in DB, fetch from API
        try:
            quote_data = self.alpha_vantage.get_real_time_quote(ticker)
            return quote_data.get('price') if quote_data else None
        except Exception as e:
            logger.error(f"Error fetching current price for {ticker}: {e}")
            return None
    
    def _analyze_conditions(self, recommendation: Recommendation, current_price: float, 
                          stock: Stock, db: Session) -> Optional[Dict]:
        """Analyze market conditions and generate signal data"""
        
        signal_components = []
        total_confidence = 0.0
        reasoning_parts = []
        
        # 1. TipRanks Smart Score Analysis
        if recommendation.smart_score:
            if recommendation.smart_score >= self.min_smart_score_buy:
                signal_components.append(('BUY', 0.4))  # 40% weight for smart score
                reasoning_parts.append(f"Strong Smart Score: {recommendation.smart_score}/10")
            elif recommendation.smart_score <= self.max_smart_score_sell:
                signal_components.append(('SELL', 0.4))
                reasoning_parts.append(f"Weak Smart Score: {recommendation.smart_score}/10")
            else:
                signal_components.append(('HOLD', 0.2))
                reasoning_parts.append(f"Neutral Smart Score: {recommendation.smart_score}/10")
        
        # 2. Price Target Analysis
        if recommendation.mean_price_target and current_price:
            upside_potential = (recommendation.mean_price_target - current_price) / current_price
            
            if upside_potential > 0.15:  # 15%+ upside
                signal_components.append(('BUY', 0.3))  # 30% weight
                reasoning_parts.append(f"Upside potential: {upside_potential:.1%}")
            elif upside_potential < -0.10:  # 10%+ downside
                signal_components.append(('SELL', 0.3))
                reasoning_parts.append(f"Downside risk: {upside_potential:.1%}")
            else:
                signal_components.append(('HOLD', 0.1))
                reasoning_parts.append(f"Limited price movement expected: {upside_potential:.1%}")
        
        # 3. Sentiment Analysis
        if recommendation.bullish_percent and recommendation.bearish_percent:
            net_bullish = recommendation.bullish_percent - recommendation.bearish_percent
            
            if net_bullish > 20:  # Strong bullish sentiment
                signal_components.append(('BUY', 0.2))  # 20% weight
                reasoning_parts.append(f"Bullish sentiment: {recommendation.bullish_percent}% vs {recommendation.bearish_percent}%")
            elif net_bullish < -20:  # Strong bearish sentiment
                signal_components.append(('SELL', 0.2))
                reasoning_parts.append(f"Bearish sentiment: {recommendation.bearish_percent}% vs {recommendation.bullish_percent}%")
            else:
                signal_components.append(('HOLD', 0.1))
                reasoning_parts.append("Neutral sentiment")
        
        # 4. Check existing positions to avoid overexposure
        existing_position = db.query(Position).filter(
            Position.stock_id == stock.id,
            Position.is_open == True
        ).first()
        
        if existing_position:
            # If we already have a position, be more conservative
            signal_components = [(action, weight * 0.7) for action, weight in signal_components]
            reasoning_parts.append(f"Existing position: {existing_position.quantity} shares")
        
        # Calculate weighted signal
        buy_weight = sum(weight for action, weight in signal_components if action == 'BUY')
        sell_weight = sum(weight for action, weight in signal_components if action == 'SELL')
        hold_weight = sum(weight for action, weight in signal_components if action == 'HOLD')
        
        # Determine final signal
        if buy_weight > sell_weight and buy_weight > hold_weight:
            signal_type = SignalType.BUY
            confidence = min(buy_weight, 1.0)
        elif sell_weight > buy_weight and sell_weight > hold_weight:
            signal_type = SignalType.SELL
            confidence = min(sell_weight, 1.0)
        else:
            signal_type = SignalType.HOLD
            confidence = min(max(buy_weight, sell_weight, hold_weight), 1.0)
        
        # Only generate signals above minimum confidence threshold
        if confidence < self.min_confidence:
            return None
        
        # Calculate position sizing and risk management
        position_size_usd = self._calculate_position_size(confidence, current_price)
        target_price = recommendation.mean_price_target if signal_type == SignalType.BUY else None
        stop_loss_price = self._calculate_stop_loss(signal_type, current_price)
        
        return {
            'signal_type': signal_type,
            'confidence': confidence,
            'reasoning': '; '.join(reasoning_parts),
            'target_price': target_price,
            'stop_loss_price': stop_loss_price,
            'position_size_usd': position_size_usd
        }
    
    def _calculate_position_size(self, confidence: float, current_price: float) -> float:
        """Calculate position size based on confidence and risk parameters"""
        # Base position size scaled by confidence
        base_size = self.max_position_size * confidence
        
        # Ensure we don't exceed maximum position size
        return min(base_size, self.max_position_size)
    
    def _calculate_stop_loss(self, signal_type: SignalType, current_price: float) -> Optional[float]:
        """Calculate stop loss price"""
        if signal_type == SignalType.BUY:
            # Stop loss below entry price
            return current_price * (1 + self.stop_loss_percentage / 100)
        elif signal_type == SignalType.SELL and current_price:
            # For short positions, stop loss above entry price
            return current_price * (1 - self.stop_loss_percentage / 100)
        
        return None
    
    def update_signal_prices(self, db: Session, signal_id: int) -> bool:
        """Update signal with current market price"""
        try:
            signal = db.query(TradingSignal).filter(TradingSignal.id == signal_id).first()
            if not signal or not signal.is_active:
                return False
            
            stock = db.query(Stock).filter(Stock.id == signal.stock_id).first()
            if not stock:
                return False
            
            current_price = self._get_current_price(db, stock.ticker)
            if not current_price:
                return False
            
            # Check if stop loss should be triggered
            if (signal.signal_type == SignalType.BUY.value and 
                signal.stop_loss_price and 
                current_price <= signal.stop_loss_price):
                
                signal.is_active = False
                reasoning_update = f"{signal.reasoning}; STOP LOSS TRIGGERED at ${current_price}"
                signal.reasoning = reasoning_update
                
                logger.warning(f"Stop loss triggered for {stock.ticker} at ${current_price}")
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating signal prices for signal {signal_id}: {e}")
            db.rollback()
            return False
    
    def cleanup_expired_signals(self, db: Session) -> int:
        """Remove expired signals"""
        try:
            expired_count = db.query(TradingSignal).filter(
                TradingSignal.expires_at < datetime.utcnow(),
                TradingSignal.is_active == True
            ).update({TradingSignal.is_active: False})
            
            db.commit()
            
            if expired_count > 0:
                logger.info(f"Deactivated {expired_count} expired signals")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired signals: {e}")
            db.rollback()
            return 0