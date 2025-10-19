#!/usr/bin/env python3
"""
Telegram Bot Integration for GiddyUp Horse Racing Bot

Sends betting notifications to Telegram channel/group.
"""

import requests
from typing import Optional
from pathlib import Path

# Try to import config
try:
    from telegram_config import (
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        TELEGRAM_CHANNEL_ID,
        SEND_MORNING_PICKS,
        SEND_BET_PLACED,
        SEND_BET_SKIPPED,
        SEND_MARKET_ANALYSIS,
        SEND_RESULTS
    )
    TELEGRAM_ENABLED = True
except ImportError:
    TELEGRAM_ENABLED = False
    TELEGRAM_BOT_TOKEN = None
    TELEGRAM_CHAT_ID = None
    TELEGRAM_CHANNEL_ID = None
    SEND_MORNING_PICKS = False
    SEND_BET_PLACED = False
    SEND_BET_SKIPPED = False
    SEND_MARKET_ANALYSIS = False
    SEND_RESULTS = False


def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """
    Send a message to Telegram channel.
    
    Args:
        message: Message text (supports HTML or Markdown)
        parse_mode: "HTML" or "Markdown"
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not TELEGRAM_ENABLED:
        return False
    
    # Use channel ID if available, otherwise fall back to personal chat
    chat_id = TELEGRAM_CHANNEL_ID if TELEGRAM_CHANNEL_ID else TELEGRAM_CHAT_ID
    
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def send_morning_picks(date: str, selections: list) -> bool:
    """Send morning picks summary to Telegram."""
    if not SEND_MORNING_PICKS:
        return False
    
    total_stake = sum(float(sel.get('stake_gbp', 0)) for sel in selections)
    
    message = f"""🏇 <b>GiddyUp Betting Card - {date}</b>

📊 <b>Daily Selections</b>
━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>Total Selections:</b> {len(selections)}
💰 <b>Total Stake:</b> £{total_stake:.2f}

<b>Today's Bets:</b>
"""
    
    for i, sel in enumerate(selections, 1):
        strategy_emoji = "🟢" if sel['strategy'] == 'A-Hybrid_V3' else "🔵"
        message += f"\n{strategy_emoji} <b>{sel['time']}</b> {sel['course']}"
        message += f"\n   🏇 {sel['horse']}"
        message += f"\n   💰 £{sel['stake_gbp']} @ {sel['odds']}"
        message += f"\n   📊 Min: {sel['min_odds_needed']}"
        
        if i < len(selections):
            message += "\n"
    
    message += f"""
━━━━━━━━━━━━━━━━━━━━━━
🎯 Bets placed at T-60 if odds ≥ minimum

#HorseRacing #Betting #GiddyUp"""
    
    return send_telegram_message(message)


def send_bet_placed(horse: str, course: str, race_time: str, odds: float, 
                   stake: float, strategy: str, expected_odds: float, 
                   is_dry_run: bool = True) -> bool:
    """Send bet placed notification to Telegram."""
    if not SEND_BET_PLACED:
        return False
    
    strategy_emoji = "🟢" if strategy == 'A-Hybrid_V3' else "🔵"
    mode = "🟡 DRY RUN" if is_dry_run else "🔴 LIVE"
    
    gross_return = odds * stake
    profit = gross_return - stake
    
    message = f"""🎯 <b>BET PLACED</b> {mode}

{strategy_emoji} <b>{strategy}</b>

🏇 <b>{horse}</b>
📍 {course}
⏰ Race: <b>{race_time}</b>

💰 <b>Stake:</b> £{stake:.2f}
📊 <b>Odds:</b> {odds:.2f} (expected {expected_odds:.2f})
💵 <b>Potential Return:</b> £{gross_return:.2f}
✨ <b>Potential Profit:</b> £{profit:.2f}

#HorseRacing #Betting #BetPlaced"""
    
    return send_telegram_message(message)


def send_bet_skipped(horse: str, course: str, race_time: str, 
                    current_odds: float, min_odds: float, expected_odds: float,
                    reason: str, strategy: str) -> bool:
    """Send bet skipped notification to Telegram."""
    if not SEND_BET_SKIPPED:
        return False
    
    strategy_emoji = "🟢" if strategy == 'A-Hybrid_V3' else "🔵"
    
    message = f"""⏭️ <b>BET SKIPPED</b>

{strategy_emoji} <b>{strategy}</b>

🏇 <b>{horse}</b>
📍 {course}
⏰ Race: <b>{race_time}</b>

📊 <b>Odds Analysis:</b>
   Expected: {expected_odds:.2f}
   Current: {current_odds:.2f}
   Minimum: {min_odds:.2f}

⚠️ <b>Reason:</b> {reason}

#HorseRacing #Betting #Skipped"""
    
    return send_telegram_message(message)


def send_market_analysis(horse: str, course: str, race_time: str,
                        expected_odds: float, current_odds: float, 
                        min_odds: float, drift_pct: float, 
                        decision: str, strategy: str) -> bool:
    """Send market analysis to Telegram."""
    if not SEND_MARKET_ANALYSIS:
        return False
    
    strategy_emoji = "🟢" if strategy == 'A-Hybrid_V3' else "🔵"
    decision_emoji = "✅" if decision == "BET" else "⏭️"
    
    drift_str = f"{drift_pct:+.1f}%"
    
    message = f"""📊 <b>MARKET ANALYSIS</b>

{strategy_emoji} <b>{strategy}</b>

🏇 <b>{horse}</b>
📍 {course}
⏰ Race: <b>{race_time}</b>

📈 <b>Odds Comparison:</b>
   Expected: {expected_odds:.2f}
   Current: {current_odds:.2f}
   Minimum: {min_odds:.2f}
   Drift: {drift_str}

{decision_emoji} <b>Decision:</b> {decision}

#HorseRacing #MarketAnalysis"""
    
    return send_telegram_message(message)


def send_result(horse: str, course: str, race_time: str, 
               result: str, odds: float, stake: float, 
               pnl: float, strategy: str) -> bool:
    """Send bet result to Telegram."""
    if not SEND_RESULTS:
        return False
    
    if result.upper() == "WIN":
        emoji = "🎉"
        result_text = "WON"
    else:
        emoji = "😔"
        result_text = "LOST"
    
    strategy_emoji = "🟢" if strategy == 'A-Hybrid_V3' else "🔵"
    pnl_str = f"+£{pnl:.2f}" if pnl > 0 else f"£{pnl:.2f}"
    
    message = f"""{emoji} <b>BET {result_text}</b>

{strategy_emoji} <b>{strategy}</b>

🏇 <b>{horse}</b>
📍 {course}
⏰ Race: <b>{race_time}</b>

📊 <b>Result:</b> {result_text}
💰 <b>Stake:</b> £{stake:.2f} @ {odds:.2f}
💵 <b>P&L:</b> {pnl_str}

#HorseRacing #BetResult"""
    
    return send_telegram_message(message)


def send_daily_summary(date: str, total_bets: int, total_staked: float,
                      wins: int, losses: int, total_pnl: float) -> bool:
    """Send daily summary to Telegram."""
    
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    roi = (total_pnl / total_staked * 100) if total_staked > 0 else 0
    
    pnl_emoji = "📈" if total_pnl > 0 else "📉"
    pnl_str = f"+£{total_pnl:.2f}" if total_pnl > 0 else f"£{total_pnl:.2f}"
    
    message = f"""📊 <b>DAILY SUMMARY - {date}</b>

━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>Bets:</b> {total_bets}
💰 <b>Staked:</b> £{total_staked:.2f}

🏆 <b>Wins:</b> {wins}
😔 <b>Losses:</b> {losses}
📊 <b>Win Rate:</b> {win_rate:.1f}%

{pnl_emoji} <b>Total P&L:</b> {pnl_str}
📈 <b>ROI:</b> {roi:+.1f}%

━━━━━━━━━━━━━━━━━━━━━━
#HorseRacing #DailySummary #GiddyUp"""
    
    return send_telegram_message(message)


def test_telegram_connection() -> bool:
    """Test Telegram bot connection."""
    if not TELEGRAM_ENABLED:
        print("❌ Telegram not configured")
        print("   Copy telegram_config.template.py to telegram_config.py")
        return False
    
    message = """🤖 <b>GiddyUp Bot Connected!</b>

✅ Telegram integration is working!

You'll receive notifications for:
🏇 Morning picks
🎯 Bets placed
⏭️ Bets skipped
📊 Market analysis
🎉 Results

#GiddyUp #HorseRacing"""
    
    success = send_telegram_message(message)
    
    if success:
        print("✅ Telegram test message sent successfully!")
    else:
        print("❌ Failed to send Telegram message")
        print("   Check your bot token and chat ID")
    
    return success


if __name__ == "__main__":
    # Test the connection
    test_telegram_connection()

