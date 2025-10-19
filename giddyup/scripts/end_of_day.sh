#!/bin/bash
#
# End of Day Workflow
# ===================
# Complete workflow after racing day finishes:
#   1. Automatically fetch results from Sporting Life API
#   2. Generate Excel report (with results pre-filled)
#   3. Generate result tweets
#   4. Send results to Telegram/Twitch
#   5. Optionally post to social media
#
# Usage:
#   ./end_of_day.sh [date]
#   ./end_of_day.sh 2025-10-18
#
# NEW: Now uses grade_day.sh for automatic result fetching!

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATE=${1:-$(date +%Y-%m-%d)}

echo "================================================================================"
echo "📊 END OF DAY WORKFLOW - $DATE"
echo "================================================================================"
echo ""
echo "🆕 Now using automatic result fetching from Sporting Life API!"
echo ""

# Call grade_day.sh which does everything
"$SCRIPT_DIR/grade_day.sh" "$DATE"

# Check if actions file exists
if [[ ! -f "$ACTIONS_CSV" ]]; then
    echo "❌ No bot actions file found for $DATE"
    echo "   Expected: $ACTIONS_CSV"
    echo ""
    echo "Did you run the bot today?"
    exit 1
fi

# Count bets placed
BET_COUNT=$(grep -c "DRY_RUN\|EXECUTED" "$ACTIONS_CSV" || echo "0")

if [ "$BET_COUNT" -eq 0 ]; then
    echo "ℹ️  No bets were placed on $DATE"
    echo "   Nothing to process."
    exit 0
fi

echo "📋 Found $BET_COUNT bet(s) placed on $DATE"
echo ""

# Step 1: Generate Excel Report
echo "================================================================================"
echo "STEP 1: Generate Excel Report"
echo "================================================================================"
echo ""

if [[ -f "$REPORT_FILE" ]]; then
    echo "⚠️  Report already exists: $REPORT_FILE"
    read -p "   Regenerate? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Skipping report generation..."
    else
        echo "   Regenerating report..."
        python3 "$SCRIPT_DIR/generate_betting_report.py" "$DATE"
    fi
else
    echo "📊 Generating Excel report..."
    python3 "$SCRIPT_DIR/generate_betting_report.py" "$DATE"
fi

echo ""

# Step 2: Fill in Results
echo "================================================================================"
echo "STEP 2: Fill in Results"
echo "================================================================================"
echo ""
echo "📝 Please open the Excel file and fill in the 'Result' column:"
echo "   File: $REPORT_FILE"
echo ""
echo "   For each bet:"
echo "   - Column L (Result): Enter 'WIN' or 'LOSS'"
echo "   - Column M (Missed Winner): Enter 'YES' if it would have won but you didn't bet"
echo "   - P&L will auto-calculate"
echo ""
echo "💡 Tip: Use Excel or LibreOffice Calc"
echo ""

# Wait for user confirmation
read -p "Press ENTER when you've filled in all results..."
echo ""

# Step 3: Generate Result Tweets
echo "================================================================================"
echo "STEP 3: Generate Result Tweets"
echo "================================================================================"
echo ""

echo "🐦 Generating tweet files for results..."
python3 "$SCRIPT_DIR/generate_result_tweets.py" "$DATE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tweet files generated in: strategies/logs/tweets/"
    echo ""
    
    # List result tweets
    RESULT_TWEETS=$(ls "$SCRIPT_DIR/strategies/logs/tweets/"*_result.tweet 2>/dev/null | wc -l)
    if [ "$RESULT_TWEETS" -gt 0 ]; then
        echo "📁 Result tweet files:"
        ls -1 "$SCRIPT_DIR/strategies/logs/tweets/"*_result.tweet | xargs -n1 basename
    fi
else
    echo "⚠️  Could not generate result tweets"
    echo "   Check that results are filled in the CSV"
fi

echo ""

# Step 4: Send to Telegram
echo "================================================================================"
echo "STEP 4: Send Results to Telegram"
echo "================================================================================"
echo ""

# Check if Telegram is configured
if python3 -c "from telegram_bot import TELEGRAM_ENABLED; exit(0 if TELEGRAM_ENABLED else 1)" 2>/dev/null; then
    echo "📱 Telegram is configured"
    read -p "   Send results to Telegram? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Sending results to Telegram..."
        
        # Send individual results
        python3 << 'EOF'
import sys
import csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from telegram_bot import send_result, send_daily_summary

date = sys.argv[1]
actions_csv = Path(f"strategies/logs/automated_bets/bot_actions_{date}.csv")

results_sent = 0
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
            if result in ["WIN", "LOSS"]:
                # Calculate P&L
                odds = float(row.get("actual_odds", 0))
                stake = float(row.get("stake", 0))
                
                if result == "WIN":
                    pnl = (odds * stake) - stake - (odds * stake * 0.02)
                    wins += 1
                else:
                    pnl = -stake
                    losses += 1
                
                total_pnl += pnl
                
                # Send result
                send_result(
                    horse=row["horse"],
                    course=row["course"],
                    race_time=row["race_time"],
                    result=result,
                    odds=odds,
                    stake=stake,
                    pnl=pnl,
                    strategy=row["strategy"]
                )
                results_sent += 1

# Send daily summary
if results_sent > 0:
    send_daily_summary(date, total_bets, total_staked, wins, losses, total_pnl)

print(f"\n✅ Sent {results_sent} result(s) to Telegram")
print(f"   Wins: {wins} | Losses: {losses} | P&L: £{total_pnl:.2f}")
EOF
        "$DATE"
    else
        echo "   Skipped Telegram notifications"
    fi
else
    echo "ℹ️  Telegram not configured (optional)"
    echo "   See TELEGRAM_QUICKSTART.md to set up"
fi

echo ""

# Step 5: Post to Social Media
echo "================================================================================"
echo "STEP 5: Post to Social Media (Optional)"
echo "================================================================================"
echo ""

echo "📱 Tweet files are ready in: strategies/logs/tweets/"
echo ""
echo "To post manually:"
echo "   1. ./tweet_manager.sh list"
echo "   2. ./tweet_manager.sh post <filename>"
echo ""

read -p "View tweet files now? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📋 Available tweet files:"
    ./tweet_manager.sh list
fi

echo ""

# Final Summary
echo "================================================================================"
echo "✅ END OF DAY WORKFLOW COMPLETE"
echo "================================================================================"
echo ""

# Parse final stats from CSV
python3 << 'EOF'
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
                odds = float(row.get("actual_odds", 0))
                pnl = (odds * stake) - stake - (odds * stake * 0.02)
                total_pnl += pnl
                wins += 1
            elif result == "LOSS":
                total_pnl -= stake
                losses += 1
            else:
                pending += 1

print(f"📊 Summary for {date}:")
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
echo "   Excel Report: $REPORT_FILE"
echo "   Tweet Files: strategies/logs/tweets/*_result.tweet"
echo "   CSV Log: $ACTIONS_CSV"
echo ""
echo "🎯 Next steps:"
echo "   - Review Excel report for detailed analysis"
echo "   - Post tweet files manually if desired"
echo "   - Archive old files if needed"
echo ""
echo "================================================================================"
echo ""

