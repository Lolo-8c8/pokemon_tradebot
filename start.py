#!/usr/bin/env python3
"""
Discord Bot Startup Script
Handles common startup issues and provides helpful error messages
"""

import os
import sys
import logging
from pathlib import Path

def check_requirements():
    """Check if all required files and dependencies exist"""
    issues = []
    
    # Check for .env file
    if not os.path.exists('.env'):
        issues.append("❌ .env file not found")
        issues.append("   Create a .env file with: DISCORD_TOKEN=your_token_here")
    else:
        # Check if DISCORD_TOKEN is in .env
        with open('.env', 'r') as f:
            content = f.read()
            if 'DISCORD_TOKEN' not in content or 'your_token_here' in content:
                issues.append("❌ DISCORD_TOKEN not properly configured in .env")
                issues.append("   Set DISCORD_TOKEN=your_actual_bot_token")
    
    # Check for cogs directory
    if not os.path.exists('cogs'):
        issues.append("❌ cogs directory not found")
        issues.append("   The cogs directory should contain your command modules")
    
    # Check for required Python files
    required_files = ['bot.py', 'config.py']
    for file in required_files:
        if not os.path.exists(file):
            issues.append(f"❌ {file} not found")
    
    return issues

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main startup function"""
    print("🤖 Discord Bot Startup Check")
    print("=" * 40)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check requirements
    issues = check_requirements()
    
    if issues:
        print("\n🚨 Startup Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        
        print("\n💡 Quick Fix Guide:")
        print("  1. Copy .env.example to .env")
        print("  2. Edit .env and add your Discord bot token")
        print("  3. Get a token from: https://discord.com/developers/applications")
        print("  4. Run: uv sync (to install dependencies)")
        print("  5. Run: uv run python bot.py")
        
        return False
    
    print("✅ All checks passed!")
    print("🚀 Starting Discord Bot...")
    
    # Import and run the bot
    try:
        from bot import main as bot_main
        import asyncio
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        print(f"\n💥 Bot crashed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

