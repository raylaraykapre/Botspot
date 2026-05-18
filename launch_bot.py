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
import schedule

from bot_config import Config
from bybit_trader import BybitSpotTrader

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
            logger.info("="*70)
            logger.info("BYBIT SPOT TRADING BOT - INITIALIZATION")
            logger.info("="*70)
            
            # Validate configuration
            Config.validate_config()
            logger.info(f"✓ Configuration validated")
            logger.info(f"✓ Trading Mode: {Config.TRADING_MODE.upper()}")
            logger.info(f"✓ Profit Target: {Config.PROFIT_TARGET_PERCENT}%")
            logger.info(f"✓ Update Interval: {Config.UPDATE_INTERVAL_SECONDS}s")
            
            # Initialize trader
            self.trader = BybitSpotTrader(mode=Config.TRADING_MODE)
            logger.info(f"✓ Bybit API connection established")
            
            # Build trading pairs list
            self._build_trading_pairs()
            
            logger.info(f"✓ Trading pairs configured: {', '.join(self.trading_pairs)}")
            logger.info("✓ Bot initialized successfully!\n")
            
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
    
    def schedule_tasks(self):
        """Schedule recurring tasks"""
        # Run trading cycle at regular intervals
        schedule.every(Config.UPDATE_INTERVAL_SECONDS).seconds.do(self.run_cycle)
        
        # Print status every hour
        schedule.every(1).hour.do(self.trader.print_status)
        
        logger.info(f"Scheduled trading cycle every {Config.UPDATE_INTERVAL_SECONDS}s")
    
    def start(self):
        """Start the trading bot"""
        if not self.initialize():
            return False
        
        self.running = True
        self.schedule_tasks()
        
        logger.info("="*70)
        logger.info("BOT STARTED - Auto-trading enabled")
        logger.info("="*70)
        logger.info(f"Start time: {datetime.now()}")
        logger.info(f"Auto-trading: {'ENABLED' if Config.ENABLE_AUTO_TRADING else 'DISABLED (Demo mode)'}")
        logger.info(f"Trading pairs: {', '.join(self.trading_pairs)}")
        logger.info("\nPress Ctrl+C to stop the bot gracefully")
        logger.info("="*70 + "\n")
        
        # Main loop
        try:
            # Run initial cycle
            self.run_cycle()
            
            # Run scheduled tasks
            while self.running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nKeyboard interrupt received")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the trading bot"""
        logger.info("\n" + "="*70)
        logger.info("BOT SHUTDOWN")
        logger.info("="*70)
        
        if self.trader:
            self.trader.print_status()
        
        logger.info("="*70)
        logger.info("Bot stopped successfully")
        logger.info(f"End time: {datetime.now()}")
        logger.info("="*70)


def main():
    """Main entry point"""
    launcher = TradingBotLauncher()
    launcher.start()


if __name__ == '__main__':
    main()
