from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from enum import Enum

Base = declarative_base()

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

# SQLAlchemy Models
class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, index=True, nullable=False)
    company_name = Column(String(200))
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    price_data = relationship("PriceData", back_populates="stock")
    recommendations = relationship("Recommendation", back_populates="stock")
    signals = relationship("TradingSignal", back_populates="stock")
    positions = relationship("Position", back_populates="stock")

class PriceData(Base):
    __tablename__ = "price_data"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    price = Column(Float, nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Integer)
    change = Column(Float)
    change_percent = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    stock = relationship("Stock", back_populates="price_data")

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    source = Column(String(50), default="TipRanks")  # TipRanks, analyst, etc.
    smart_score = Column(Integer)  # 1-10 scale for TipRanks
    score_meaning = Column(String(50))  # Strong Buy, Buy, Hold, Sell, Strong Sell
    mean_price_target = Column(Float)
    median_price_target = Column(Float)
    high_price_target = Column(Float)
    low_price_target = Column(Float)
    num_analysts = Column(Integer)
    bullish_percent = Column(Float)
    bearish_percent = Column(Float)
    news_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    stock = relationship("Stock", back_populates="recommendations")

class TradingSignal(Base):
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float)  # 0.0 to 1.0
    reasoning = Column(Text)
    price_when_generated = Column(Float)
    target_price = Column(Float)
    stop_loss_price = Column(Float)
    position_size_usd = Column(Float)
    is_active = Column(Boolean, default=True)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)
    
    # Relationship
    stock = relationship("Stock", back_populates="signals")

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float)
    entry_date = Column(DateTime, default=datetime.utcnow)
    exit_date = Column(DateTime)
    exit_price = Column(Float)
    pnl = Column(Float, default=0.0)  # Profit/Loss
    pnl_percent = Column(Float, default=0.0)
    stop_loss_price = Column(Float)
    is_open = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relationship
    stock = relationship("Stock", back_populates="positions")

class TradingOrder(Base):
    __tablename__ = "trading_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("trading_signals.id"))
    order_type = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float)  # Target price
    executed_price = Column(Float)  # Actual execution price
    status = Column(String(20), default="PENDING")
    broker_order_id = Column(String(100))  # External broker order ID
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    error_message = Column(Text)

# Pydantic Models for API responses
class StockBase(BaseModel):
    ticker: str = Field(..., max_length=10, description="Stock ticker symbol")
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None

class StockCreate(StockBase):
    pass

class StockResponse(StockBase):
    id: int
    market_cap: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PriceDataBase(BaseModel):
    price: float = Field(..., gt=0, description="Current stock price")
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[int] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None

class PriceDataCreate(PriceDataBase):
    stock_id: int

class PriceDataResponse(PriceDataBase):
    id: int
    stock_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class RecommendationBase(BaseModel):
    source: str = "TipRanks"
    smart_score: Optional[int] = Field(None, ge=1, le=10)
    score_meaning: Optional[str] = None
    mean_price_target: Optional[float] = None
    median_price_target: Optional[float] = None
    high_price_target: Optional[float] = None
    low_price_target: Optional[float] = None
    num_analysts: Optional[int] = None
    bullish_percent: Optional[float] = None
    bearish_percent: Optional[float] = None
    news_score: Optional[float] = None

class RecommendationCreate(RecommendationBase):
    stock_id: int

class RecommendationResponse(RecommendationBase):
    id: int
    stock_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class TradingSignalBase(BaseModel):
    signal_type: SignalType
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    price_when_generated: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    position_size_usd: Optional[float] = None

class TradingSignalCreate(TradingSignalBase):
    stock_id: int

class TradingSignalResponse(TradingSignalBase):
    id: int
    stock_id: int
    is_active: bool
    generated_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PositionBase(BaseModel):
    quantity: float = Field(..., ne=0)
    entry_price: float = Field(..., gt=0)
    stop_loss_price: Optional[float] = None
    notes: Optional[str] = None

class PositionCreate(PositionBase):
    stock_id: int

class PositionResponse(PositionBase):
    id: int
    stock_id: int
    current_price: Optional[float] = None
    entry_date: datetime
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    is_open: bool = True
    
    class Config:
        from_attributes = True

class TradingOrderBase(BaseModel):
    order_type: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: float = Field(..., ne=0)
    price: Optional[float] = None

class TradingOrderCreate(TradingOrderBase):
    stock_id: int
    signal_id: Optional[int] = None

class TradingOrderResponse(TradingOrderBase):
    id: int
    stock_id: int
    signal_id: Optional[int] = None
    executed_price: Optional[float] = None
    status: OrderStatus
    broker_order_id: Optional[str] = None
    created_at: datetime
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

# Utility function to create database tables
def create_database(database_url: str):
    """Create database tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine

def get_session_factory(database_url: str):
    """Get SQLAlchemy session factory"""
    engine = create_database(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal