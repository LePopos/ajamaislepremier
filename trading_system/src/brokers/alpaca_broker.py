import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from .base_broker import BaseBroker, Order, Position, OrderType, OrderStatus, OrderSide

logger = logging.getLogger(__name__)

class AlpacaBroker(BaseBroker):
    """Alpaca broker integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.secret_key = config.get('secret_key')
        self.paper_trading = config.get('paper_trading', True)
        
        # Set base URL based on environment
        if self.paper_trading:
            self.base_url = "https://paper-api.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"
        
        self.headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key,
            'Content-Type': 'application/json'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def connect(self) -> bool:
        """Connect to Alpaca API"""
        try:
            # Test connection by getting account info
            response = self.session.get(f"{self.base_url}/v2/account")
            if response.status_code == 200:
                self.is_connected = True
                account_info = response.json()
                logger.info(f"Connected to Alpaca {'Paper' if self.paper_trading else 'Live'} Trading")
                logger.info(f"Account status: {account_info.get('status', 'Unknown')}")
                return True
            else:
                logger.error(f"Failed to connect to Alpaca: {response.status_code} {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Alpaca: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Alpaca API"""
        self.is_connected = False
        if hasattr(self, 'session'):
            self.session.close()
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            response = self.session.get(f"{self.base_url}/v2/account")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get account info: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_buying_power(self) -> float:
        """Get available buying power"""
        account_info = self.get_account_info()
        return float(account_info.get('buying_power', 0))
    
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            response = self.session.get(f"{self.base_url}/v2/positions")
            if response.status_code == 200:
                positions_data = response.json()
                positions = []
                
                for pos_data in positions_data:
                    position = Position(
                        symbol=pos_data['symbol'],
                        quantity=float(pos_data['qty']),
                        market_value=float(pos_data['market_value']),
                        avg_entry_price=float(pos_data['avg_entry_price']),
                        unrealized_pnl=float(pos_data['unrealized_pl']),
                        side=pos_data['side']
                    )
                    positions.append(position)
                
                return positions
            else:
                logger.error(f"Failed to get positions: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        try:
            response = self.session.get(f"{self.base_url}/v2/positions/{symbol}")
            if response.status_code == 200:
                pos_data = response.json()
                return Position(
                    symbol=pos_data['symbol'],
                    quantity=float(pos_data['qty']),
                    market_value=float(pos_data['market_value']),
                    avg_entry_price=float(pos_data['avg_entry_price']),
                    unrealized_pnl=float(pos_data['unrealized_pl']),
                    side=pos_data['side']
                )
            elif response.status_code == 404:
                return None  # No position found
            else:
                logger.error(f"Failed to get position for {symbol}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return None
    
    def place_order(self, symbol: str, quantity: float, side: OrderSide,
                   order_type: OrderType = OrderType.MARKET, 
                   limit_price: Optional[float] = None,
                   stop_price: Optional[float] = None) -> Optional[Order]:
        """Place a trading order"""
        
        # Validate order first
        is_valid, error_msg = self.validate_order(symbol, quantity, side)
        if not is_valid:
            logger.error(f"Order validation failed: {error_msg}")
            return None
        
        try:
            # Prepare order data
            order_data = {
                'symbol': symbol.upper(),
                'qty': str(int(quantity)),  # Alpaca expects integer shares
                'side': side.value,
                'type': order_type.value,
                'time_in_force': 'day'
            }
            
            # Add price parameters based on order type
            if order_type == OrderType.LIMIT and limit_price:
                order_data['limit_price'] = str(limit_price)
            elif order_type == OrderType.STOP and stop_price:
                order_data['stop_price'] = str(stop_price)
            elif order_type == OrderType.STOP_LIMIT and limit_price and stop_price:
                order_data['limit_price'] = str(limit_price)
                order_data['stop_price'] = str(stop_price)
            
            # Place order
            response = self.session.post(f"{self.base_url}/v2/orders", json=order_data)
            
            if response.status_code == 201:
                order_response = response.json()
                order = Order(
                    id=order_response['id'],
                    symbol=order_response['symbol'],
                    quantity=float(order_response['qty']),
                    side=OrderSide(order_response['side']),
                    order_type=OrderType(order_response['type']),
                    status=self._map_alpaca_status(order_response['status']),
                    filled_qty=float(order_response.get('filled_qty', 0)),
                    filled_price=float(order_response.get('filled_avg_price', 0)) if order_response.get('filled_avg_price') else 0,
                    created_at=datetime.fromisoformat(order_response['created_at'].replace('Z', '+00:00'))
                )
                
                logger.info(f"Order placed: {side.value} {quantity} shares of {symbol}")
                return order
            else:
                logger.error(f"Failed to place order: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            response = self.session.delete(f"{self.base_url}/v2/orders/{order_id}")
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return False
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        try:
            response = self.session.get(f"{self.base_url}/v2/orders/{order_id}")
            if response.status_code == 200:
                order_data = response.json()
                return Order(
                    id=order_data['id'],
                    symbol=order_data['symbol'],
                    quantity=float(order_data['qty']),
                    side=OrderSide(order_data['side']),
                    order_type=OrderType(order_data['type']),
                    status=self._map_alpaca_status(order_data['status']),
                    filled_qty=float(order_data.get('filled_qty', 0)),
                    filled_price=float(order_data.get('filled_avg_price', 0)) if order_data.get('filled_avg_price') else 0,
                    created_at=datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00'))
                )
            else:
                logger.error(f"Failed to get order {order_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    def get_orders(self, symbol: Optional[str] = None, 
                  status: Optional[OrderStatus] = None) -> List[Order]:
        """Get orders (with optional filters)"""
        try:
            params = {}
            if symbol:
                params['symbols'] = symbol.upper()
            if status:
                # Map our status to Alpaca status
                alpaca_status = self._map_to_alpaca_status(status)
                if alpaca_status:
                    params['status'] = alpaca_status
            
            response = self.session.get(f"{self.base_url}/v2/orders", params=params)
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = []
                
                for order_data in orders_data:
                    order = Order(
                        id=order_data['id'],
                        symbol=order_data['symbol'],
                        quantity=float(order_data['qty']),
                        side=OrderSide(order_data['side']),
                        order_type=OrderType(order_data['type']),
                        status=self._map_alpaca_status(order_data['status']),
                        filled_qty=float(order_data.get('filled_qty', 0)),
                        filled_price=float(order_data.get('filled_avg_price', 0)) if order_data.get('filled_avg_price') else 0,
                        created_at=datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00'))
                    )
                    orders.append(order)
                
                return orders
            else:
                logger.error(f"Failed to get orders: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for symbol"""
        try:
            # Use Alpaca's data API for quotes
            data_url = "https://data.alpaca.markets/v2/stocks"
            response = self.session.get(f"{data_url}/{symbol.upper()}/quotes/latest")
            
            if response.status_code == 200:
                quote_data = response.json()
                quote = quote_data.get('quote', {})
                
                return {
                    'symbol': symbol.upper(),
                    'bid': quote.get('bp'),
                    'ask': quote.get('ap'),
                    'bid_size': quote.get('bs'),
                    'ask_size': quote.get('as'),
                    'price': (quote.get('bp', 0) + quote.get('ap', 0)) / 2 if quote.get('bp') and quote.get('ap') else None,
                    'timestamp': quote.get('t')
                }
            else:
                logger.error(f"Failed to get quote for {symbol}: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return {}
    
    def _map_alpaca_status(self, alpaca_status: str) -> OrderStatus:
        """Map Alpaca status to our OrderStatus enum"""
        status_mapping = {
            'new': OrderStatus.PENDING,
            'accepted': OrderStatus.PENDING,
            'pending_new': OrderStatus.PENDING,
            'filled': OrderStatus.FILLED,
            'partially_filled': OrderStatus.PARTIAL_FILL,
            'canceled': OrderStatus.CANCELED,
            'expired': OrderStatus.CANCELED,
            'rejected': OrderStatus.REJECTED
        }
        return status_mapping.get(alpaca_status.lower(), OrderStatus.PENDING)
    
    def _map_to_alpaca_status(self, status: OrderStatus) -> Optional[str]:
        """Map our OrderStatus to Alpaca status"""
        status_mapping = {
            OrderStatus.PENDING: 'open',
            OrderStatus.FILLED: 'filled',
            OrderStatus.CANCELED: 'canceled',
            OrderStatus.REJECTED: 'rejected',
            OrderStatus.PARTIAL_FILL: 'open'
        }
        return status_mapping.get(status)
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'session'):
            self.session.close()