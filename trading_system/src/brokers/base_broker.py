from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    PARTIAL_FILL = "partial_fill"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class Position:
    """Represents a stock position"""
    def __init__(self, symbol: str, quantity: float, market_value: float, 
                 avg_entry_price: float, unrealized_pnl: float, side: str):
        self.symbol = symbol
        self.quantity = quantity
        self.market_value = market_value
        self.avg_entry_price = avg_entry_price
        self.unrealized_pnl = unrealized_pnl
        self.side = side

class Order:
    """Represents a trading order"""
    def __init__(self, id: str, symbol: str, quantity: float, side: OrderSide,
                 order_type: OrderType, status: OrderStatus, filled_qty: float = 0.0,
                 filled_price: float = 0.0, created_at: datetime = None):
        self.id = id
        self.symbol = symbol
        self.quantity = quantity
        self.side = side
        self.order_type = order_type
        self.status = status
        self.filled_qty = filled_qty
        self.filled_price = filled_price
        self.created_at = created_at or datetime.utcnow()

class BaseBroker(ABC):
    """Abstract base class for broker integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to broker API"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from broker API"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        pass
    
    @abstractmethod
    def get_buying_power(self) -> float:
        """Get available buying power"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, quantity: float, side: OrderSide,
                   order_type: OrderType = OrderType.MARKET, 
                   limit_price: Optional[float] = None,
                   stop_price: Optional[float] = None) -> Optional[Order]:
        """Place a trading order"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        pass
    
    @abstractmethod
    def get_orders(self, symbol: Optional[str] = None, 
                  status: Optional[OrderStatus] = None) -> List[Order]:
        """Get orders (with optional filters)"""
        pass
    
    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for symbol"""
        pass
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        # This is a simplified check - real implementation would check market calendar
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            return False
        # Approximate market hours (9:30 AM - 4:00 PM ET)
        return 9 <= now.hour < 16
    
    def calculate_position_size(self, symbol: str, target_amount: float, 
                              current_price: float) -> int:
        """Calculate number of shares to buy for target dollar amount"""
        if current_price <= 0:
            return 0
        
        buying_power = self.get_buying_power()
        max_shares_by_power = int(buying_power / current_price)
        target_shares = int(target_amount / current_price)
        
        return min(max_shares_by_power, target_shares)
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        positions = self.get_positions()
        return sum(pos.market_value for pos in positions)
    
    def validate_order(self, symbol: str, quantity: float, side: OrderSide) -> tuple[bool, str]:
        """Validate order before placing"""
        if not self.is_connected:
            return False, "Not connected to broker"
        
        if quantity <= 0:
            return False, "Quantity must be positive"
        
        if side == OrderSide.BUY:
            # Check buying power
            quote = self.get_quote(symbol)
            if not quote:
                return False, f"Cannot get quote for {symbol}"
            
            price = quote.get('price', 0)
            required_amount = quantity * price
            buying_power = self.get_buying_power()
            
            if required_amount > buying_power:
                return False, f"Insufficient buying power: need ${required_amount:.2f}, have ${buying_power:.2f}"
        
        elif side == OrderSide.SELL:
            # Check if we have enough shares
            position = self.get_position(symbol)
            if not position or position.quantity < quantity:
                current_qty = position.quantity if position else 0
                return False, f"Insufficient shares: need {quantity}, have {current_qty}"
        
        return True, "Order validation passed"