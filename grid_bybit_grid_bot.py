#!/usr/bin/env python3
"""Standalone Bybit Grid Trading Bot with DEMO and LIVE modes.

This script uses ccxt to fetch real market data from Bybit.
DEMO mode simulates trades locally without API keys.
LIVE mode places real orders on Bybit spot using provided API credentials.
"""

import ccxt
import sys
import time
import traceback
from datetime import datetime

# === CONFIGURATION ===
TRADING_MODE = "DEMO"  # Set to "DEMO" for simulation or "LIVE" for real trading
SYMBOL = "BTC/USDT"  # Bybit spot symbol to trade
USD_TO_PHP = 56.50  # Exchange rate used to convert USD/USDT prices into PHP
ALLOCATION_PERCENT = 10.0  # Wallet percentage allocated per grid order
LOWER_PRICE = 26000.0  # Grid lower bound in USD
UPPER_PRICE = 32000.0  # Grid upper bound in USD
GRID_COUNT = 12  # Number of grid segments between lower and upper price
POLL_INTERVAL = 7  # Seconds between market checks
DEMO_START_CASH_PHP = 1_000_000.0  # Virtual PHP cash available in DEMO mode
DEMO_START_BASE = 0.0  # Virtual BTC balance in DEMO mode
LIVE_API_KEY = ""  # Fill live API key for LIVE mode
LIVE_API_SECRET = ""  # Fill live API secret for LIVE mode
# =====================


def format_php(value):
    return f"₱{value:,.2f}"


def format_usd(value):
    return f"${value:,.2f}"


def log(message):
    print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] {message}")


def build_grid(lower, upper, count):
    step = (upper - lower) / count
    return [round(lower + i * step, 2) for i in range(count + 1)]


class GridTradingBot:
    def __init__(self):
        self.symbol = SYMBOL
        self.trading_mode = TRADING_MODE.upper().strip()
        self.usd_to_php = USD_TO_PHP
        self.allocation_percent = max(1.0, min(ALLOCATION_PERCENT, 50.0))
        self.grid_lines = build_grid(LOWER_PRICE, UPPER_PRICE, GRID_COUNT)
        self.last_price = None
        self.position_map = {price: False for price in self.grid_lines}
        self.exchange = None

        # DEMO mode wallet state
        self.demo_cash_php = DEMO_START_CASH_PHP
        self.demo_base = DEMO_START_BASE

        self._initialize_exchange()
        self._print_startup_summary()

    def _initialize_exchange(self):
        self.exchange = ccxt.bybit({
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })

        if self.trading_mode == "LIVE":
            if not LIVE_API_KEY or not LIVE_API_SECRET:
                log("ERROR: LIVE mode selected but LIVE_API_KEY or LIVE_API_SECRET is missing.")
                sys.exit(1)
            self.exchange.apiKey = LIVE_API_KEY
            self.exchange.secret = LIVE_API_SECRET
            self._confirm_live_mode()

        try:
            self.exchange.load_markets()
        except Exception as ex:
            log(f"Unable to load markets: {ex}")
            sys.exit(1)

    def _confirm_live_mode(self):
        print("\nWARNING: Live trading is active. Real funds may be used.")
        print("Type 'CONFIRM' to continue or anything else to exit.")
        choice = input("> ").strip()
        if choice != "CONFIRM":
            log("Live trading cancelled by user.")
            sys.exit(0)
        log("Live trading confirmed. Starting bot...")

    def _print_startup_summary(self):
        mode_text = "DEMO" if self.trading_mode == "DEMO" else "LIVE"
        log(f"Starting Bybit grid trading bot in {mode_text} mode")
        log(f"Symbol: {self.symbol}")
        log(f"Grid: {len(self.grid_lines)} levels from {format_usd(self.grid_lines[0])} to {format_usd(self.grid_lines[-1])}")
        log(f"Allocation per order: {self.allocation_percent:.1f}% of wallet")
        log(f"PHP conversion rate: {self.usd_to_php:.2f} PHP per USD")
        if self.trading_mode == "DEMO":
            total_value = self.demo_cash_php + (self.demo_base * self.grid_lines[0] * self.usd_to_php)
            log(f"DEMO wallet starting value: {format_php(total_value)}")
        log("---")

    def fetch_price(self):
        ticker = self.exchange.fetch_ticker(self.symbol)
        return float(ticker["last"])

    def get_live_wallet_value_php(self, price):
        balance = self.exchange.fetch_balance({"type": "spot"})
        base_currency = self.symbol.split("/")[0]
        quote_currency = self.symbol.split("/")[1]
        base_free = float(balance.get(base_currency, {}).get("free", 0.0))
        quote_free = float(balance.get(quote_currency, {}).get("free", 0.0))
        total_usd_value = quote_free + (base_free * price)
        return total_usd_value * self.usd_to_php, base_free, quote_free

    def run(self):
        try:
            while True:
                try:
                    current_price = self.fetch_price()
                    self.process_tick(current_price)
                except (ccxt.NetworkError, ccxt.RequestTimeout, ccxt.RateLimitExceeded) as network_error:
                    log(f"Network error: {network_error}. Retrying after {POLL_INTERVAL}s.")
                except ccxt.ExchangeError as exchange_error:
                    log(f"Exchange error: {exchange_error}. Sleeping and retrying.")
                except Exception as unexpected:
                    log(f"Unexpected error: {unexpected}")
                    traceback.print_exc()
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            log("Bot stopped by user.")

    def process_tick(self, current_price):
        price_php = current_price * self.usd_to_php
        if self.last_price is None:
            self.last_price = current_price
            self._print_market_snapshot(current_price, price_php)
            return

        self._print_market_snapshot(current_price, price_php)

        for level in self.grid_lines:
            if self.last_price > level >= current_price:
                self._execute_buy(level, current_price)
            elif self.last_price < level <= current_price:
                self._execute_sell(level, current_price)

        self.last_price = current_price

    def _print_market_snapshot(self, price, price_php):
        if self.trading_mode == "DEMO":
            total_php = self.demo_cash_php + (self.demo_base * price_php)
            log(f"Price: {format_usd(price)} / {format_php(price_php)} | Demo wallet: {format_php(total_php)} | Cash: {format_php(self.demo_cash_php)} | BTC: {self.demo_base:.8f}")
        else:
            wallet_php, base_free, quote_free = self.get_live_wallet_value_php(price)
            log(f"Price: {format_usd(price)} / {format_php(price_php)} | Live wallet value: {format_php(wallet_php)} | {self.symbol.split('/')[0]}: {base_free:.8f} | USDT: {quote_free:.4f}")

    def _execute_buy(self, level, current_price):
        if self.position_map[level]:
            return
        log(f"Grid buy triggered at {format_usd(level)}")
        if self.trading_mode == "DEMO":
            self._demo_buy(level, current_price)
        else:
            self._live_buy(level, current_price)
        self.position_map[level] = True

    def _execute_sell(self, level, current_price):
        if not self.position_map[level]:
            return
        log(f"Grid sell triggered at {format_usd(level)}")
        if self.trading_mode == "DEMO":
            self._demo_sell(level, current_price)
        else:
            self._live_sell(level, current_price)
        self.position_map[level] = False

    # --- DEMO MODE LOGIC ---
    def _demo_buy(self, level, current_price):
        if self.demo_cash_php <= 0:
            log("DEMO buy skipped: no PHP cash available.")
            return

        allocation_php = self.demo_cash_php * (self.allocation_percent / 100)
        price_php = current_price * self.usd_to_php
        quantity = allocation_php / price_php
        if quantity <= 0:
            log("DEMO buy skipped: allocation too small.")
            return

        self.demo_base += quantity
        self.demo_cash_php -= allocation_php
        log(f"DEMO BUY executed: bought {quantity:.8f} BTC for {format_php(allocation_php)} at {format_usd(current_price)}")

    def _demo_sell(self, level, current_price):
        if self.demo_base <= 0:
            log("DEMO sell skipped: no BTC available.")
            return

        allocation_php = (self.demo_cash_php + self.demo_base * current_price * self.usd_to_php) * (self.allocation_percent / 100)
        price_php = current_price * self.usd_to_php
        quantity = min(self.demo_base, allocation_php / price_php)
        if quantity <= 0:
            log("DEMO sell skipped: allocation too small.")
            return

        self.demo_base -= quantity
        self.demo_cash_php += quantity * price_php
        log(f"DEMO SELL executed: sold {quantity:.8f} BTC for {format_php(quantity * price_php)} at {format_usd(current_price)}")

    # --- LIVE MODE LOGIC ---
    def _live_buy(self, level, current_price):
        try:
            wallet_php, base_free, quote_free = self.get_live_wallet_value_php(current_price)
            allocation_php = wallet_php * (self.allocation_percent / 100)
            allocation_usdt = allocation_php / self.usd_to_php
            quantity = allocation_usdt / current_price
            if allocation_usdt > quote_free:
                allocation_usdt = quote_free
                quantity = quote_free / current_price
            if quantity <= 0:
                log("LIVE buy skipped: insufficient USDT balance.")
                return

            order = self.exchange.create_market_buy_order(self.symbol, quantity)
            log(f"LIVE BUY order placed: {quantity:.8f} {self.symbol.split('/')[0]} | order id: {order.get('id')}")
        except Exception as ex:
            log(f"LIVE buy failed: {ex}")
            traceback.print_exc()

    def _live_sell(self, level, current_price):
        try:
            wallet_php, base_free, quote_free = self.get_live_wallet_value_php(current_price)
            allocation_php = wallet_php * (self.allocation_percent / 100)
            price_php = current_price * self.usd_to_php
            quantity = allocation_php / price_php
            if quantity > base_free:
                quantity = base_free
            if quantity <= 0:
                log("LIVE sell skipped: insufficient base asset balance.")
                return

            order = self.exchange.create_market_sell_order(self.symbol, quantity)
            log(f"LIVE SELL order placed: {quantity:.8f} {self.symbol.split('/')[0]} | order id: {order.get('id')}")
        except Exception as ex:
            log(f"LIVE sell failed: {ex}")
            traceback.print_exc()


def main():
    bot = GridTradingBot()
    bot.run()


if __name__ == "__main__":
    main()
