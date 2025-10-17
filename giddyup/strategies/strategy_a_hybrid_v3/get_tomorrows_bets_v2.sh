#!/bin/bash
#
# Get Tomorrow's Bets - Enhanced with Bankroll & Database Logging
#
# Usage:
#   ./get_tomorrows_bets_v2.sh 2025-10-18 5000
#   ./get_tomorrows_bets_v2.sh [date] [bankroll_gbp]
#
# Arguments:
#   date: Target date (YYYY-MM-DD), defaults to tomorrow
#   bankroll: Your total bankroll in GBP (e.g., 5000)
#

# Parse arguments
if [ -z "$1" ]; then
    TARGET_DATE=$(date -d "tomorrow" +%Y-%m-%d)
else
    TARGET_DATE=$1
fi

if [ -z "$2" ]; then
    echo "Usage: $0 [date] <bankroll_gbp>"
    echo "Example: $0 2025-10-18 5000"
    echo ""
    echo "Please provide your bankroll amount in GBP"
    exit 1
fi

BANKROLL_GBP=$2

# Calculate unit size (1% of bankroll)
UNIT_GBP=$(echo "scale=2; $BANKROLL_GBP / 100" | bc)

echo "================================================================================"
echo "🏇 HYBRID MODEL V3 - Bet Selections for $TARGET_DATE"
echo "================================================================================"
echo ""
echo "💰 Bankroll: £$BANKROLL_GBP"
echo "📊 Unit Size: £$UNIT_GBP (1% of bankroll)"
echo ""

# Create output directory
mkdir -p logs/bets

# Output files
CSV_FILE="logs/bets/bets_${TARGET_DATE}.csv"
SQL_FILE="logs/bets/bets_${TARGET_DATE}.sql"

# Run the selection query and save to CSV
docker exec horse_racing psql -U postgres -d horse_db << EOF | tee /tmp/bet_output.txt

-- ============================================================================
-- HYBRID MODEL V3 SELECTION QUERY WITH BANKROLL
-- ============================================================================

-- Data availability check
SELECT 
    '📊 Data Availability' as status,
    COUNT(*) as total_runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) as have_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / NULLIF(COUNT(*), 0), 0) || '%' as pct_ready
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';

\\echo ''
\\echo '================================================================================'
\\echo ''

-- Main selection query with bankroll calculations
WITH race_data AS (
    SELECT 
        r.race_id,
        r.race_date,
        r.off_time,
        TO_CHAR(r.off_time, 'HH24:MI') as race_time,
        c.course_name,
        r.class,
        ROUND(r.dist_f::numeric, 1) as dist_f,
        r.going,
        r.ran as field_size,
        ru.horse_id,
        h.horse_name,
        t.trainer_name,
        j.jockey_name,
        ru.num as runner_num,
        ru.age,
        ru.lbs,
        COALESCE(ru.win_ppwap, ru.dec) as decimal_odds,
        RANK() OVER (PARTITION BY r.race_id ORDER BY COALESCE(ru.win_ppwap, ru.dec)) as market_rank,
        1.0 / NULLIF(COALESCE(ru.win_ppwap, ru.dec), 0) as q_market,
        SUM(1.0 / NULLIF(COALESCE(ru.win_ppwap, ru.dec), 0)) OVER (PARTITION BY r.race_id) as overround
    FROM racing.runners ru
    JOIN racing.races r ON r.race_id = ru.race_id
    LEFT JOIN racing.courses c ON c.course_id = r.course_id
    LEFT JOIN racing.horses h ON h.horse_id = ru.horse_id
    LEFT JOIN racing.trainers t ON t.trainer_id = ru.trainer_id
    LEFT JOIN racing.jockeys j ON j.jockey_id = ru.jockey_id
    WHERE r.race_date = '$TARGET_DATE'
    AND COALESCE(ru.win_ppwap, ru.dec) >= 1.01
),
with_calcs AS (
    SELECT 
        *,
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
    SELECT 
        *,
        p_model / NULLIF(q_vigfree, 0) as disagreement,
        p_model - q_vigfree as edge_pp,
        p_model * (decimal_odds - 1) * 0.98 - (1 - p_model) as ev_raw,
        CASE 
            WHEN market_rank <= 2 THEN (p_model * (decimal_odds - 1) * 0.98 - (1 - p_model)) * 0.3
            ELSE p_model * (decimal_odds - 1) * 0.98 - (1 - p_model)
        END as ev_adjusted
    FROM with_calcs
),
filtered AS (
    SELECT *
    FROM with_metrics
    WHERE decimal_odds BETWEEN 7.0 AND 12.0
    AND market_rank BETWEEN 3 AND 6
    AND overround <= 1.18
    AND disagreement >= 2.50
    AND edge_pp >= 0.08
    AND ev_adjusted >= 0.05
),
best_per_race AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY edge_pp DESC) as rank_in_race
    FROM filtered
),
with_stakes AS (
    SELECT 
        *,
        0.015 as stake_units,
        ROUND((0.015 * $UNIT_GBP)::numeric, 2) as stake_gbp
    FROM best_per_race
    WHERE rank_in_race = 1
)
SELECT 
    '🎯 BET #' || ROW_NUMBER() OVER (ORDER BY off_time) as bet_num,
    race_time as "Time",
    course_name as "Course",
    horse_name as "Horse",
    trainer_name as "Trainer",
    runner_num as "Draw",
    ROUND(decimal_odds::numeric, 2) as "Odds",
    market_rank as "Rank",
    ROUND((q_vigfree * 100)::numeric, 1) || '%' as "Market",
    ROUND((p_model * 100)::numeric, 1) || '%' as "Model",
    ROUND(disagreement::numeric, 2) || 'x' as "Disagree",
    ROUND((edge_pp * 100)::numeric, 1) || 'pp' as "Edge",
    '£' || stake_gbp as "Stake"
FROM with_stakes
ORDER BY off_time;

-- Export to CSV
\\echo ''
\\echo 'Exporting to CSV...'
\\copy (SELECT race_date, race_time, course_name, horse_name, trainer_name, runner_num, ROUND(decimal_odds::numeric, 2) as odds, market_rank, ROUND((q_vigfree * 100)::numeric, 1) as market_pct, ROUND((p_model * 100)::numeric, 1) as model_pct, ROUND(disagreement::numeric, 2) as disagree, ROUND((edge_pp * 100)::numeric, 1) as edge_pp, 0.015 as stake_units, ROUND((0.015 * $UNIT_GBP)::numeric, 2) as stake_gbp, '' as result, '' as pnl_gbp FROM with_stakes ORDER BY off_time) TO STDOUT WITH CSV HEADER

-- Summary
\\echo ''
\\echo '================================================================================'
SELECT 
    '📊 SUMMARY' as info,
    COUNT(*) as total_bets,
    ROUND(AVG(decimal_odds)::numeric, 2) as avg_odds,
    ROUND(AVG(market_rank)::numeric, 1) as avg_rank,
    ROUND(SUM(stake_units)::numeric, 3) as total_units,
    '£' || ROUND(SUM(stake_gbp)::numeric, 2) as total_stake_gbp
FROM with_stakes;

\\echo ''
\\echo 'Bankroll: £$BANKROLL_GBP | Unit: £$UNIT_GBP'
\\echo 'Expected Win Rate: ~11% | Expected ROI: +3.1%'
\\echo 'Paper Trading: LOG these bets, do NOT place real money yet'
\\echo ''
\\echo 'CSV saved to: $CSV_FILE'
\\echo ''

EOF

# Save CSV output
grep -A1000 "race_date,race_time" /tmp/bet_output.txt | grep -v "^--" | grep -v "^Exporting" | grep -v "^(" > "$CSV_FILE"

# Generate SQL insert statements for database logging
cat > "$SQL_FILE" << EOSQL
-- Insert into modeling.signals for tracking
-- Run this to log bets to database

INSERT INTO modeling.signals (
    as_of, race_id, horse_id, model_id,
    p_win, fair_odds_win, best_odds_win, best_odds_src,
    edge_win, stake_units, liquidity_ok, reasons
)
EOSQL

# Add INSERT statements from the query results
docker exec horse_racing psql -U postgres -d horse_db << EOFSQL >> "$SQL_FILE"
SELECT 
    'SELECT ' || race_id || ', ' || horse_id || ', 1, ' ||
    ROUND(p_model::numeric, 4) || ', ' ||
    ROUND((1.0/p_model)::numeric, 2) || ', ' ||
    ROUND(decimal_odds::numeric, 2) || ', ' ||
    '''T-60'', ' ||
    ROUND(edge_pp::numeric, 4) || ', ' ||
    '0.015, TRUE, ' ||
    '''{"disagreement":' || ROUND(disagreement::numeric, 2) || ',"rank":' || market_rank || '}''::jsonb);'
FROM (
    SELECT * FROM with_stakes ORDER BY off_time
) as inserts;
EOFSQL

echo ""
echo "================================================================================"
echo "✅ BETS LOGGED"
echo "================================================================================"
echo ""
echo "📄 CSV File: $CSV_FILE"
echo "    → Import into Excel/Google Sheets"
echo ""
echo "🗄️  SQL File: $SQL_FILE"
echo "    → Run to insert into modeling.signals table"
echo ""
echo "📊 Next Steps:"
echo "    1. Review bets above"
echo "    2. Open CSV in spreadsheet: open $CSV_FILE"
echo "    3. (Optional) Log to DB: psql < $SQL_FILE"
echo "    4. Evening: Update 'result' and 'pnl_gbp' columns in spreadsheet"
echo ""
echo "================================================================================"

