#!/bin/bash
#
# Grade Day Script
# ================
# Automatically fetch race results and generate complete report
#
# Usage:
#   ./grade_day.sh [date]
#   ./grade_day.sh 2025-10-18

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
DATE=${1:-$(date +%Y-%m-%d)}

echo "================================================================================"
echo "📊 GRADING DAY - $DATE"
echo "================================================================================"
echo ""

# Check if actions file exists
ACTIONS_CSV="$SCRIPT_DIR/strategies/logs/automated_bets/bot_actions_$DATE.csv"

if [[ ! -f "$ACTIONS_CSV" ]]; then
    echo "❌ No bot actions file found for $DATE"
    echo "   Expected: $ACTIONS_CSV"
    echo ""
    echo "Did you run the bot on $DATE?"
    exit 1
fi

# Count bets
BET_COUNT=$(grep -E "DRY_RUN|EXECUTED" "$ACTIONS_CSV" 2>/dev/null | wc -l | tr -d ' \n' || echo "0")

if [ "$BET_COUNT" -eq 0 ] 2>/dev/null; then
    echo "ℹ️  No bets were placed on $DATE"
    echo "   Nothing to grade."
    exit 0
fi

echo "📋 Found $BET_COUNT bet(s) to check"
echo ""

# Step 1: Fetch results from API
echo "================================================================================"
echo "STEP 1: Fetch Results from Sporting Life API"
echo "================================================================================"
echo ""

python3 "$SCRIPT_DIR/results_checker.py" "$DATE"

if [ $? -ne 0 ]; then
    echo "⚠️  Could not fetch all results (some races may not be finished yet)"
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted"
        exit 1
    fi
fi

echo ""

# Step 2: Generate Excel Report
echo "================================================================================"
echo "STEP 2: Generate Excel Report"
echo "================================================================================"
echo ""

REPORT_FILE="$SCRIPT_DIR/strategies/logs/automated_bets/betting_report_$DATE.xlsx"

if [[ -f "$REPORT_FILE" ]]; then
    echo "⚠️  Report already exists: $REPORT_FILE"
    read -p "   Regenerate? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Using existing report..."
    else
        echo "   Regenerating report..."
        python3 "$SCRIPT_DIR/generate_betting_report.py" "$DATE"
    fi
else
    echo "📊 Generating Excel report with results..."
    python3 "$SCRIPT_DIR/generate_betting_report.py" "$DATE"
fi

echo ""

# Step 3: Generate Result Tweets
echo "================================================================================"
echo "STEP 3: Generate Result Tweets & Media"
echo "================================================================================"
echo ""

echo "🐦 Generating tweet files..."
python3 "$SCRIPT_DIR/generate_result_tweets.py" "$DATE"

echo ""

# Step 4: Send to Communication Channels
echo "================================================================================"
echo "STEP 4: Send Results to Communication Channels"
echo "================================================================================"
echo ""

# Telegram
if python3 -c "from telegram_bot import TELEGRAM_ENABLED; exit(0 if TELEGRAM_ENABLED else 1)" 2>/dev/null; then
    echo "📱 Telegram is configured"
    read -p "   Send results to Telegram? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Results were already sent during results_checker.py
        echo "   ✅ Results notifications sent via results_checker"
        
        # Send daily summary
        python3 << 'EOF'
import sys
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from telegram_bot import send_daily_summary

date = sys.argv[1]
actions_csv = Path(f"strategies/logs/automated_bets/bot_actions_{date}.csv")

wins = 0
losses = 0
total_pnl = 0
total_staked = 0
total_bets = 0

with actions_csv.open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("bet_placed") in ["DRY_RUN", "EXECUTED"]:
            total_bets += 1
            total_staked += float(row.get("stake", 0))
            
            result = row.get("result", "").strip().upper()
            if result == "WIN":
                wins += 1
                total_pnl += float(row.get("pnl_gbp", 0))
            elif result == "LOSS":
                losses += 1
                total_pnl += float(row.get("pnl_gbp", 0))

send_daily_summary(date, total_bets, total_staked, wins, losses, total_pnl)
print(f"   ✅ Daily summary sent to Telegram")
EOF
        "$DATE"
    fi
else
    echo "ℹ️  Telegram not configured (optional)"
fi

echo ""

# Final Summary
echo "================================================================================"
echo "✅ GRADING COMPLETE FOR $DATE"
echo "================================================================================"
echo ""

# Calculate final stats
python3 << 'EOF'
import sys
import csv
from pathlib import Path

date = sys.argv[1]
actions_csv = Path(f"strategies/logs/automated_bets/bot_actions_{date}.csv")

total_bets = 0
wins = 0
losses = 0
pending = 0
total_pnl = 0
total_staked = 0

with actions_csv.open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("bet_placed") in ["DRY_RUN", "EXECUTED"]:
            total_bets += 1
            stake = float(row.get("stake", 0))
            total_staked += stake
            
            result = row.get("result", "").strip().upper()
            if result == "WIN":
                wins += 1
                pnl = float(row.get("pnl_gbp", 0))
                total_pnl += pnl
            elif result == "LOSS":
                losses += 1
                pnl = float(row.get("pnl_gbp", 0))
                total_pnl += pnl
            else:
                pending += 1

print(f"📊 Final Summary:")
print(f"   Total Bets: {total_bets}")
print(f"   Wins: {wins} | Losses: {losses} | Pending: {pending}")
print(f"   Total Staked: £{total_staked:.2f}")
print(f"   Total P&L: £{total_pnl:+.2f}")

if total_staked > 0:
    roi = (total_pnl / total_staked) * 100
    print(f"   ROI: {roi:+.1f}%")

if wins + losses > 0:
    win_rate = (wins / (wins + losses)) * 100
    print(f"   Win Rate: {win_rate:.1f}%")
EOF
"$DATE"

echo ""
echo "📁 Files generated:"
echo "   Excel Report: strategies/logs/automated_bets/betting_report_$DATE.xlsx"
echo "   Result Tweets: strategies/logs/tweets/*_result.tweet"
echo "   Updated CSV: strategies/logs/automated_bets/bot_actions_$DATE.csv"
echo ""
echo "🎯 Next steps:"
echo "   - Review Excel report: Open betting_report_$DATE.xlsx"
echo "   - Post result tweets: ./tweet_manager.sh list"
echo "   - Share on social media!"
echo ""
echo "================================================================================"
echo ""

