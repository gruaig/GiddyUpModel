#!/usr/bin/env python3
"""
Twitch Chat Bot Integration

Sends betting updates to your Twitch chat in real-time.

Setup:
1. Copy twitch_config.template.py to twitch_config.py
2. Add your Twitch credentials
3. Run python3 twitch_bot.py to test
"""

import socket
import time
from typing import Optional

# Try to import config
try:
    from twitch_config import (
        TWITCH_CHANNEL,
        TWITCH_BOT_USERNAME,
        TWITCH_OAUTH_TOKEN,
        SEND_MORNING_SUMMARY,
        SEND_BET_PLACED,
        SEND_BET_SKIPPED,
        SEND_RESULTS
    )
    TWITCH_ENABLED = True
except ImportError:
    TWITCH_ENABLED = False
    TWITCH_CHANNEL = None
    TWITCH_BOT_USERNAME = None
    TWITCH_OAUTH_TOKEN = None
    SEND_MORNING_SUMMARY = False
    SEND_BET_PLACED = False
    SEND_BET_SKIPPED = False
    SEND_RESULTS = False


class TwitchBot:
    """Simple Twitch IRC bot for sending messages."""
    
    def __init__(self):
        self.sock = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to Twitch IRC."""
        if not TWITCH_ENABLED:
            return False
        
        try:
            self.sock = socket.socket()
            self.sock.connect(('irc.chat.twitch.tv', 6667))
            
            # Authenticate
            self.sock.send(f"PASS {TWITCH_OAUTH_TOKEN}\n".encode('utf-8'))
            self.sock.send(f"NICK {TWITCH_BOT_USERNAME}\n".encode('utf-8'))
            self.sock.send(f"JOIN #{TWITCH_CHANNEL}\n".encode('utf-8'))
            
            time.sleep(1)
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Twitch connection error: {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """Send message to Twitch chat."""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            self.sock.send(f"PRIVMSG #{TWITCH_CHANNEL} :{message}\n".encode('utf-8'))
            return True
        except Exception as e:
            print(f"Twitch send error: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Twitch."""
        if self.sock:
            self.sock.close()
            self.connected = False


# Global bot instance
_twitch_bot = None


def get_bot() -> TwitchBot:
    """Get or create Twitch bot instance."""
    global _twitch_bot
    if _twitch_bot is None:
        _twitch_bot = TwitchBot()
    return _twitch_bot


def send_to_twitch(message: str) -> bool:
    """Send a message to Twitch chat."""
    if not TWITCH_ENABLED:
        return False
    
    bot = get_bot()
    return bot.send_message(message)


def send_morning_summary(date: str, total_bets: int, total_stake: float) -> bool:
    """Send morning summary to Twitch."""
    if not SEND_MORNING_SUMMARY:
        return False
    
    message = f"🏇 LIVE BETTING STREAM! Today's card: {total_bets} selections, £{total_stake:.2f} total stake. Let's make some money! 💰"
    return send_to_twitch(message)


def send_bet_placed(horse: str, course: str, race_time: str, odds: float, 
                   stake: float, profit: float) -> bool:
    """Send bet placed to Twitch."""
    if not SEND_BET_PLACED:
        return False
    
    message = f"🎯 BET PLACED! {horse} @ {course} ({race_time}) | £{stake:.2f} @ {odds:.2f} | Potential profit: £{profit:.2f} LET'S GOOO! 🚀"
    return send_to_twitch(message)


def send_bet_skipped(horse: str, course: str, reason: str) -> bool:
    """Send bet skipped to Twitch."""
    if not SEND_BET_SKIPPED:
        return False
    
    message = f"⏭️ SKIPPED: {horse} @ {course} - {reason}"
    return send_to_twitch(message)


def send_win(horse: str, course: str, pnl: float) -> bool:
    """Send win result to Twitch."""
    if not SEND_RESULTS:
        return False
    
    message = f"🎉🎉🎉 WINNER! {horse} @ {course} won! Profit: £{pnl:+.2f}! YESSS! 🏆💰"
    return send_to_twitch(message)


def send_loss(horse: str, course: str, pnl: float) -> bool:
    """Send loss result to Twitch."""
    if not SEND_RESULTS:
        return False
    
    message = f"😔 Lost: {horse} @ {course} - £{abs(pnl):.2f}. On to the next one! 💪"
    return send_to_twitch(message)


def send_daily_summary(wins: int, losses: int, total_pnl: float) -> bool:
    """Send end of day summary to Twitch."""
    
    result_emoji = "📈" if total_pnl > 0 else "📉"
    message = f"{result_emoji} END OF DAY: {wins}W-{losses}L | P&L: £{total_pnl:+.2f} | Thanks for watching! 🏇"
    return send_to_twitch(message)


def test_connection() -> bool:
    """Test Twitch connection."""
    if not TWITCH_ENABLED:
        print("❌ Twitch not configured")
        print("   Copy twitch_config.template.py to twitch_config.py")
        return False
    
    message = "🤖 GiddyUp bot connected! Stream starting soon! 🏇"
    
    success = send_to_twitch(message)
    
    if success:
        print("✅ Twitch test message sent successfully!")
        print(f"   Channel: #{TWITCH_CHANNEL}")
    else:
        print("❌ Failed to send Twitch message")
        print("   Check your OAuth token and channel name")
    
    return success


if __name__ == "__main__":
    # Test the connection
    test_connection()

