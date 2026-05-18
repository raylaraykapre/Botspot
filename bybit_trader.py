"""
Bybit Spot Trading Bot - Main Trading Engine
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from pybit.unified_trading import HTTP

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


class SpotTraderBase:
    """Base class for spot trading logic shared by live and demo traders."""

    def __init__(self, strategy: TradingStrategy, mode: str):
        self.strategy = strategy
        self.mode = mode
        self.open_positions: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        self.last_analysis_time: Dict[str, datetime] = {}

    def php_to_usdt(self, amount_php: float) -> float:
        return round(amount_php * Config.PHP_USD_RATE, 6)

    def usdt_to_php(self, amount_usdt: float) -> float:
        if Config.PHP_USD_RATE == 0:
            return 0.0
        return round(amount_usdt / Config.PHP_USD_RATE, 2)

    def get_top_gainers(self, limit: int = 3) -> List[str]:
        try:
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
            gainers = sorted(
                [d for d in data if d.get('price_change_percentage_24h')],
                key=lambda x: x['price_change_percentage_24h'],
                reverse=True
            )
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
        raise NotImplementedError

    def get_current_price(self, pair: str) -> Optional[float]:
        raise NotImplementedError

    def place_buy_order(self, pair: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str]:
        raise NotImplementedError

    def place_sell_order(self, pair: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str]:
        raise NotImplementedError

    def analyze_pair(self, pair: str) -> Dict:
        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing {pair}")
        logger.info(f"{'='*60}")
        candles = self.get_klines(pair, 'D', 7)
        if not candles:
            logger.warning(f"No candle data for {pair}")
            return {'pair': pair, 'action': 'skip', 'reason': 'No data'}
        current_price = self.get_current_price(pair)
        if not current_price:
            logger.warning(f"Could not get current price for {pair}")
            return {'pair': pair, 'action': 'skip', 'reason': 'No price'}
        analysis = self.strategy.analyze_candles(candles)
        analysis['pair'] = pair
        analysis['current_price'] = current_price
        logger.info(f"Analysis: {json.dumps(analysis, indent=2)}")
        if pair in self.open_positions:
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
            should_buy, reason = self.strategy.is_buy_signal(current_price, candles, pair)
            if should_buy and Config.ENABLE_AUTO_TRADING:
                buy_amount_usdt = self.php_to_usdt(Config.BUY_AMOUNT_PHP)
                quantity = self.strategy.calculate_buy_quantity(buy_amount_usdt, current_price)
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
        logger.info(f"\n{'#'*60}")
        logger.info(f"TRADING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Mode: {self.mode.upper()}")
        logger.info(f"{'#'*60}")
        results = []
        for pair in pairs:
            try:
                result = self.analyze_pair(pair)
                results.append(result)
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error analyzing {pair}: {e}")
                results.append({'pair': pair, 'action': 'error', 'reason': str(e)})
        logger.info(f"\nCycle Summary: {len(results)} pairs analyzed")
        self._log_summary(results)
        return results

    def _log_summary(self, results: List[Dict]):
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
        return {
            'open_positions': self.open_positions,
            'trade_history_count': len(self.trade_history),
            'last_trades': self.trade_history[-5:] if self.trade_history else []
        }

    def print_status(self):
        portfolio = self.get_portfolio_status()
        logger.info(f"\n{'='*60}")
        logger.info("PORTFOLIO STATUS")
        logger.info(f"{'='*60}")
        logger.info(f"Open Positions: {len(portfolio['open_positions'])}")
        for pair, position in portfolio['open_positions'].items():
            logger.info(f"  {pair}: {position['quantity']} @ {position['entry_price']}")
        if self.mode == 'demo' and hasattr(self, 'demo_account'):
            logger.info(f"Demo Balance: {self.demo_account['balance_php']} PHP / {self.demo_account['balance_usdt']} USDT")
        logger.info(f"Total Trades Executed: {portfolio['trade_history_count']}")
        if portfolio['last_trades']:
            logger.info("Last 5 Trades:")
            for trade in portfolio['last_trades']:
                profit = ((trade['exit_price'] - trade['entry_price']) / trade['entry_price']) * 100
                logger.info(f"  {trade['pair']}: Entry={trade['entry_price']}, Exit={trade['exit_price']}, Profit={profit:.2f}%")


class BybitSpotTrader(SpotTraderBase):
    """Live Bybit spot trading implementation."""

    def __init__(self):
        super().__init__(strategy=TradingStrategy(
            profit_target_percent=Config.PROFIT_TARGET_PERCENT,
            lookback_days=Config.LOOKBACK_DAYS
        ), mode='real')
        creds = Config.get_api_credentials()
        self.public_api_base = creds['url']
        try:
            self.client = HTTP(
                testnet=creds['is_testnet'],
                api_key=creds['api_key'],
                api_secret=creds['api_secret']
            )
            logger.info("Connected to Bybit real API")
        except Exception as e:
            logger.error(f"Failed to connect to Bybit API: {e}")
            raise

    def get_klines(self, pair: str, interval: str = 'D', limit: int = 7) -> List[Dict]:
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
            klines.reverse()
            candles = []
            for kline in klines:
                candles.append({
                    'time': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            return candles
        except Exception as e:
            logger.error(f"Exception fetching klines for {pair}: {e}")
            return []

    def get_current_price(self, pair: str) -> Optional[float]:
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
            if pair in self.open_positions:
                trade_record = {
                    'pair': pair,
                    'entry_price': self.open_positions[pair].get('entry_price'),
                    'exit_price': price or self.get_current_price(pair),
                    'quantity': quantity,
                    'time': datetime.now(),
                    'profit': 0
                }
                self.trade_history.append(trade_record)
                del self.open_positions[pair]
            return True, order_id
        except Exception as e:
            logger.error(f"Exception placing sell order for {pair}: {e}")
            return False, str(e)


class DemoSpotTrader(SpotTraderBase):
    """Local demo trading engine using Bybit chart data."""

    def __init__(self):
        super().__init__(strategy=TradingStrategy(
            profit_target_percent=Config.PROFIT_TARGET_PERCENT,
            lookback_days=Config.LOOKBACK_DAYS
        ), mode='demo')
        self.public_api_base = Config.BYBIT_MAINNET_URL
        self.demo_account = {
            'balance_php': Config.DEMO_STARTING_BALANCE_PHP,
            'balance_usdt': self.php_to_usdt(Config.DEMO_STARTING_BALANCE_PHP),
            'positions': {},
            'trade_history': []
        }
        self.open_positions = self.demo_account['positions']

    def get_klines(self, pair: str, interval: str = 'D', limit: int = 7) -> List[Dict]:
        return self._get_public_klines(pair, interval, limit)

    def _get_public_klines(self, pair: str, interval: str = 'D', limit: int = 7) -> List[Dict]:
        interval_map = {'D': '1D'}
        query_interval = interval_map.get(interval, interval)
        url = f"{self.public_api_base}/v5/market/kline"
        params = {
            'category': 'spot',
            'symbol': pair,
            'interval': query_interval,
            'limit': limit
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            data = response.json()
            if data.get('retCode', 0) != 0:
                logger.warning(f"Bybit public klines unavailable for {pair}: {data.get('retMsg')}")
                return self._get_coingecko_klines(pair, limit)
            klines = data['result']['list']
            klines.reverse()
            candles = []
            for kline in klines:
                candles.append({
                    'time': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            return candles
        except Exception as e:
            logger.warning(f"Demo public kline fetch failed for {pair}: {e}. Falling back to CoinGecko.")
            return self._get_coingecko_klines(pair, limit)

    def _get_coingecko_klines(self, pair: str, limit: int = 7) -> List[Dict]:
        symbol_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'SOLUSDT': 'solana'
        }
        if pair not in symbol_map:
            return []
        url = f"https://api.coingecko.com/api/v3/coins/{symbol_map[pair]}/market_chart"
        params = {'vs_currency': 'usd', 'days': limit, 'interval': 'daily'}
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            prices = data.get('prices', [])
            if not prices:
                return []
            candles = []
            for price_data in prices[-limit:]:
                timestamp = int(price_data[0] / 1000)
                price = float(price_data[1])
                candles.append({
                    'time': timestamp,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': 0.0
                })
            return candles
        except Exception as e:
            logger.error(f"CoinGecko fallback klines failed: {e}")
            return []

    def get_current_price(self, pair: str) -> Optional[float]:
        return self._get_public_price(pair)

    def _get_public_price(self, pair: str) -> Optional[float]:
        url = f"{self.public_api_base}/v5/market/tickers"
        params = {'category': 'spot', 'symbol': pair}
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            data = response.json()
            if data.get('retCode', 0) != 0:
                logger.warning(f"Bybit public price unavailable for {pair}: {data.get('retMsg')}")
                return self._get_coingecko_price(pair)
            ticker = data['result']['list'][0]
            return float(ticker['lastPrice'])
        except Exception as e:
            logger.warning(f"Demo public price fetch failed: {e}. Falling back to CoinGecko.")
            return self._get_coingecko_price(pair)

    def _get_coingecko_price(self, pair: str) -> Optional[float]:
        symbol_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'SOLUSDT': 'solana'
        }
        if pair not in symbol_map:
            return None
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': symbol_map[pair], 'vs_currencies': 'usd'}
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            return float(data[symbol_map[pair]]['usd'])
        except Exception as e:
            logger.error(f"CoinGecko price fetch failed for {pair}: {e}")
            return None

    def place_buy_order(self, pair: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str]:
        return self._simulate_buy_order(pair, quantity, price)

    def _simulate_buy_order(self, pair: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str]:
        entry_price = price or self.get_current_price(pair)
        if entry_price is None:
            return False, "No market price available"
        total_cost_usdt = quantity * entry_price
        if total_cost_usdt > self.demo_account['balance_usdt']:
            logger.warning(f"Demo buy failed: insufficient demo USDT balance for {pair}")
            return False, "Insufficient demo balance"
        self.demo_account['balance_usdt'] -= total_cost_usdt
        self.demo_account['balance_php'] = self.usdt_to_php(self.demo_account['balance_usdt'])
        order_id = f"DEMO-BUY-{pair}-{int(time.time())}"
        self.open_positions[pair] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'order_id': order_id,
            'time': datetime.now(),
            'cost_usdt': total_cost_usdt
        }
        logger.info(f"DEMO BUY for {pair}: qty={quantity} entry={entry_price} USDT cost={total_cost_usdt}")
        return True, order_id

    def place_sell_order(self, pair: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str]:
        return self._simulate_sell_order(pair, quantity, price)

    def _simulate_sell_order(self, pair: str, quantity: float, price: Optional[float] = None) -> Tuple[bool, str]:
        if pair not in self.open_positions:
            return False, "No open demo position"
        position = self.open_positions[pair]
        if quantity != position['quantity']:
            return False, "Partial sells are not supported in demo mode"
        exit_price = price or self.get_current_price(pair)
        if exit_price is None:
            return False, "No market price available"
        proceeds_usdt = quantity * exit_price
        self.demo_account['balance_usdt'] += proceeds_usdt
        self.demo_account['balance_php'] = self.usdt_to_php(self.demo_account['balance_usdt'])
        entry_price = position['entry_price']
        profit_usdt = proceeds_usdt - position.get('cost_usdt', quantity * entry_price)
        profit_php = self.usdt_to_php(profit_usdt)
        order_id = f"DEMO-SELL-{pair}-{int(time.time())}"
        trade_record = {
            'pair': pair,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'time': datetime.now(),
            'profit_usdt': profit_usdt,
            'profit_php': profit_php,
        }
        self.trade_history.append(trade_record)
        self.demo_account['trade_history'].append(trade_record)
        del self.open_positions[pair]
        logger.info(f"DEMO SELL for {pair}: qty={quantity} exit={exit_price} USDT proceeds={proceeds_usdt} profit_usdt={profit_usdt}")
        return True, order_id
