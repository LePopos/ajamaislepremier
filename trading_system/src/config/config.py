import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    # API Keys
    alpha_vantage_api_key: str = ""
    tipranks_proxy_url: Optional[str] = None
    
    # Trading parameters
    max_position_size: float = 1000.0  # Maximum position size in USD
    stop_loss_percentage: float = -5.0  # Stop loss at -5%
    min_smart_score: int = 8  # Minimum TipRanks Smart Score for buy signal
    max_smart_score: int = 3  # Maximum Smart Score for sell signal
    
    # Risk management
    max_daily_trades: int = 10
    max_portfolio_risk: float = 0.02  # 2% max portfolio risk per trade
    
    # Data collection
    collection_interval_minutes: int = 15  # Collect data every 15 minutes
    # Expert analyst watchlists
    cj_muse_stocks: List[str] = ["NVDA", "MU", "INTC", "GLW", "AZTA"]  # C.J. Muse picks
    richard_shannon_stocks: List[str] = ["TSM", "LITE", "COHR", "VICR", "QBTS"]  # Richard Shannon picks
    watchlist: List[str] = ["NVDA", "MU", "INTC", "GLW", "AZTA", "TSM", "LITE", "COHR", "VICR", "QBTS"]  # Combined expert picks
    
    # Database
    database_url: str = "sqlite:///./trading_data.db"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/trading_system.log"
    
    # Email Notifications
    email_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: Optional[str] = None
    sender_password: Optional[str] = None  # Use app-specific password for Gmail
    recipient_emails: List[str] = []
    
    # Webhooks (Slack, Discord, etc.)
    webhook_url: Optional[str] = None
    
    # Notification settings
    send_signal_alerts: bool = True
    send_daily_summary: bool = True
    daily_summary_hour: int = 18  # 6 PM
    
    # Broker Configuration (Alpaca)
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    paper_trading: bool = True
    dry_run: bool = True  # Safety: no real trades by default
    auto_execute_confidence: float = 0.8  # Min confidence for auto-execution
    
    class Config:
        env_file = ".env"
        case_sensitive = False

config = Config()