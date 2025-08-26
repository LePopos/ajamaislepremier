from typing import Dict, List, Optional, Any
from datetime import datetime
import random
import logging
from .base_broker import BaseBroker, Order, Position, OrderType, OrderStatus, OrderSide

logger = logging.getLogger(__name__)

class MockBroker(BaseBroker):
    """Mock broker for testing and simulation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Simulated account data
        self.account_balance = 10000.0  # $10k starting balance
        self.positions = {}  # symbol -> position
        self.orders = {}  # order_id -> order
        self.next_order_id = 1
        
        # Mock market data (simplified)
        self.mock_prices = {
            'AAPL': 182.50,
            'MSFT': 415.30,
            'GOOGL': 2850.20,
            'TSLA': 248.42,
            'NVDA': 645.20,
            'AMZN': 3345.10
        }
    
    def connect(self) -> bool:
        """Connect to mock broker (always succeeds)"""
        self.is_connected = True
        logger.info("Connected to Mock Broker (simulation mode)")
        return True
    
    def disconnect(self):
        """Disconnect from mock broker"""
        self.is_connected = False
        logger.info("Disconnected from Mock Broker")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get mock account information"""
        portfolio_value = self.get_portfolio_value()
        return {
            'account_number': 'MOCK123456',
            'status': 'ACTIVE',
            'currency': 'USD',
            'cash': self.account_balance,
            'portfolio_value': portfolio_value,
            'equity': self.account_balance + portfolio_value,
            'buying_power': self.account_balance,
            'day_trade_count': 0,
            'account_type': 'CASH'
        }
    
    def get_buying_power(self) -> float:
        """Get available buying power"""
        return self.account_balance
    
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        positions = []
        for symbol, pos_data in self.positions.items():
            current_price = self._get_mock_price(symbol)
            market_value = pos_data['quantity'] * current_price
            unrealized_pnl = market_value - (pos_data['quantity'] * pos_data['avg_entry_price'])
            
            position = Position(
                symbol=symbol,
                quantity=pos_data['quantity'],
                market_value=market_value,
                avg_entry_price=pos_data['avg_entry_price'],
                unrealized_pnl=unrealized_pnl,
                side='long' if pos_data['quantity'] > 0 else 'short'
            )
            positions.append(position)
        
        return positions
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        if symbol not in self.positions:
            return None
        
        pos_data = self.positions[symbol]
        current_price = self._get_mock_price(symbol)
        market_value = pos_data['quantity'] * current_price
        unrealized_pnl = market_value - (pos_data['quantity'] * pos_data['avg_entry_price'])
        
        return Position(
            symbol=symbol,
            quantity=pos_data['quantity'],
            market_value=market_value,
            avg_entry_price=pos_data['avg_entry_price'],
            unrealized_pnl=unrealized_pnl,
            side='long' if pos_data['quantity'] > 0 else 'short'
        )
    
    def place_order(self, symbol: str, quantity: float, side: OrderSide,
                   order_type: OrderType = OrderType.MARKET, 
                   limit_price: Optional[float] = None,
                   stop_price: Optional[float] = None) -> Optional[Order]:
        """Place a mock trading order"""
        
        # Validate order
        is_valid, error_msg = self.validate_order(symbol, quantity, side)
        if not is_valid:
            logger.error(f"Mock order validation failed: {error_msg}")
            return None
        
        order_id = str(self.next_order_id)
        self.next_order_id += 1
        
        # Simulate order execution
        current_price = self._get_mock_price(symbol)
        
        # Add some random slippage for realism (±0.1%)
        slippage = random.uniform(-0.001, 0.001)
        execution_price = current_price * (1 + slippage)
        
        # Create order
        order = Order(
            id=order_id,
            symbol=symbol,
            quantity=quantity,
            side=side,
            order_type=order_type,
            status=OrderStatus.FILLED,  # Mock orders fill immediately
            filled_qty=quantity,
            filled_price=execution_price,
            created_at=datetime.utcnow()
        )
        
        # Store order
        self.orders[order_id] = order
        
        # Update positions and account balance
        self._execute_order(symbol, quantity, side, execution_price)
        
        logger.info(f"Mock order executed: {side.value} {quantity} shares of {symbol} at ${execution_price:.2f}")
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order (mock always succeeds)"""
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELED
            return True
        return False
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        return self.orders.get(order_id)
    
    def get_orders(self, symbol: Optional[str] = None, 
                  status: Optional[OrderStatus] = None) -> List[Order]:
        """Get orders (with optional filters)"""
        orders = list(self.orders.values())
        
        if symbol:
            orders = [o for o in orders if o.symbol.upper() == symbol.upper()]
        
        if status:
            orders = [o for o in orders if o.status == status]
        
        return orders
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get mock real-time quote for symbol"""
        price = self._get_mock_price(symbol)
        
        if price is None:
            return {}
        
        # Add some random spread
        spread = price * 0.001  # 0.1% spread
        bid = price - spread/2
        ask = price + spread/2
        
        return {
            'symbol': symbol.upper(),
            'price': price,
            'bid': bid,
            'ask': ask,
            'bid_size': random.randint(100, 1000),
            'ask_size': random.randint(100, 1000),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_mock_price(self, symbol: str) -> Optional[float]:
        """Get mock price for symbol"""
        base_price = self.mock_prices.get(symbol.upper())
        if base_price is None:
            return None
        
        # Add some random price movement (±2%)
        movement = random.uniform(-0.02, 0.02)
        return base_price * (1 + movement)
    
    def _execute_order(self, symbol: str, quantity: float, side: OrderSide, price: float):
        """Execute order and update positions/balance"""
        
        total_cost = quantity * price
        
        if side == OrderSide.BUY:
            # Buy order: deduct cash, add to position
            self.account_balance -= total_cost
            
            if symbol in self.positions:
                # Update existing position
                existing_qty = self.positions[symbol]['quantity']
                existing_cost = existing_qty * self.positions[symbol]['avg_entry_price']
                
                new_qty = existing_qty + quantity
                new_avg_price = (existing_cost + total_cost) / new_qty
                
                self.positions[symbol] = {
                    'quantity': new_qty,
                    'avg_entry_price': new_avg_price
                }
            else:
                # Create new position
                self.positions[symbol] = {
                    'quantity': quantity,
                    'avg_entry_price': price
                }
                
        elif side == OrderSide.SELL:
            # Sell order: add cash, reduce position
            self.account_balance += total_cost
            
            if symbol in self.positions:
                self.positions[symbol]['quantity'] -= quantity
                
                # Remove position if quantity is zero
                if self.positions[symbol]['quantity'] <= 0:
                    del self.positions[symbol]
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        total_value = 0.0
        
        for symbol, pos_data in self.positions.items():
            current_price = self._get_mock_price(symbol)
            if current_price:
                total_value += pos_data['quantity'] * current_price
        
        return total_value
    
    def reset_account(self, starting_balance: float = 10000.0):
        """Reset mock account to starting state"""
        self.account_balance = starting_balance
        self.positions = {}
        self.orders = {}
        self.next_order_id = 1
        logger.info(f"Mock account reset with ${starting_balance:.2f} balance")