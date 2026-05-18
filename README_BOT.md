# Bybit Spot Trading Bot

An automated trading bot for Bybit spot market using a "Buy Low, Sell High" strategy with 7-day chart analysis. Supports both demo (testnet) and real-time trading with Philippine Peso support.

## Features

✨ **Trading Strategy:**
- Buy Low, Sell High strategy based on 7-day chart analysis
- Automatic detection of support (buy) and resistance (sell) levels
- Minimum 7% profit target requirement before selling
- Volatility-based analysis for optimal entry/exit points

📊 **Trading Pairs:**
- BTCUSDT (Bitcoin)
- ETHUSDT (Ethereum)
- SOLUSDT (Solana)
- Top 3 gainers from the market (auto-detected)

🌐 **Modes:**
- **Demo Mode**: Local simulation engine using Bybit chart data for pricing and signals
- **Real Mode**: Live trading on Bybit Mainnet

💱 **Currency Support:**
- Philippine Peso (PHP) based trade amounts
- USDT/USD pricing and calculations

🤖 **Automation:**
- Fully automated trading cycles
- Configurable trade intervals
- Graceful shutdown handling
- Comprehensive logging and monitoring

## Quick Start

### 1. Initial Setup

```bash
# Clone or navigate to the repository
cd Botspot

# Run the setup script
python setup.py
```

The setup script will:
- Guide you through configuration
- Create `.env` file with your API credentials
- Install dependencies
- Verify all components

### 2. Configuration

Edit the created `.env` file:

```bash
# Demo API credentials (from https://testnet.bybit.com/)
BYBIT_API_KEY_DEMO=your_demo_key
BYBIT_API_SECRET_DEMO=your_demo_secret

# Real API credentials (from https://www.bybit.com/)
BYBIT_API_KEY_REAL=your_real_key
BYBIT_API_SECRET_REAL=your_real_secret

# Trading mode
TRADING_MODE=demo  # Change to 'real' for live trading

# Trading settings
BUY_AMOUNT_PHP=5000  # Amount in PHP per trade
PROFIT_TARGET_PERCENT=7  # Minimum profit % before selling
UPDATE_INTERVAL_SECONDS=300  # Check market every 5 minutes
ENABLE_AUTO_TRADING=false  # Set to true to enable actual trading
```

### 3. Start the Bot

```bash
# Start trading bot
python launch_bot.py
```

The bot will:
1. Connect to Bybit API
2. Load trading strategy
3. Begin analyzing trading pairs every 5 minutes
4. Execute buy/sell signals automatically (if enabled)
5. Log all activities to `trading_bot.log`

## Strategy Details

### Buy Signal Conditions
- Price is within 2% of the 7-day support level (lowest price)
- Price is lower than the 7-day average price
- No existing position in that pair

### Sell Signal Conditions
- Profit percentage ≥ profit target (default: 7%)
- Price is within 2% of the 7-day resistance level (highest price)
- Active position in that pair

### Price Analysis
```
Support Level = Lowest price in last 7 days
Resistance Level = Highest price in last 7 days
Average Price = Mean of last 7 daily closes
```

## Project Structure

```
Botspot/
├── launch_bot.py          # Main entry point - launches the trading bot
├── bybit_trader.py        # Core trading engine and API integration
├── strategy.py            # Trading strategy implementation
├── bot_config.py          # Configuration management
├── setup.py               # Setup and configuration wizard
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment configuration
├── .env                   # Your API credentials (created by setup)
├── trading_bot.log        # Trading activity logs
└── README_BOT.md          # This file
```

## File Descriptions

### launch_bot.py
- Entry point for the bot
- Manages bot lifecycle (startup, shutdown, scheduling)
- Handles graceful shutdown on Ctrl+C
- Schedules recurring trading cycles

### bybit_trader.py
- Core trading engine
- Bybit API communication
- Order placement (buy/sell)
- Price and chart data retrieval
- Market analysis and top gainers detection

### strategy.py
- Trading strategy implementation
- Support/resistance level detection
- Buy/sell signal generation
- Profit calculation

### bot_config.py
- Centralized configuration management
- Environment variable loading
- API credential handling
- Validates configuration

## Usage Examples

### Demo Mode (Recommended First)
In demo mode the bot runs a local simulation engine. It still uses live market data from Bybit charts for price and signal analysis, but all buy/sell orders are simulated locally and are not placed on the exchange.

```bash
# .env configuration
TRADING_MODE=demo
ENABLE_AUTO_TRADING=false  # Monitor without actual trades

# Run bot
python launch_bot.py

# Watch the logs to see signals and analysis
tail -f trading_bot.log
```

### Real Mode
```bash
# .env configuration
TRADING_MODE=real
ENABLE_AUTO_TRADING=true
BUY_AMOUNT_PHP=5000

# Run bot
python launch_bot.py
```

### Custom Trading Pairs
Edit the `DEFAULT_PAIRS` in `bot_config.py`:
```python
DEFAULT_PAIRS = [
    'BTCUSDT',
    'ETHUSDT',
    'SOLUSDT',
    'ADAUSDT',  # Add custom pairs
    'XRPUSDT',
]
```

## Monitoring

### View Logs
```bash
# Real-time log viewing
tail -f trading_bot.log

# View specific section
grep "BUY SIGNAL" trading_bot.log
grep "SELL SIGNAL" trading_bot.log
grep "ERROR" trading_bot.log
```

### Bot Output Format
```
===== TRADING CYCLE =====
Analyzing BTCUSDT
  Support: 45000.50
  Resistance: 48500.75
  Current Price: 46200.00
  Average Price: 46800.00
  Action: BUY
  
Analyzing ETHUSDT
  Support: 2800.25
  Current Price: 2850.00
  Action: HOLD (position open, profit: 2.3%)
```

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| TRADING_MODE | demo | 'demo' for testnet, 'real' for mainnet |
| BUY_AMOUNT_PHP | 5000 | Amount in PHP to spend per buy signal |
| PROFIT_TARGET_PERCENT | 7 | Minimum profit % before selling |
| UPDATE_INTERVAL_SECONDS | 300 | Seconds between trading cycles (5 min) |
| LOOKBACK_DAYS | 7 | Days of history for analysis |
| CANDLE_PERIOD | D | Candle period (D for daily) |
| ENABLE_AUTO_TRADING | false | Enable actual order placement |
| LOG_LEVEL | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

## API Key Setup

### Demo Mode API Keys

1. Go to https://testnet.bybit.com/
2. Sign up or login
3. API Management → Create New Key
4. Select "Spot Trading" permissions
5. Copy API Key and Secret to `.env`

### Real Mode API Keys

1. Go to https://www.bybit.com/
2. Login to your account
3. Account Settings → API Management → Create New Key
4. Configure permissions:
   - Enable: Spot Trading
   - Disable: Copy Trading (optional)
   - Set IP whitelist for security
5. Copy API Key and Secret to `.env`

⚠️ **IMPORTANT**: Never share API keys or commit `.env` to version control!

## Safety Considerations

1. **Start Small**: Test with small amounts in demo mode first
2. **API Key Security**: 
   - Keep `.env` file secret
   - Add `.env` to `.gitignore`
   - Use IP whitelist on Bybit API keys
3. **Market Risk**: 
   - Cryptocurrency markets are volatile
   - Strategy can lose money in unfavorable conditions
   - Test thoroughly before using real money
4. **Rate Limiting**: 
   - Bot respects API rate limits
   - Built-in delays between requests
5. **Monitoring**: 
   - Regularly check logs
   - Monitor portfolio status
   - Watch market conditions

## Troubleshooting

### Bot Won't Connect
```
ERROR: Failed to connect to Bybit API
```
**Solution:**
- Verify API keys in `.env`
- Check internet connectivity
- Ensure API is enabled on Bybit
- Check IP whitelist settings

### No Buy/Sell Signals
```
No buy signal. Current: 45000, Support: 44500, Avg: 46000
```
**Solution:**
- Current price may not match strategy conditions
- Increase monitoring period or adjust profit target
- Check market conditions match strategy

### Order Placement Failed
```
ERROR: Buy order failed: Insufficient balance
```
**Solution:**
- Ensure account has sufficient balance
- Reduce BUY_AMOUNT_PHP in `.env`
- Check order type and parameters

### API Rate Limit
```
ERROR: Rate limit exceeded
```
**Solution:**
- Increase UPDATE_INTERVAL_SECONDS in `.env`
- Reduce number of trading pairs
- Wait before making more requests

## Performance Metrics

The bot tracks:
- **Trade Count**: Total number of executed trades
- **Win Rate**: Percentage of profitable trades
- **Average Profit**: Average profit per trade
- **Max Drawdown**: Largest loss from peak
- **Sharpe Ratio**: Risk-adjusted returns

View metrics in logs or portfolio status output.

## Customization

### Modify Strategy Thresholds
Edit `strategy.py`:
```python
# Change buy/sell conditions
SUPPORT_RANGE = 0.02  # 2% from support
RESISTANCE_RANGE = 0.02  # 2% from resistance
```

### Add New Trading Pairs
Edit `bot_config.py`:
```python
DEFAULT_PAIRS = [
    'BTCUSDT',
    'ETHUSDT',
    'SOLUSDT',
    'ADAUSDT',  # Add here
]
```

### Change Update Frequency
Edit `.env`:
```
UPDATE_INTERVAL_SECONDS=600  # Check every 10 minutes
```

## Advanced Usage

### Running Multiple Instances
```bash
# Terminal 1: Run with config 1
TRADING_MODE=demo python launch_bot.py

# Terminal 2: Run with config 2
TRADING_MODE=real python launch_bot.py
```

### Background Execution
```bash
# Run in background
nohup python launch_bot.py > bot.log 2>&1 &

# Check status
ps aux | grep launch_bot.py

# Stop bot
kill <pid>
```

### Docker Deployment
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "launch_bot.py"]
```

## Common Issues & Solutions

### Issue: "No module named 'pybit'"
```bash
pip install -r requirements.txt
```

### Issue: API credentials not found
```bash
# Make sure .env file exists and is in correct format
# Verify with:
python -c "from bot_config import Config; Config.validate_config()"
```

### Issue: Orders not executing
```bash
# Enable auto-trading in .env
ENABLE_AUTO_TRADING=true

# Or check if in demo mode:
TRADING_MODE=demo  # Won't execute real orders
```

## Performance Tips

1. **Optimize Update Interval**: 
   - Faster intervals = more overhead but quicker response
   - Slower intervals = less API calls but might miss signals

2. **Limit Trading Pairs**:
   - Fewer pairs = faster analysis
   - Recommended: 3-6 pairs for balance

3. **Monitor Logs Regularly**:
   - Catch errors early
   - Understand market behavior

## Future Enhancements

- [ ] Machine learning for signal optimization
- [ ] Multiple strategy modes (momentum, RSI, MACD)
- [ ] Portfolio rebalancing
- [ ] Risk management with stop-losses
- [ ] Discord/Telegram notifications
- [ ] Web dashboard for monitoring
- [ ] Backtesting engine

## Support & Community

- **Issues**: Check logs in `trading_bot.log`
- **Documentation**: See README_BOT.md
- **Bybit API Docs**: https://bybit-exchange.github.io/docs/spot/

## License

MIT License - See LICENSE file

## Disclaimer

⚠️ **IMPORTANT**: 
- This bot is provided as-is for educational purposes
- Trading cryptocurrencies involves risk
- Past performance does not guarantee future results
- Start with small amounts and demo mode
- Understand the strategy before using real money
- You are responsible for your own trading decisions

## Version History

### v1.0 - Initial Release
- Core buy low/sell high strategy
- 7-day chart analysis
- Demo and real mode support
- Multiple trading pairs
- Comprehensive logging

---

**Start trading smartly with Bybit Spot Trading Bot!** 🚀
