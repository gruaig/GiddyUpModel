#!/bin/bash
#
# Check Picks Results (Demo/Preview)
# ==================================
# Check hypothetical results for your daily picks
# (Use this before/instead of running the bot)
#
# Usage:
#   ./check_picks_results.sh [date]
#   ./check_picks_results.sh 2025-10-18

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
DATE=${1:-$(date +%Y-%m-%d)}

echo "================================================================================"
echo "📊 CHECKING PICKS RESULTS - $DATE"
echo "================================================================================"
echo ""
echo "ℹ️  This checks hypothetical results for your morning picks"
echo "   (even if you didn't actually place bets)"
echo ""

# Check betting log
BETTING_LOG="$SCRIPT_DIR/strategies/logs/daily_bets/betting_log_2025.csv"

if [[ ! -f "$BETTING_LOG" ]]; then
    echo "❌ No betting log found: $BETTING_LOG"
    exit 1
fi

# Count picks for today
PICK_COUNT=$(grep "^$DATE," "$BETTING_LOG" | wc -l)

if [ "$PICK_COUNT" -eq 0 ]; then
    echo "ℹ️  No picks found for $DATE"
    exit 0
fi

echo "📋 Found $PICK_COUNT pick(s) for $DATE"
echo ""

# Use Python to check results
python3 - "$DATE" << 'PYTHON_EOF'
import sys
import csv
import requests
from pathlib import Path

sys.path.insert(0, str(Path(".").absolute()))
from results_checker import fetch_results, check_horse_position, calculate_pnl, normalize_horse_name

date = sys.argv[1] if len(sys.argv) > 1 else "2025-10-18"
betting_log = Path(f"strategies/logs/daily_bets/betting_log_2025.csv")

# Fetch results
print("📡 Fetching results from Sporting Life API...")
race_results = fetch_results(date)
print(f"✅ Found {len(race_results)} race results\n")

# Read picks for this date
picks = []
with betting_log.open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['date'] == date:
            picks.append(row)

wins = 0
losses = 0
pending = 0
total_pnl = 0.0
total_staked = 0.0

print("=" * 80)
print(f"RESULTS FOR {date}")
print("=" * 80)
print("")

for pick in picks:
    horse = pick['horse']
    course = pick['course']
    race_time = pick['time']
    odds = float(pick['odds'])
    stake = float(pick['stake_gbp'])
    
    total_staked += stake
    
    # Check result
    result = check_horse_position(horse, course, race_time, race_results)
    
    if result:
        pnl = calculate_pnl(result, odds, stake)
        total_pnl += pnl
        
        if result == "WIN":
            wins += 1
            print(f"🎉 WIN: {horse} @ {course} ({race_time})")
            print(f"   Stake: £{stake:.2f} @ {odds:.2f} | P&L: £{pnl:+.2f}")
        else:
            losses += 1
            print(f"😔 LOSS: {horse} @ {course} ({race_time})")
            print(f"   Stake: £{stake:.2f} @ {odds:.2f} | P&L: £{pnl:.2f}")
        print("")
    else:
        pending += 1
        print(f"⏳ PENDING: {horse} @ {course} ({race_time})")
        print(f"   Result not available yet")
        print("")

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"  Total Picks: {len(picks)}")
print(f"  Wins: {wins}")
print(f"  Losses: {losses}")
print(f"  Pending: {pending}")
print(f"  Total Would-Be Staked: £{total_staked:.2f}")
print(f"  Hypothetical P&L: £{total_pnl:+.2f}")

if total_staked > 0:
    roi = (total_pnl / total_staked) * 100
    print(f"  Hypothetical ROI: {roi:+.1f}%")

if wins + losses > 0:
    win_rate = (wins / (wins + losses)) * 100
    print(f"  Win Rate: {win_rate:.1f}%")

print("")
print("💡 Note: These are hypothetical results for your picks.")
print("   Actual results depend on which bets were actually placed.")
print("")
PYTHON_EOF

echo "================================================================================"
echo ""

