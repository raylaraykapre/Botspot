"""
Bybit Spot Trading Bot - Main Trading Engine
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pybit.unified_trading import HTTP
import requests

from bot_config import Config
from strategy import TradingStrategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BybitSpotTrader:
    """Main trading bot for Bybit spot market"""
    
    def __init__(self, mode: str = 'demo'):
        """
        Initialize Bybit trader
        
        Args:
            mode: 'demo' for testnet or 'real' for mainnet
        """
        self.mode = mode
        self.config = Config
        self.strategy = TradingStrategy(
            profit_target_percent=Config.PROFIT_TARGET_PERCENT,
            lookback_days=Config.LOOKBACK_DAYS
        )
        
        # Get API credentials
        creds = Config.get_api_credentials()
        
        try:
            self.client = HTTP(
                testnet=creds['is_testnet'],
                api_key=creds['api_key'],
                api_secret=creds['api_secret']
            )
            logger.info(f"Connected to Bybit {mode} API")
        except Exception as e:
            logger.error(f"Failed to connect to Bybit API: {e}")
            raise
        
        # Trading state
        self.open_positions = {}  # {pair: {'entry_price': x, 'quantity': y}}
        self.trade_history = []
        self.last_analysis_time = {}
        
    def get_top_gainers(self, limit: int = 3) -> List[str]:
        """
        Get top 3 gainers from the market
        Uses CoinGecko API as free alternative
        
        Args:
            limit: Number of top gainers to return
            
        Returns:
            List of trading pairs (e.g., ['BTCUSDT', 'ETHUSDT'])
        """
        try:
            # Using CoinGecko API for price data
            # Map common gainers to Bybit pairs
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_rank',
                'per_page': 100,
                'sparkline': False,
                'price_change_percentage': '24h'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            # Filter and sort by 24h price change
            gainers = sorted(
                [d for d in data if d.get('price_change_percentage_24h')],
                key=lambda x: x['price_change_percentage_24h'],
                reverse=True
            )
            
            # Map to Bybit symbols
            symbol_map = {
                'bitcoin': 'BTCUSDT',
                'ethereum': 'ETHUSDT',
                'solana': 'SOLUSDT',
                'ripple': 'XRPUSDT',
                'cardano': 'ADAUSDT',
                'polkadot': 'DOTUSDT',
                'dogecoin': 'DOGEUSDT',
                'litecoin': 'LTCUSDT',
            }
            
            top_gainers = []
            for gainer in gainers:
                symbol = gainer['id'].lower()
                if symbol in symbol_map:
                    pair = symbol_map[symbol]
                    if pair not in top_gainers:
                        top_gainers.append(pair)
                    if len(top_gainers) >= limit:
                        break
            
            logger.info(f"Top gainers: {top_gainers}")
            return top_gainers
            
        except Exception as e:
            logger.warning(f"Failed to fetch top gainers: {e}. Using defaults.")
            return ['ADAUSDT', 'XRPUSDT', 'DOTUSDT']
    
    def get_klines(self, pair: str, interval: str = 'D', limit: int = 7) -> List[Dict]:
        """
        Get candlestick data from Bybit
        
        Args:
            pair: Trading pair (e.g., 'BTCUSDT')
            interval: Candle interval (D for daily)
            limit: Number of candles to fetch
            
        Returns:
            List of candle dictionaries
        """
        try:
            response = self.client.get_kline(
                category="spot",
                symbol=pair,
                interval=interval,
                limit=limit
            )
            
            if response['retCode'] != 0:
                logger.error(f"Error fetching klines for {pair}: {response['retMsg']}")
                return []
            
            klines = response['result']['list']
            # Reverse to get chronological order (oldest first)
            klines.reverse()
            
            # Convert to standard format
            candles = []
            for kline in klines:
                candle = {
                    'time': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                }
                candles.append(candle)
            
            return candles
            
        except Exception as e:
            logger.error(f"Exception fetching klines for {pair}: {e}")
            return []
    
    def get_current_price(self, pair: str) -> Optional[float]:
        """
        Get current price of a trading pair
        
        Args:
            pair: Trading pair (e.g., 'BTCUSDT')
            
        Returns:
            Current price or None if error
        """
        try:
            response = self.client.get_tickers(
                category="spot",
                symbol=pair
            )
            
            if response['retCode'] != 0:
                logger.error(f"Error fetching price for {pair}")
                return None
            
            ticker = response['result']['list'][0]
            return float(ticker['lastPrice'])
            
        except Exception as e:
            logger.error(f"Exception fetching current price for {pair}: {e}")
            return None
    
    def place_buy_order(self, pair: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str]:
        """
        Place a buy order on Bybit
        
        Args:
            pair: Trading pair
            quantity: Quantity to buy
            price: Optional limit price (None for market order)
            
        Returns:
            Tuple of (success: bool, order_id_or_error: str)
        """
        try:
            order_type = "Market" if price is None else "Limit"
            
            params = {
                'category': 'spot',
                'symbol': pair,
                'side': 'Buy',
                'orderType': order_type,
                'qty': str(quantity),
            }
            
            if price:
                params['price'] = str(price)
            
            response = self.client.place_order(**params)
            
            if response['retCode'] != 0:
                error_msg = response['retMsg']
                logger.error(f"Buy order failed for {pair}: {error_msg}")
                return False, error_msg
            
            order_id = response['result']['orderId']
            logger.info(f"BUY order placed for {pair}: {quantity} @ {order_type} - Order ID: {order_id}")
            
            # Track position
            self.open_positions[pair] = {
                'entry_price': price or self.get_current_price(pair),
                'quantity': quantity,
                'order_id': order_id,
                'time': datetime.now()
            }
            
            return True, order_id
            
        except Exception as e:
            logger.error(f"Exception placing buy order for {pair}: {e}")
            return False, str(e)
    
    def place_sell_order(self, pair: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str]:
        """
        Place a sell order on Bybit
        
        Args:
            pair: Trading pair
            quantity: Quantity to sell
            price: Optional limit price (None for market order)
            
        Returns:
            Tuple of (success: bool, order_id_or_error: str)
        """
        try:
            order_type = "Market" if price is None else "Limit"
            
            params = {
                'category': 'spot',
                'symbol': pair,
                'side': 'Sell',
                'orderType': order_type,
                'qty': str(quantity),
            }
            
            if price:
                params['price'] = str(price)
            
            response = self.client.place_order(**params)
            
            if response['retCode'] != 0:
                error_msg = response['retMsg']
                logger.error(f"Sell order failed for {pair}: {error_msg}")
                return False, error_msg
            
            order_id = response['result']['orderId']
            logger.info(f"SELL order placed for {pair}: {quantity} @ {order_type} - Order ID: {order_id}")
            
            # Record trade
            if pair in self.open_positions:
                trade_record = {
                    'pair': pair,
                    'entry_price': self.open_positions[pair].get('entry_price'),
                    'exit_price': price or self.get_current_price(pair),
                    'quantity': quantity,
                    'time': datetime.now(),
                    'profit': 0  # Will be calculated later
                }
                self.trade_history.append(trade_record)
                del self.open_positions[pair]
            
            return True, order_id
            
        except Exception as e:
            logger.error(f"Exception placing sell order for {pair}: {e}")
            return False, str(e)
    
    def analyze_pair(self, pair: str) -> Dict:
        """
        Analyze a trading pair and determine action
        
        Args:
            pair: Trading pair to analyze
            
        Returns:
            Dictionary with analysis results and recommended action
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing {pair}")
        logger.info(f"{'='*60}")
        
        # Get historical data
        candles = self.get_klines(pair, 'D', 7)
        if not candles:
            logger.warning(f"No candle data for {pair}")
            return {'pair': pair, 'action': 'skip', 'reason': 'No data'}
        
        # Get current price
        current_price = self.get_current_price(pair)
        if not current_price:
            logger.warning(f"Could not get current price for {pair}")
            return {'pair': pair, 'action': 'skip', 'reason': 'No price'}
        
        # Analyze using strategy
        analysis = self.strategy.analyze_candles(candles)
        analysis['pair'] = pair
        analysis['current_price'] = current_price
        
        logger.info(f"Analysis: {json.dumps(analysis, indent=2)}")
        
        # Check if we have open position
        if pair in self.open_positions:
            # Check sell signal
            entry_price = self.open_positions[pair]['entry_price']
            should_sell, reason = self.strategy.is_sell_signal(pair, entry_price, current_price, candles)
            
            if should_sell and Config.ENABLE_AUTO_TRADING:
                quantity = self.open_positions[pair]['quantity']
                success, result = self.place_sell_order(pair, quantity)
                analysis['action'] = 'sell'
                analysis['result'] = result
                analysis['success'] = success
            else:
                analysis['action'] = 'hold'
                analysis['reason'] = reason
        else:
            # Check buy signal
            should_buy, reason = self.strategy.is_buy_signal(current_price, candles, pair)
            
            if should_buy and Config.ENABLE_AUTO_TRADING:
                # Calculate buy quantity based on budget
                quantity = self.strategy.calculate_buy_quantity(Config.BUY_AMOUNT_PHP, current_price)
                success, result = self.place_buy_order(pair, quantity)
                analysis['action'] = 'buy'
                analysis['quantity'] = quantity
                analysis['result'] = result
                analysis['success'] = success
            else:
                analysis['action'] = 'wait'
                analysis['reason'] = reason
        
        return analysis
    
    def run_trading_cycle(self, pairs: List[str]) -> List[Dict]:
        """
        Run one complete trading cycle for all pairs
        
        Args:
            pairs: List of trading pairs to analyze
            
        Returns:
            List of analysis results
        """
        logger.info(f"\n{'#'*60}")
        logger.info(f"TRADING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Mode: {self.mode.upper()}")
        logger.info(f"{'#'*60}")
        
        results = []
        for pair in pairs:
            try:
                result = self.analyze_pair(pair)
                results.append(result)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Error analyzing {pair}: {e}")
                results.append({'pair': pair, 'action': 'error', 'reason': str(e)})
        
        logger.info(f"\nCycle Summary: {len(results)} pairs analyzed")
        self._log_summary(results)
        
        return results
    
    def _log_summary(self, results: List[Dict]):
        """Log summary of trading cycle"""
        buy_signals = [r for r in results if r.get('action') == 'buy']
        sell_signals = [r for r in results if r.get('action') == 'sell']
        holds = [r for r in results if r.get('action') == 'hold']
        waits = [r for r in results if r.get('action') == 'wait']
        
        logger.info(f"BUY signals: {len(buy_signals)}")
        for b in buy_signals:
            logger.info(f"  - {b['pair']}: qty={b.get('quantity', 'N/A')}")
        
        logger.info(f"SELL signals: {len(sell_signals)}")
        for s in sell_signals:
            logger.info(f"  - {s['pair']}")
        
        logger.info(f"HOLD positions: {len(holds)}")
        for h in holds:
            logger.info(f"  - {h['pair']}")
        
        logger.info(f"WAIT (no signal): {len(waits)}")
    
    def get_portfolio_status(self) -> Dict:
        """
        Get current portfolio status
        
        Returns:
            Dictionary with portfolio information
        """
        return {
            'open_positions': self.open_positions,
            'trade_history_count': len(self.trade_history),
            'last_trades': self.trade_history[-5:] if self.trade_history else []
        }
    
    def print_status(self):
        """Print current trading status"""
        portfolio = self.get_portfolio_status()
        
        logger.info(f"\n{'='*60}")
        logger.info("PORTFOLIO STATUS")
        logger.info(f"{'='*60}")
        logger.info(f"Open Positions: {len(portfolio['open_positions'])}")
        
        for pair, position in portfolio['open_positions'].items():
            logger.info(f"  {pair}: {position['quantity']} @ {position['entry_price']}")
        
        logger.info(f"Total Trades Executed: {portfolio['trade_history_count']}")
        
        if portfolio['last_trades']:
            logger.info("Last 5 Trades:")
            for trade in portfolio['last_trades']:
                profit = ((trade['exit_price'] - trade['entry_price']) / trade['entry_price']) * 100
                logger.info(f"  {trade['pair']}: Entry={trade['entry_price']}, Exit={trade['exit_price']}, Profit={profit:.2f}%")
