# Botspot - Automated Bybit Spot Trading Bot

An intelligent, fully automated trading bot for Bybit spot market. Implements a proven "Buy Low, Sell High" strategy using 7-day chart analysis to identify optimal entry and exit points.

## 🎯 Quick Summary

- **Strategy**: Buy Low, Sell High with 7-day chart analysis
- **Target Profit**: 7% minimum gain before selling
- **Trading Pairs**: BTCUSDT, ETHUSDT, SOLUSDT + Top 3 market gainers
- **Modes**: Demo (local simulated orders using Bybit chart data) and Real (mainnet) trading
- **Currency**: Philippine Peso (PHP) support for trade amounts
- **Fully Automated**: Runs 24/7 analyzing and executing trades

## ✨ Features

- ✅ Automated support/resistance level detection
- ✅ Intelligent buy/sell signal generation
- ✅ Demo mode for safe testing
- ✅ Real-time market analysis
- ✅ Comprehensive trade logging
- ✅ Graceful error handling
- ✅ Top gainers auto-detection
- ✅ Multiple trading pair support
- ✅ Configurable profit targets
- ✅ Rate-limited API calls

## 🚀 Quick Start

### Installation

```bash
# Clone the repository (if not already done)
git clone https://github.com/raylaraykapre/Botspot.git
cd Botspot

# Run setup wizard
python setup.py
```

### Configuration

The setup wizard will guide you through:
1. Bybit API key setup (demo and/or real)
2. Trading preferences (amount, profit target)
3. Auto-trading enablement

### Start Trading

```bash
# Run the bot
python launch_bot.py
```

**First Time?** Start in demo mode (TRADING_MODE=demo) to test!

## 📖 Documentation

- **[README_BOT.md](README_BOT.md)** - Comprehensive bot documentation
- **[bot_config.py](bot_config.py)** - Configuration reference
- **[strategy.py](strategy.py)** - Strategy implementation details
- **[bybit_trader.py](bybit_trader.py)** - API integration code

## 📊 Strategy Overview

### Buy Signal
When all these conditions are met:
- Price is within 2% of the 7-day support level (lowest price)
- Price is below the 7-day average price
- No existing position in that cryptocurrency

### Sell Signal
When all these conditions are met:
- Profit is at or exceeds 7% target
- Price is within 2% of the 7-day resistance level (highest price)
- Active position exists in that cryptocurrency

### Example
```
BTC 7-Day Analysis:
- Support (Low):     $45,000
- Resistance (High): $48,500  
- Average:          $46,800

Current Price: $45,200
→ BUY SIGNAL (below average, near support)

Entry at $45,200, Profit Target: $48,364 (7% gain)
→ SELL when profit ≥ 7% and price near resistance
```

## 🎯 Trading Pairs

**Default Pairs:**
- BTCUSDT (Bitcoin)
- ETHUSDT (Ethereum)
- SOLUSDT (Solana)

**Dynamic Pairs:**
- Top 3 market gainers (auto-detected every cycle)

## 🛠️ Configuration

### Key Settings (.env)

```env
# Trading Mode
TRADING_MODE=demo              # 'demo' or 'real'
ENABLE_AUTO_TRADING=false      # Enable actual trading

# Trading Parameters
BUY_AMOUNT_PHP=5000            # Amount per trade (PHP)
PROFIT_TARGET_PERCENT=7        # Minimum profit target
UPDATE_INTERVAL_SECONDS=300    # Check every 5 minutes

# API Keys (from Bybit)
BYBIT_API_KEY_DEMO=xxx
BYBIT_API_SECRET_DEMO=xxx
BYBIT_API_KEY_REAL=xxx
BYBIT_API_SECRET_REAL=xxx
```

## 📁 Project Structure

```
Botspot/
├── launch_bot.py           # Main entry point
├── bybit_trader.py         # Trading engine
├── strategy.py             # Buy/sell strategy
├── bot_config.py           # Configuration
├── setup.py                # Setup wizard
├── requirements.txt        # Dependencies
├── .env.example            # Example config
├── .env                    # Your config (created)
├── trading_bot.log         # Trade logs
├── README.md               # This file
├── README_BOT.md           # Detailed documentation
└── .gitignore              # Git ignore rules
```

## 🔐 Security

- **API Keys**: Stored locally in `.env` (never committed)
- **Testnet First**: Always test in demo mode initially
- **Small Amounts**: Start with small trade amounts
- **IP Whitelist**: Configure on Bybit for additional security
- **Audit Logs**: All trades logged to `trading_bot.log`

## 📈 Performance

Track your bot's performance:
- Total trades executed
- Win rate (% profitable trades)
- Average profit per trade
- Portfolio balance
- Open positions

View in bot logs or check:
```bash
tail -f trading_bot.log | grep "PORTFOLIO STATUS"
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| API connection error | Verify credentials in `.env` |
| No buy/sell signals | Market may not match strategy; check logs |
| Insufficient balance | Reduce `BUY_AMOUNT_PHP` in `.env` |
| Rate limit errors | Increase `UPDATE_INTERVAL_SECONDS` |

See [README_BOT.md](README_BOT.md) for detailed troubleshooting.

## 📝 Logs

Monitor bot activity:
```bash
# Watch live logs
tail -f trading_bot.log

# View buy signals
grep "BUY SIGNAL" trading_bot.log

# View sell signals  
grep "SELL SIGNAL" trading_bot.log

# Check errors
grep "ERROR" trading_bot.log
```

## ⚠️ Important Disclaimer

This bot is provided for educational purposes. Trading cryptocurrencies involves risk:
- **Volatile Market**: Prices can change rapidly
- **Strategy Risk**: No strategy guarantees profits
- **Test First**: Use demo mode extensively before real trading
- **Small Amounts**: Start small and scale gradually
- **Your Decision**: You are responsible for trading decisions
- **Past Performance**: Does not guarantee future results

**Start small, test thoroughly, understand the risks.** 🎯

## 🤝 Contributing

To improve the bot:
1. Fork the repository
2. Create a feature branch
3. Make your improvements
4. Commit and push
5. Create a Pull Request

## 📞 Support

- **Documentation**: See [README_BOT.md](README_BOT.md)
- **Bybit Docs**: https://bybit-exchange.github.io/docs/spot/
- **Logs**: Check `trading_bot.log` for detailed information

## 📜 License

MIT License - See LICENSE file

## 🎉 Get Started

```bash
# 1. Setup (interactive wizard)
python setup.py

# 2. Review configuration
cat .env

# 3. Start in demo mode
python launch_bot.py

# 4. Monitor logs
tail -f trading_bot.log

# 5. When confident, enable real trading
# Edit .env: TRADING_MODE=real, ENABLE_AUTO_TRADING=true
```

---

**Happy trading! Remember: Start small, think long-term, manage risk.** 🚀