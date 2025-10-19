#!/usr/bin/env python3
"""
Test Telegram bot connection and send a test message.
"""

import sys
import requests
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except ImportError:
    print("❌ telegram_config.py not found!")
    sys.exit(1)

def test_telegram_connection():
    """Test Telegram bot connection and send test message."""
    
    if TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("❌ Telegram not configured!")
        print("\n📱 Setup steps:")
        print("1. Message @GiddyUpBot on Telegram")
        print("2. Run: curl -s \"https://api.telegram.org/bot8419851120:AAHTWE5k67fR7_wuyS5Lv9JFjKJ30ODClHI/getUpdates\" | python3 -m json.tool")
        print("3. Find your chat ID and update telegram_config.py")
        return False
    
    print(f"🤖 Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"💬 Chat ID: {TELEGRAM_CHAT_ID}")
    
    # Test message
    message = """🎉 TELEGRAM CONNECTION TEST - 2025-10-18

✅ Bot is working!
📊 Your betting results are ready to be sent.

🏆 BIG WINNER: Crown Of Oaks (GB) @ Ascot
💰 P&L: £+50.09

📈 Daily Summary:
• Wins: 4
• Losses: 32  
• Total P&L: £-283.91
• Win Rate: 11.1%

#HorseRacing #Betting #Results"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Test message sent successfully!")
            print(f"📱 Message ID: {result['result']['message_id']}")
            return True
        else:
            print(f"❌ Failed to send message: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

if __name__ == "__main__":
    test_telegram_connection()
