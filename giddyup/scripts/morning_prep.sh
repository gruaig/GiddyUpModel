#!/bin/bash
#
# Morning Preparation Script
# Run this once each morning to:
#   1. Generate today's betting selections from database
#   2. Create PNG betting card
#   3. Prepare for automated betting
#
# Usage:
#   ./morning_prep.sh [date] [bankroll]
#   ./morning_prep.sh                    # Uses today and default bankroll
#   ./morning_prep.sh 2025-10-19 5000    # Specific date and bankroll

set -e

# Configuration
DEFAULT_BANKROLL=5000
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs/morning_prep"

# Parameters
TARGET_DATE=${1:-$(date +%Y-%m-%d)}
BANKROLL=${2:-$DEFAULT_BANKROLL}

# Create log directory
mkdir -p "$LOG_DIR"

# Log file
LOG_FILE="$LOG_DIR/morning_prep_$TARGET_DATE.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "================================================================================"
log "🌅 MORNING PREPARATION - $TARGET_DATE"
log "================================================================================"
log ""
log "💰 Bankroll: £$BANKROLL"
log ""

# Step 1: Check if database is ready
log "📊 Step 1: Checking if odds data is ready..."
ODDS_COUNT=$(docker exec horse_racing psql -U postgres -d horse_db -t -c "
SELECT COUNT(*) 
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE'
AND (win_ppwap IS NOT NULL OR dec IS NOT NULL);
" | tr -d ' ')

log "   Found $ODDS_COUNT runners with odds for $TARGET_DATE"

if [ "$ODDS_COUNT" -lt 100 ]; then
    log "⚠️  WARNING: Only $ODDS_COUNT runners have odds. Expected 400+."
    log "   Odds may still be loading. Consider waiting 30 minutes."
    log ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "❌ Aborted by user"
        exit 1
    fi
else
    log "✅ Odds data looks good ($ODDS_COUNT runners)"
fi

log ""

# Step 2: Generate selections
log "🎯 Step 2: Generating betting selections from database..."
cd "$SCRIPT_DIR/strategies"
./RUN_BOTH_STRATEGIES.sh "$TARGET_DATE" "$BANKROLL" 2>&1 | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
    log "❌ ERROR: Failed to generate selections"
    exit 1
fi

log ""

# Step 3: Generate PNG betting card
log "🎨 Step 3: Generating PNG betting card..."
cd "$SCRIPT_DIR"
python3 generate_betting_card.py "$TARGET_DATE" 2>&1 | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
    log "⚠️  WARNING: Failed to generate PNG (not critical)"
fi

log ""

# Step 4: Display summary
log "================================================================================"
log "✅ MORNING PREPARATION COMPLETE"
log "================================================================================"
log ""

# Count bets
BET_COUNT=$(tail -n +2 "$SCRIPT_DIR/strategies/logs/daily_bets/betting_log_2025.csv" | grep "^$TARGET_DATE," | wc -l)

log "📋 Summary:"
log "   Date: $TARGET_DATE"
log "   Bankroll: £$BANKROLL"
log "   Selections: $BET_COUNT bet(s)"
log ""

log "📁 Files Generated:"
log "   CSV: strategies/logs/daily_bets/betting_log_2025.csv"
log "   PNG: strategies/logs/daily_bets/betting_card_$TARGET_DATE.png"
log ""

log "🤖 Next Steps:"
log ""
log "   Option A - Manual monitoring:"
log "     python3 HorseBot.py --date $TARGET_DATE --bankroll $BANKROLL --dry-run --no-refresh"
log ""
log "   Option B - Start as service (automated all day):"
log "     sudo systemctl start giddyup-bot"
log ""
log "   (Service will use pre-generated selections, not re-query database)"
log ""

log "💡 Tip: Use --no-refresh flag to avoid re-querying database"
log "================================================================================"
log ""

