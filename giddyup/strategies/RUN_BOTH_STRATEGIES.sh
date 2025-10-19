#!/bin/bash
#
# RUN BOTH STRATEGIES - Simplified Working Version
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

# Create logs directory
mkdir -p logs/daily_bets

# Output files
CSV_FILE="logs/daily_bets/betting_log_2025.csv"
TEMP_CSV="/tmp/bets_$TARGET_DATE.csv"

# Create header if file doesn't exist
if [ ! -f "$CSV_FILE" ]; then
    echo "date,time,course,horse,trainer,odds,strategy,reasoning,min_odds_needed,t60_actual_odds,action_taken,stake_gbp,result,pnl_gbp" > "$CSV_FILE"
fi

echo "Fetching selections..."
echo ""

# Export both strategies to temp CSV
docker exec horse_racing psql -U postgres -d horse_db -c "
-- STRATEGY A: HYBRID V3
WITH race_data AS (
    SELECT 
        r.race_id, r.race_date, r.off_time,
        TO_CHAR(r.off_time, 'HH24:MI') as race_time,
        c.course_name,
        h.horse_name, t.trainer_name,
        COALESCE(ru.win_ppwap, ru.dec) as decimal_odds,
        ROW_NUMBER() OVER (PARTITION BY r.race_id ORDER BY COALESCE(ru.win_ppwap, ru.dec)) as market_rank,
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
    AND overround <= 2.20
    AND disagreement >= 2.20
    AND edge_pp >= 0.06
    AND ev_adjusted >= 0.03
),
best_per_race AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY edge_pp DESC) as rank_in_race
    FROM filtered
),
strategy_a AS (
    SELECT 
        race_date::text, 
        race_time,
        course_name, 
        horse_name, 
        COALESCE(trainer_name, '') as trainer_name,
        ROUND(decimal_odds::numeric, 2) as odds,
        'A-Hybrid_V3' as strategy,
        'Rank ' || market_rank || '/' || field_size || ' | Disagree ' || ROUND(disagreement::numeric, 2) || 'x | Edge +' || ROUND((edge_pp*100)::numeric, 1) || 'pp' as reasoning,
        ROUND((decimal_odds * 0.95)::numeric, 2) as min_odds_needed,
        '' as t60_actual_odds,
        '' as action_taken,
        ROUND((0.015 * $UNIT_GBP)::numeric, 2) as stake_gbp,
        '' as result,
        '' as pnl_gbp
    FROM best_per_race
    WHERE rank_in_race = 1
),
-- STRATEGY B: PATH B
race_data_b AS (
    SELECT 
        r.race_id, r.race_date, r.off_time,
        TO_CHAR(r.off_time, 'HH24:MI') as race_time,
        c.course_name,
        h.horse_name, t.trainer_name,
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
    WHERE edge_pp >= edge_min_required * 0.85
    AND ev >= 0.015
    AND overround <= 2.20
),
best_per_race_b AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY edge_pp DESC) as rank_in_race
    FROM filtered_b
),
strategy_b AS (
    SELECT 
        race_date::text,
        race_time,
        course_name, 
        horse_name, 
        COALESCE(trainer_name, '') as trainer_name,
        ROUND(decimal_odds::numeric, 2) as odds,
        'B-Path_B' as strategy,
        'Edge +' || ROUND((edge_pp*100)::numeric, 1) || 'pp (need ' || ROUND((edge_min_required*0.85*100)::numeric, 0) || 'pp) | EV +' || ROUND((ev*100)::numeric, 1) || '%' as reasoning,
        ROUND((decimal_odds * 0.90)::numeric, 2) as min_odds_needed,
        '' as t60_actual_odds,
        '' as action_taken,
        ROUND((0.04 * $UNIT_GBP)::numeric, 2) as stake_gbp,
        '' as result,
        '' as pnl_gbp
    FROM best_per_race_b
    WHERE rank_in_race = 1
)
SELECT * FROM strategy_a
UNION ALL
SELECT * FROM strategy_b
ORDER BY race_time;
" -t -A -F',' > "$TEMP_CSV"

# Count bets
BET_COUNT=$(cat "$TEMP_CSV" | wc -l)

if [ "$BET_COUNT" -eq 0 ]; then
    echo "❌ NO BETS FOUND for $TARGET_DATE"
    echo ""
    echo "Possible reasons:"
    echo "  1. No runners meet strategy criteria"
    echo "  2. No odds data (check with CHECK_DATA_READY.sh)"
    echo "  3. All races filtered out by quality gates"
    echo ""
    exit 0
fi

# Display bets
echo "================================================================================"
echo "✅ FOUND $BET_COUNT BET(S)"
echo "================================================================================"
echo ""

# Pretty print
cat "$TEMP_CSV" | while IFS=',' read date time course horse trainer odds strat reasoning min t60 action stake result pnl; do
    echo "🏇 $time $course - $horse"
    echo "   Odds: $odds | Strategy: $strat"
    echo "   Why: $reasoning"
    echo "   Action at T-60: If odds >= $min → BET £$stake"
    echo ""
done

# Append to CSV
cat "$TEMP_CSV" >> "$CSV_FILE"

echo "================================================================================"
echo "✅ BETS SAVED TO CSV"
echo "================================================================================"
echo ""
echo "📄 File: $CSV_FILE"
echo "📊 Total bets today: $BET_COUNT"
echo ""

# Generate PNG betting card
echo "🎨 Generating betting card image..."
python3 ../generate_betting_card.py "$TARGET_DATE" 2>/dev/null
if [ $? -eq 0 ]; then
    echo ""
else
    echo "⚠️  Could not generate PNG (missing Pillow? pip3 install pillow)"
    echo ""
fi

echo "🎯 WORKFLOW:"
echo "   1. At T-60 for each race, check Betfair odds"
echo "   2. If odds >= min_odds_needed → PLACE BET"
echo "   3. If odds < min_odds_needed → SKIP"
echo "   4. After racing, fill in results and P&L"
echo ""

# Clean up
rm -f "$TEMP_CSV"

