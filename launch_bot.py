#!/usr/bin/env python3
"""
Bybit Spot Trading Bot - Launcher Script
Automated trading with buy low/sell high strategy
"""

import sys
import time
import logging
import signal
from datetime import datetime

from bot_config import Config
from bybit_trader import BybitSpotTrader, DemoSpotTrader

# Setup logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingBotLauncher:
    """Manages the trading bot lifecycle"""
    
    def __init__(self):
        """Initialize the bot launcher"""
        self.trader = None
        self.running = False
        self.trading_pairs = []
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("\n\nShutdown signal received. Stopping bot...")
        self.running = False
        self.shutdown()
        sys.exit(0)
    
    def initialize(self):
        """Initialize the trading bot"""
        try:
            logger.info("Initializing trading bot")
            Config.validate_config()
            logger.info(f"Config validated | mode={Config.TRADING_MODE.upper()} | interval={Config.UPDATE_INTERVAL_SECONDS}s")
            
            if Config.TRADING_MODE.lower() == 'demo':
                self.trader = DemoSpotTrader()
                logger.info(f"Demo trader initialized | balance={Config.DEMO_STARTING_BALANCE_PHP} PHP")
            else:
                self.trader = BybitSpotTrader()
                logger.info("Bybit API trader initialized")
            
            self._build_trading_pairs()
            logger.info(f"Trading pairs: {', '.join(self.trading_pairs)}")
            logger.info("Bot initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Initialization failed: {e}")
            logger.error("\nPlease check:")
            logger.error("1. .env file is configured with API credentials")
            logger.error("2. Bybit API keys are valid")
            logger.error("3. Network connectivity is available")
            return False
    
    def _build_trading_pairs(self):
        """Build complete list of trading pairs"""
        # Default pairs
        pairs = Config.DEFAULT_PAIRS.copy()
        
        # Add top 3 gainers
        try:
            logger.info("Fetching top gainers...")
            gainers = self.trader.get_top_gainers(limit=3)
            for pair in gainers:
                if pair not in pairs:
                    pairs.append(pair)
        except Exception as e:
            logger.warning(f"Could not fetch gainers: {e}")
        
        self.trading_pairs = pairs[:6]  # Limit to reasonable number
    
    def run_cycle(self):
        """Run a single trading cycle"""
        try:
            if not self.trader:
                logger.error("Trader not initialized")
                return
            
            # Analyze all pairs
            results = self.trader.run_trading_cycle(self.trading_pairs)
            
            # Print status
            self.trader.print_status()
            
        except Exception as e:
            logger.error(f"Error during trading cycle: {e}", exc_info=True)
    
    def start(self):
        """Start the trading bot"""
        if not self.initialize():
            return False
        
        self.running = True
        logger.info(f"Bot started | mode={Config.TRADING_MODE} | auto-trading={'ENABLED' if Config.ENABLE_AUTO_TRADING else 'DISABLED'}")
        logger.info(f"Start time: {datetime.now()}")
        
        try:
            # Run initial cycle
            self.run_cycle()
            
            while self.running:
                time.sleep(Config.UPDATE_INTERVAL_SECONDS)
                self.run_cycle()
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the trading bot"""
        if self.trader:
            self.trader.print_status()
        logger.info(f"Bot stopped successfully | end={datetime.now()}")


def main():
    """Main entry point"""
    launcher = TradingBotLauncher()
    launcher.start()


if __name__ == '__main__':
    main()
