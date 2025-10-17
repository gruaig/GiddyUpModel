#!/bin/bash
#
# RUN BOTH STRATEGIES - Complete Daily Workflow
# Creates one unified spreadsheet with both strategies
#
# Usage:
#   ./RUN_BOTH_STRATEGIES.sh 2025-10-18 5000
#

if [ -z "$1" ]; then
    TARGET_DATE=$(date -d "tomorrow" +%Y-%m-%d)
else
    TARGET_DATE=$1
fi

if [ -z "$2" ]; then
    echo "Usage: $0 [date] <bankroll_gbp>"
    echo "Example: $0 2025-10-18 5000"
    exit 1
fi

BANKROLL_GBP=$2
UNIT_GBP=$(echo "scale=2; $BANKROLL_GBP / 100" | bc)

echo "================================================================================"
echo "🏇 DAILY BETTING SHEET - $TARGET_DATE"
echo "================================================================================"
echo ""
echo "💰 Bankroll: £$BANKROLL_GBP | Unit: £$UNIT_GBP (1%)"
echo ""
echo "Running BOTH strategies:"
echo "  Strategy A: Proven (+3.1% ROI, 3-4 bets/day)"
echo "  Strategy B: High ROI (+65% ROI, 0-2 bets/day)"
echo ""

# Create logs directory
mkdir -p logs/daily_bets

# Output file (append mode for ongoing tracking)
CSV_FILE="logs/daily_bets/betting_log_2025.csv"

# Create header if file doesn't exist
if [ ! -f "$CSV_FILE" ]; then
    echo "date,time,course,horse,trainer,odds,strategy,reasoning,min_odds_needed,t60_check,action_at_t60,stake_gbp,result,pnl_gbp" > "$CSV_FILE"
fi

echo "Fetching selections from database..."
echo ""

# Run combined query
docker exec horse_racing psql -U postgres -d horse_db << EOF | tee /tmp/both_strategies_output.txt

-- Data availability check
SELECT '📊 Data Check for $TARGET_DATE' as info;
SELECT 
    COUNT(*) as total_runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) as have_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / NULLIF(COUNT(*), 0), 0) || '% ready' as status
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';

\\echo ''
\\echo '================================================================================'
\\echo '🎯 STRATEGY A: HYBRID V3 (Proven, Rank-Based)'
\\echo '================================================================================'
\\echo ''

-- STRATEGY A selections
WITH race_data AS (
    SELECT 
        r.race_id, r.race_date, r.off_time,
        TO_CHAR(r.off_time, 'HH24:MI') as race_time,
        c.course_name, r.class,
        ru.horse_id, h.horse_name, t.trainer_name,
        ru.num as runner_num,
        COALESCE(ru.win_ppwap, ru.dec) as decimal_odds,
        RANK() OVER (PARTITION BY r.race_id ORDER BY COALESCE(ru.win_ppwap, ru.dec)) as market_rank,
        COUNT(*) OVER (PARTITION BY r.race_id) as field_size,
        1.0 / NULLIF(COALESCE(ru.win_ppwap, ru.dec), 0) as q_market,
        SUM(1.0 / NULLIF(COALESCE(ru.win_ppwap, ru.dec), 0)) OVER (PARTITION BY r.race_id) as overround
    FROM racing.runners ru
    JOIN racing.races r ON r.race_id = ru.race_id
    LEFT JOIN racing.courses c ON c.course_id = r.course_id
    LEFT JOIN racing.horses h ON h.horse_id = ru.horse_id
    LEFT JOIN racing.trainers t ON t.trainer_id = ru.trainer_id
    WHERE r.race_date = '$TARGET_DATE'
    AND COALESCE(ru.win_ppwap, ru.dec) >= 1.01
),
with_calcs AS (
    SELECT *, 
        q_market / NULLIF(overround, 0) as q_vigfree,
        CASE 
            WHEN market_rank = 3 THEN (q_market / overround) * 2.4
            WHEN market_rank = 4 THEN (q_market / overround) * 2.3
            WHEN market_rank = 5 THEN (q_market / overround) * 2.0
            WHEN market_rank = 6 THEN (q_market / overround) * 1.8
            ELSE (q_market / overround) * 1.1
        END as p_model
    FROM race_data
),
with_metrics AS (
    SELECT *,
        p_model / NULLIF(q_vigfree, 0) as disagreement,
        p_model - q_vigfree as edge_pp,
        CASE WHEN market_rank <= 2 THEN (p_model * (decimal_odds - 1) * 0.98 - (1 - p_model)) * 0.3
             ELSE p_model * (decimal_odds - 1) * 0.98 - (1 - p_model) END as ev_adjusted
    FROM with_calcs
),
filtered AS (
    SELECT * FROM with_metrics
    WHERE decimal_odds BETWEEN 7.0 AND 12.0
    AND market_rank BETWEEN 3 AND 6
    AND overround <= 1.18
    AND disagreement >= 2.50
    AND edge_pp >= 0.08
    AND ev_adjusted >= 0.05
),
best_per_race AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY edge_pp DESC) as rank_in_race
    FROM filtered
),
strategy_a AS (
    SELECT 
        race_date, race_time, course_name, horse_name, trainer_name,
        ROUND(decimal_odds::numeric, 2) as odds,
        'A-Hybrid_V3' as strategy,
        'Rank ' || market_rank || ' of ' || field_size || ' | Disagree ' || ROUND(disagreement::numeric, 2) || 'x | Edge +' || ROUND((edge_pp*100)::numeric, 1) || 'pp | EV +' || ROUND((ev_adjusted*100)::numeric, 1) || '%' as reasoning,
        ROUND((decimal_odds * 0.95)::numeric, 2) as min_odds_needed,
        'Check Betfair at ' || TO_CHAR(off_time - INTERVAL '60 minutes', 'HH24:MI') as t60_check,
        'If odds >= ' || ROUND((decimal_odds * 0.95)::numeric, 1) || ' → BET | If < ' || ROUND((decimal_odds * 0.95)::numeric, 1) || ' → SKIP' as action_at_t60,
        ROUND((0.015 * $UNIT_GBP)::numeric, 2) as stake_gbp
    FROM best_per_race
    WHERE rank_in_race = 1
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY race_time) as "#",
    race_time as "Time",
    course_name as "Course",
    horse_name as "Horse",
    odds as "Odds",
    reasoning as "Why Betting",
    action_at_t60 as "Action at T-60",
    '£' || stake_gbp as "Stake"
FROM strategy_a
ORDER BY race_time;

\\echo ''
\\echo '================================================================================'
\\echo '💎 STRATEGY B: PATH B (High ROI, Odds-Based)'
\\echo '================================================================================'
\\echo ''

-- STRATEGY B selections
WITH race_data_b AS (
    SELECT 
        r.race_id, r.race_date, r.off_time,
        TO_CHAR(r.off_time, 'HH24:MI') as race_time,
        c.course_name, r.class,
        ru.horse_id, h.horse_name, t.trainer_name,
        COALESCE(ru.win_ppwap, ru.dec) as decimal_odds,
        RANK() OVER (PARTITION BY r.race_id ORDER BY COALESCE(ru.win_ppwap, ru.dec)) as market_rank,
        1.0 / NULLIF(COALESCE(ru.win_ppwap, ru.dec), 0) as q_market,
        SUM(1.0 / NULLIF(COALESCE(ru.win_ppwap, ru.dec), 0)) OVER (PARTITION BY r.race_id) as overround
    FROM racing.runners ru
    JOIN racing.races r ON r.race_id = ru.race_id
    LEFT JOIN racing.courses c ON c.course_id = r.course_id
    LEFT JOIN racing.horses h ON h.horse_id = ru.horse_id
    LEFT JOIN racing.trainers t ON t.trainer_id = ru.trainer_id
    WHERE r.race_date = '$TARGET_DATE'
    AND COALESCE(ru.win_ppwap, ru.dec) BETWEEN 7.0 AND 16.0
),
with_calcs_b AS (
    SELECT *,
        q_market / NULLIF(overround, 0) as q_vigfree,
        CASE 
            WHEN market_rank = 3 THEN (q_market / overround) * 2.4
            WHEN market_rank = 4 THEN (q_market / overround) * 2.3
            WHEN market_rank = 5 THEN (q_market / overround) * 2.0
            WHEN market_rank = 6 THEN (q_market / overround) * 1.8
            ELSE (q_market / overround) * 1.1
        END as p_model,
        CASE 
            WHEN decimal_odds < 8.0 THEN 0.40
            WHEN decimal_odds < 12.0 THEN 0.15
            ELSE 0.50
        END as lambda,
        CASE 
            WHEN decimal_odds < 8.0 THEN 0.15
            WHEN decimal_odds < 12.0 THEN 0.15
            ELSE 0.16
        END as edge_min_required
    FROM race_data_b
),
with_blend_b AS (
    SELECT *,
        (1 - lambda) * p_model + lambda * q_vigfree as p_blend
    FROM with_calcs_b
),
with_metrics_b AS (
    SELECT *,
        p_blend - q_vigfree as edge_pp,
        p_blend * (decimal_odds - 1) * 0.98 - (1 - p_blend) as ev
    FROM with_blend_b
),
filtered_b AS (
    SELECT * FROM with_metrics_b
    WHERE edge_pp >= edge_min_required
    AND ev >= 0.02
    AND overround <= 1.18
),
best_per_race_b AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY edge_pp DESC) as rank_in_race
    FROM filtered_b
),
strategy_b AS (
    SELECT 
        race_date, race_time, course_name, horse_name, trainer_name,
        ROUND(decimal_odds::numeric, 2) as odds,
        'B-Path_B' as strategy,
        'Odds ' || ROUND(decimal_odds::numeric, 1) || ' (blend ' || ROUND((lambda*100)::numeric, 0) || '% mkt) | Edge +' || ROUND((edge_pp*100)::numeric, 1) || 'pp (need ' || ROUND((edge_min_required*100)::numeric, 0) || 'pp) | EV +' || ROUND((ev*100)::numeric, 1) || '%' as reasoning,
        ROUND((decimal_odds * 0.90)::numeric, 2) as min_odds_needed,
        'Check Betfair at ' || TO_CHAR(off_time - INTERVAL '60 minutes', 'HH24:MI') as t60_check,
        'If odds >= ' || ROUND((decimal_odds * 0.90)::numeric, 1) || ' → BET | If < ' || ROUND((decimal_odds * 0.90)::numeric, 1) || ' → SKIP' as action_at_t60,
        ROUND((0.04 * $UNIT_GBP)::numeric, 2) as stake_gbp
    FROM best_per_race_b
    WHERE rank_in_race = 1
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY race_time) as "#",
    race_time as "Time",
    course_name as "Course",
    horse_name as "Horse",
    odds as "Odds",
    reasoning as "Why Betting",
    action_at_t60 as "Action at T-60",
    '£' || stake_gbp as "Stake"
FROM strategy_b
ORDER BY race_time;

\\echo ''
\\echo '================================================================================'
\\echo '📊 COMBINED SUMMARY'
\\echo '================================================================================'
\\echo ''

-- Combined summary
WITH all_bets AS (
    SELECT * FROM strategy_a
    UNION ALL
    SELECT * FROM strategy_b
)
SELECT 
    strategy as "Strategy",
    COUNT(*) as "Bets",
    ROUND(AVG(odds)::numeric, 1) as "Avg Odds",
    '£' || ROUND(SUM(stake_gbp)::numeric, 2) as "Total Stake"
FROM all_bets
GROUP BY strategy
UNION ALL
SELECT 
    'TOTAL' as strategy,
    COUNT(*),
    ROUND(AVG(odds)::numeric, 1),
    '£' || ROUND(SUM(stake_gbp)::numeric, 2)
FROM all_bets;

\\echo ''
\\echo 'Exporting to CSV...'

-- Export to CSV (append mode)
\\copy (SELECT race_date, race_time, course_name, horse_name, trainer_name, odds, strategy, reasoning, min_odds_needed, '', '', stake_gbp, '', '' FROM (SELECT * FROM strategy_a UNION ALL SELECT * FROM strategy_b) combined ORDER BY race_time) TO STDOUT WITH CSV

EOF

# Append to CSV (not overwrite)
grep -v "^Exporting\|^Data Check\|^(" /tmp/both_strategies_output.txt | \
    grep "^2025" | \
    sed 's/"//g' >> "$CSV_FILE"

echo ""
echo "================================================================================"
echo "✅ DAILY BETTING SHEET READY"
echo "================================================================================"
echo ""
echo "📄 CSV File: $CSV_FILE"
echo "   → Import to Excel/Google Sheets"
echo ""
echo "📋 Columns in spreadsheet:"
echo "   1. date             - Race date"
echo "   2. time             - Race time"
echo "   3. course           - Course name"
echo "   4. horse            - Horse name"
echo "   5. trainer          - Trainer name"
echo "   6. odds             - Current odds (8am snapshot)"
echo "   7. strategy         - A-Hybrid_V3 or B-Path_B"
echo "   8. reasoning        - WHY this bet (disagreement, edge, etc.)"
echo "   9. min_odds_needed  - Minimum odds required at T-60"
echo "   10. t60_actual_odds - YOU FILL THIS: What odds showed at T-60"
echo "   11. action_taken    - YOU FILL THIS: BET or SKIP"
echo "   12. stake_gbp       - Stake amount if bet placed"
echo "   13. result          - YOU FILL THIS: WON or LOST"
echo "   14. pnl_gbp         - YOU FILL THIS: Calculate profit/loss"
echo ""
echo "🎯 YOUR WORKFLOW TODAY:"
echo ""
echo "MORNING (Now - 8am):"
echo "  ✅ Review bets above"
echo "  ✅ Note T-60 times for each race"
echo "  ✅ Set phone alerts"
echo ""
echo "AT T-60 FOR EACH RACE:"
echo "  1. Open Betfair, find the race"
echo "  2. Check current odds for the horse"
echo "  3. Fill in spreadsheet column: 't60_actual_odds'"
echo "  4. Compare to 'min_odds_needed':"
echo "     - If actual >= minimum → PLACE BET, write 'BET' in 'action_taken'"
echo "     - If actual < minimum → SKIP, write 'SKIP' in 'action_taken'"
echo "  5. If BET: Place bet on Betfair for the stake amount shown"
echo ""
echo "EVENING (After racing):"
echo "  1. Check which horses won"
echo "  2. Fill in 'result' column (WON or LOST)"
echo "  3. Calculate 'pnl_gbp':"
echo "     - If WON: stake × (odds - 1) × 0.98"
echo "     - If LOST: -stake"
echo "     - If SKIP: leave blank"
echo ""
echo "⚠️  BOTH STRATEGIES USE T-60 TIMING:"
echo "   Strategy A: T-60 (60 min before off)"
echo "   Strategy B: T-60 (60 min before off)"
echo "   SAME timing, just different selection criteria!"
echo ""
echo "================================================================================"
echo ""

# Create today's quick reference file
cat > "logs/daily_bets/quick_ref_${TARGET_DATE}.txt" << REFEOF
QUICK REFERENCE - $TARGET_DATE
═══════════════════════════════════════════════════════════════════════════════

AT T-60 FOR EACH BET:
1. Open Betfair
2. Find the race
3. Check horse's current odds
4. Fill spreadsheet: 't60_actual_odds' column
5. If odds >= min_odds_needed → BET ✅
6. If odds < min_odds_needed → SKIP ❌

EVENING:
1. Check results
2. Fill 'result' column (WON/LOST)
3. Calculate P&L:
   WON: stake × (odds - 1) × 0.98
   LOST: -stake
   SKIP: blank

═══════════════════════════════════════════════════════════════════════════════
REFEOF

echo "📌 Quick reference saved: logs/daily_bets/quick_ref_${TARGET_DATE}.txt"
echo ""
echo "🎯 Open spreadsheet: open $CSV_FILE"
echo ""

