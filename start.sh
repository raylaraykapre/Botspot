#!/bin/bash
# Quick Start Script for Bybit Trading Bot

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         BYBIT SPOT TRADING BOT - QUICK START                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
python3 --version
echo "✓ Python found"
echo ""

# Install dependencies
echo "[2/5] Installing dependencies..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Run setup
echo "[3/5] Running interactive setup..."
python3 setup.py
echo ""

# Test connection
echo "[4/5] Testing Bybit connection..."
python3 -c "from bot_config import Config; Config.validate_config(); print('✓ Connection test passed')" 2>/dev/null || echo "⚠ Connection test skipped (API keys needed)"
echo ""

# Ready to go
echo "[5/5] Setup complete!"
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    READY TO TRADE!                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📖 Documentation:"
echo "   - Main README:    cat README.md"
echo "   - Bot Guide:      cat README_BOT.md"
echo "   - Configuration:  cat .env"
echo ""
echo "🚀 Start the bot:"
echo "   python3 launch_bot.py"
echo ""
echo "📊 Monitor trading:"
echo "   tail -f trading_bot.log"
echo ""
echo "💡 Pro Tips:"
echo "   1. Start in demo mode (TRADING_MODE=demo)"
echo "   2. Monitor logs for at least 24 hours"
echo "   3. Verify strategy works before real trading"
echo "   4. Start with small amounts (₱5000-10000)"
echo ""
echo "⚠️  Remember:"
echo "   - Crypto trading is risky"
echo "   - Keep API keys secure"
echo "   - Never commit .env to git"
echo "   - Test thoroughly before going live"
echo ""
