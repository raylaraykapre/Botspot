"""
Trading Strategy: Buy Low, Sell High with 7-Day Chart Analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class TradingStrategy:
    """Implements buy low, sell high strategy using 7-day chart analysis"""
    
    def __init__(self, profit_target_percent: float = 7.0, lookback_days: int = 7):
        """
        Initialize strategy parameters
        
        Args:
            profit_target_percent: Minimum profit required for selling (default: 7%)
            lookback_days: Number of days to look back for support/resistance (default: 7)
        """
        self.profit_target_percent = profit_target_percent
        self.lookback_days = lookback_days
        self.active_positions = {}  # Track open positions
        
    def find_support_resistance(self, candles: List[Dict]) -> Tuple[float, float]:
        """
        Find support and resistance levels from candle data
        
        Args:
            candles: List of candle dictionaries with 'high', 'low', 'close' prices
            
        Returns:
            Tuple of (support_level, resistance_level)
        """
        if not candles or len(candles) < 2:
            return None, None
        
        lows = [float(c['low']) for c in candles]
        highs = [float(c['high']) for c in candles]
        closes = [float(c['close']) for c in candles]
        
        support = min(lows)
        resistance = max(highs)
        return support, resistance
    
    def calculate_average_price(self, candles: List[Dict]) -> float:
        """Calculate average price from candle data"""
        if not candles:
            return 0
        
        closes = [float(c['close']) for c in candles]
        return sum(closes) / len(closes)
    
    def is_buy_signal(self, current_price: float, candles: List[Dict], 
                      pair: str) -> Tuple[bool, str]:
        """
        Determine if current price is a good buying opportunity
        
        Criteria:
        - Price is near or at support level (lowest price in lookback period)
        - Price is lower than average
        
        Args:
            current_price: Current market price
            candles: Historical candle data
            pair: Trading pair name
            
        Returns:
            Tuple of (should_buy: bool, reason: str)
        """
        if not candles or len(candles) < 3:
            return False, "Insufficient candle data"
        
        lows = [float(c['low']) for c in candles]
        closes = [float(c['close']) for c in candles]
        
        support_level = min(lows)
        avg_price = sum(closes) / len(closes)
        
        # Buy if price is within 2% of support level (near lowest point)
        support_range = support_level * 1.02
        
        if current_price <= support_range and current_price < avg_price:
            reason = f"Price {current_price} near support {support_level:.2f}"
            return True, reason
        
        return False, f"No buy signal. Current: {current_price}, Support: {support_level}, Avg: {avg_price}"
    
    def is_sell_signal(self, pair: str, entry_price: float, current_price: float,
                      candles: List[Dict]) -> Tuple[bool, str]:
        """
        Determine if current price is a good selling opportunity
        
        Criteria:
        - Minimum 7% profit achieved
        - Price is near or at resistance level (highest price in lookback period)
        
        Args:
            pair: Trading pair name
            entry_price: Price at which we bought
            current_price: Current market price
            candles: Historical candle data
            
        Returns:
            Tuple of (should_sell: bool, reason: str)
        """
        if not candles:
            return False, "Insufficient candle data"
        
        # Calculate profit percentage
        profit_percent = ((current_price - entry_price) / entry_price) * 100
        
        # Find resistance level
        highs = [float(c['high']) for c in candles]
        resistance_level = max(highs)
        
        # Sell if we hit or exceed profit target AND near resistance
        resistance_range = resistance_level * 0.98  # Within 2% of resistance
        
        if profit_percent >= self.profit_target_percent:
            if current_price >= resistance_range:
                reason = f"Profit {profit_percent:.2f}% >= Target {self.profit_target_percent}%"
                return True, reason
            return True, f"Profit target hit: {profit_percent:.2f}% gain"
        
        return False, f"Profit: {profit_percent:.2f}% < Target {self.profit_target_percent}%"
    
    def calculate_buy_quantity(self, buy_amount_usd: float, current_price: float) -> float:
        """
        Calculate quantity to buy based on USD amount
        
        Args:
            buy_amount_usd: Amount in USD to spend
            current_price: Current price of asset
            
        Returns:
            Quantity to buy (rounded to appropriate precision)
        """
        quantity = buy_amount_usd / current_price
        # Round to 4 decimal places for most crypto
        return round(quantity, 4)
    
    def get_take_profit_price(self, entry_price: float) -> float:
        """
        Calculate take profit price based on profit target
        
        Args:
            entry_price: Price at which we bought
            
        Returns:
            Take profit price
        """
        return entry_price * (1 + self.profit_target_percent / 100)
    
    def get_stop_loss_price(self, entry_price: float, stop_loss_percent: float = 5.0) -> float:
        """
        Calculate stop loss price
        
        Args:
            entry_price: Price at which we bought
            stop_loss_percent: Stop loss percentage (default: 5%)
            
        Returns:
            Stop loss price
        """
        return entry_price * (1 - stop_loss_percent / 100)
    
    def analyze_candles(self, candles: List[Dict]) -> Dict:
        """
        Comprehensive candle analysis
        
        Args:
            candles: List of candle data
            
        Returns:
            Dictionary with analysis results
        """
        if not candles or len(candles) < 2:
            return {}
        
        closes = [float(c['close']) for c in candles]
        opens = [float(c['open']) for c in candles]
        highs = [float(c['high']) for c in candles]
        lows = [float(c['low']) for c in candles]
        
        analysis = {
            'support': min(lows),
            'resistance': max(highs),
            'current_price': closes[-1],
            'average_price': sum(closes) / len(closes),
            'highest_price': max(highs),
            'lowest_price': min(lows),
            'price_range': max(highs) - min(lows),
            'volatility': (max(highs) - min(lows)) / (sum(closes) / len(closes)),
            'uptrend': closes[-1] > sum(closes[:-1]) / len(closes[:-1]) if len(closes) > 1 else False,
        }
        
        return analysis
