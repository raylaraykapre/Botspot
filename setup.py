#!/usr/bin/env python3
"""
Quick setup and configuration script for Bybit Trading Bot
"""

import os
import sys
from pathlib import Path


def setup_environment():
    """Setup environment variables"""
    print("\n" + "="*70)
    print("BYBIT TRADING BOT - CONFIGURATION SETUP")
    print("="*70)
    
    env_file = ".env"
    
    # Check if .env exists
    if os.path.exists(env_file):
        print(f"\n✓ {env_file} already exists")
        response = input("Do you want to reconfigure? (y/n): ").strip().lower()
        if response != 'y':
            print("Skipping configuration")
            return True
    
    print("\n" + "-"*70)
    print("DEMO MODE CONFIGURATION (Local demo trading using Bybit charts)")
    print("-"*70)
    
    print("\nDemo mode does not require Bybit API keys.")
    print("The engine uses local simulation and public chart data only.")
    
    demo_api_key = ''
    demo_api_secret = ''
    
    print("\n" + "-"*70)
    print("REAL MODE CONFIGURATION (Live Trading)")
    print("-"*70)
    
    print("\nTo get Real API keys:")
    print("1. Go to: https://www.bybit.com/")
    print("2. Login to your account")
    print("3. Account Settings → API Management → Create New Key")
    print("⚠️  NEVER share your real API keys!")
    print("\nEnter your Real API credentials (or press Enter to skip):")
    
    real_api_key = input("Real API Key (BYBIT_API_KEY_REAL): ").strip()
    real_api_secret = input("Real API Secret (BYBIT_API_SECRET_REAL): ").strip()
    
    print("\n" + "-"*70)
    print("TRADING CONFIGURATION")
    print("-"*70)
    
    print("\nSelect trading mode:")
    print("1. Demo (Testnet - No real money)")
    print("2. Real (Mainnet - Live trading)")
    
    mode_choice = input("Choose mode (1 or 2): ").strip()
    trading_mode = 'real' if mode_choice == '2' else 'demo'
    
    print("\nEnter trading settings:")
    
    buy_amount = input("Buy amount in PHP (default: 5000): ").strip() or "5000"
    profit_target = input("Profit target % (default: 7): ").strip() or "7"
    demo_balance = input("Demo starting balance in PHP (default: 100000): ").strip() or "100000"
    php_usd_rate = input("PHP to USD conversion rate (default: 0.018): ").strip() or "0.018"
    update_interval = input("Update interval in seconds (default: 300): ").strip() or "300"
    
    enable_trading = input("Enable auto-trading? (y/n, default: n): ").strip().lower()
    enable_trading = 'true' if enable_trading == 'y' else 'false'
    
    # Create .env content
    env_content = f"""# Bybit API Configuration
BYBIT_API_KEY_DEMO={demo_api_key}
BYBIT_API_SECRET_DEMO={demo_api_secret}
BYBIT_API_KEY_REAL={real_api_key}
BYBIT_API_SECRET_REAL={real_api_secret}

# Trading Mode: 'demo' or 'real'
TRADING_MODE={trading_mode}

# Currency Settings
BASE_CURRENCY=PHP
FIAT_CURRENCY=USDT

# Trading Settings
BUY_AMOUNT_PHP={buy_amount}
PROFIT_TARGET_PERCENT={profit_target}
DEMO_STARTING_BALANCE_PHP={demo_balance}
PHP_USD_RATE={php_usd_rate}
TRADING_PAIRS=BTCUSDT,ETHUSDT,SOLUSDT

# Chart Analysis
CANDLE_PERIOD=D
LOOKBACK_DAYS=7

# Bot Settings
UPDATE_INTERVAL_SECONDS={update_interval}
ENABLE_AUTO_TRADING={enable_trading}

# Logging
LOG_LEVEL=INFO
"""
    
    # Write .env file
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        os.chmod(env_file, 0o600)  # Restrict file permissions
        print(f"\n✓ Configuration saved to {env_file}")
        return True
    except Exception as e:
        print(f"\n✗ Error writing {env_file}: {e}")
        return False


def install_dependencies():
    """Install Python dependencies"""
    print("\n" + "-"*70)
    print("INSTALLING DEPENDENCIES")
    print("-"*70)
    
    try:
        import subprocess
        print("\nInstalling required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
        print("✓ Dependencies installed successfully")
        return True
    except Exception as e:
        print(f"✗ Error installing dependencies: {e}")
        print("\nYou can install manually with:")
        print("  pip install -r requirements.txt")
        return False


def verify_setup():
    """Verify the setup"""
    print("\n" + "-"*70)
    print("VERIFYING SETUP")
    print("-"*70)
    
    checks = [
        (".env file exists", os.path.exists(".env")),
        ("requirements.txt exists", os.path.exists("requirements.txt")),
        ("bot_config.py exists", os.path.exists("bot_config.py")),
        ("bybit_trader.py exists", os.path.exists("bybit_trader.py")),
        ("strategy.py exists", os.path.exists("strategy.py")),
        ("launch_bot.py exists", os.path.exists("launch_bot.py")),
    ]
    
    all_ok = True
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        all_ok = all_ok and result
    
    return all_ok


def print_next_steps():
    """Print next steps for user"""
    print("\n" + "="*70)
    print("SETUP COMPLETE!")
    print("="*70)
    
    print("\n📚 Next steps:")
    print("1. Review your configuration in .env file")
    print("2. Test with demo mode first (TRADING_MODE=demo)")
    print("3. Start the bot with: python launch_bot.py")
    print("\n💡 For real trading:")
    print("   - Set TRADING_MODE=real in .env")
    print("   - Set ENABLE_AUTO_TRADING=true")
    print("   - Start with small amounts to test")
    
    print("\n📖 Documentation:")
    print("   - See README_BOT.md for detailed information")
    print("   - See strategy.py for strategy details")
    
    print("\n⚠️  Important:")
    print("   - Start in demo mode to test the bot first")
    print("   - Keep API keys secure (never commit .env)")
    print("   - Monitor trades and logs regularly")
    print("   - Start with small trade amounts")
    
    print("\n" + "="*70 + "\n")


def main():
    """Main setup function"""
    try:
        # Setup environment
        if not setup_environment():
            print("\n✗ Configuration setup failed")
            return False
        
        # Install dependencies
        if not install_dependencies():
            print("\n⚠️  Warning: Dependencies installation may have failed")
            print("You might need to install them manually")
        
        # Verify setup
        if not verify_setup():
            print("\n✗ Some setup files are missing")
            return False
        
        # Print next steps
        print_next_steps()
        return True
        
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
