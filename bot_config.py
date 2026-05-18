import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Trading Bot Configuration"""
    
    # API Configuration
    BYBIT_API_KEY_DEMO = os.getenv('BYBIT_API_KEY_DEMO', '')
    BYBIT_API_SECRET_DEMO = os.getenv('BYBIT_API_SECRET_DEMO', '')
    BYBIT_API_KEY_REAL = os.getenv('BYBIT_API_KEY_REAL', '')
    BYBIT_API_SECRET_REAL = os.getenv('BYBIT_API_SECRET_REAL', '')
    
    # Trading Mode
    TRADING_MODE = os.getenv('TRADING_MODE', 'demo')  # 'demo' or 'real'
    
    # Currency Configuration
    BASE_CURRENCY = os.getenv('BASE_CURRENCY', 'PHP')
    FIAT_CURRENCY = os.getenv('FIAT_CURRENCY', 'USDT')
    
    # Trading Configuration
    BUY_AMOUNT_PHP = float(os.getenv('BUY_AMOUNT_PHP', '5000'))
    PROFIT_TARGET_PERCENT = float(os.getenv('PROFIT_TARGET_PERCENT', '7'))
    
    # Default Trading Pairs
    DEFAULT_PAIRS = [
        'BTCUSDT',
        'ETHUSDT',
        'SOLUSDT'
    ]
    
    # Chart Settings
    CANDLE_PERIOD = os.getenv('CANDLE_PERIOD', 'D')  # Daily candles
    LOOKBACK_DAYS = int(os.getenv('LOOKBACK_DAYS', '7'))
    
    # Bot Settings
    UPDATE_INTERVAL_SECONDS = int(os.getenv('UPDATE_INTERVAL_SECONDS', '300'))
    ENABLE_AUTO_TRADING = os.getenv('ENABLE_AUTO_TRADING', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'trading_bot.log'
    
    # API Endpoints
    BYBIT_TESTNET_URL = 'https://api-testnet.bybit.com'
    BYBIT_MAINNET_URL = 'https://api.bybit.com'
    
    @classmethod
    def get_api_credentials(cls):
        """Get appropriate API credentials based on trading mode"""
        if cls.TRADING_MODE == 'demo':
            return {
                'api_key': cls.BYBIT_API_KEY_DEMO,
                'api_secret': cls.BYBIT_API_SECRET_DEMO,
                'url': cls.BYBIT_TESTNET_URL,
                'is_testnet': True
            }
        else:
            return {
                'api_key': cls.BYBIT_API_KEY_REAL,
                'api_secret': cls.BYBIT_API_SECRET_REAL,
                'url': cls.BYBIT_MAINNET_URL,
                'is_testnet': False
            }
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is set"""
        creds = cls.get_api_credentials()
        if not creds['api_key'] or not creds['api_secret']:
            raise ValueError(f"API credentials not configured for {cls.TRADING_MODE} mode. Please set up .env file.")
        return True
