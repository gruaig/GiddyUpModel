#!/usr/bin/env python3
"""Quick Telegram integration test with example messages."""

from telegram_bot import *

print("\n" + "="*80)
print("🧪 TELEGRAM INTEGRATION TEST")
print("="*80 + "\n")

if not TELEGRAM_ENABLED:
    print("❌ Telegram not configured!")
    print("\nSteps:")
    print("1. Copy telegram_config.template.py to telegram_config.py")
    print("2. Add your bot token and chat ID")
    print("3. Run this test again")
    print("")
    exit(1)

print(f"✅ Configuration loaded")
print(f"   Token: {TELEGRAM_BOT_TOKEN[:20]}...")
print(f"   Chat ID: {TELEGRAM_CHAT_ID}")
print("")

# Test 1: Connection test
print("Test 1: Connection...")
if test_telegram_connection():
    print("✅ Connection test passed\n")
else:
    print("❌ Connection test failed\n")
    exit(1)

# Test 2: Morning picks
print("Test 2: Morning picks...")
test_selections = [
    {
        'time': '14:30',
        'course': 'Kempton',
        'horse': 'Test Horse 1',
        'odds': 10.0,
        'stake_gbp': 20.0,
        'min_odds_needed': 9.5,
        'strategy': 'A-Hybrid_V3'
    },
    {
        'time': '15:00',
        'course': 'Wolverhampton',
        'horse': 'Test Horse 2',
        'odds': 8.5,
        'stake_gbp': 15.0,
        'min_odds_needed': 7.65,
        'strategy': 'B-Path_B'
    }
]

if send_morning_picks("2025-10-18", test_selections):
    print("✅ Morning picks sent\n")
else:
    print("❌ Morning picks failed\n")

# Test 3: Bet placed
print("Test 3: Bet placed...")
if send_bet_placed(
    horse="Test Winner",
    course="Kempton",
    race_time="14:30",
    odds=12.0,
    stake=25.0,
    strategy="B-Path_B",
    expected_odds=11.5,
    is_dry_run=True
):
    print("✅ Bet placed notification sent\n")
else:
    print("❌ Bet placed notification failed\n")

# Test 4: Bet skipped
print("Test 4: Bet skipped...")
if send_bet_skipped(
    horse="Test Loser",
    course="Wolverhampton",
    race_time="15:00",
    current_odds=6.5,
    min_odds=7.0,
    expected_odds=8.0,
    reason="Odds too low: 6.5 < 7.0",
    strategy="A-Hybrid_V3"
):
    print("✅ Bet skipped notification sent\n")
else:
    print("❌ Bet skipped notification failed\n")

# Test 5: Result (Win)
print("Test 5: Result (Win)...")
if send_result(
    horse="Test Winner",
    course="Kempton",
    race_time="14:30",
    result="WIN",
    odds=12.0,
    stake=25.0,
    pnl=268.60,  # (12*25) - 25 - (12*25*0.02)
    strategy="B-Path_B"
):
    print("✅ Win result sent\n")
else:
    print("❌ Win result failed\n")

# Test 6: Result (Loss)
print("Test 6: Result (Loss)...")
if send_result(
    horse="Test Loser",
    course="Wolverhampton",
    race_time="15:00",
    result="LOSS",
    odds=8.5,
    stake=15.0,
    pnl=-15.0,
    strategy="A-Hybrid_V3"
):
    print("✅ Loss result sent\n")
else:
    print("❌ Loss result failed\n")

print("="*80)
print("✅ ALL TESTS COMPLETE")
print("="*80)
print("\nCheck your Telegram to see all test messages!")
print("")

