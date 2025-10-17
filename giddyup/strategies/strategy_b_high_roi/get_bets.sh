#!/bin/bash
#
# Strategy B: Path B Daily Selections
# High ROI (65%+), Lower Volume (1 bet/day avg)
#
# Usage:
#   ./get_bets.sh 2025-10-18 5000
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
echo "🏇 STRATEGY B: PATH B (High ROI) - Selections for $TARGET_DATE"
echo "================================================================================"
echo ""
echo "💰 Bankroll: £$BANKROLL_GBP | Unit: £$UNIT_GBP"
echo "📊 Expected: 0-2 bets (many days zero - very selective!)"
echo ""

# Run selection query with Strategy B logic
docker exec horse_racing psql -U postgres -d horse_db << EOF

-- Data check
SELECT '📊 Data Availability:' as info;
SELECT 
    COUNT(*) as runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) as have_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) / COUNT(*), 0) || '%' as ready
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';

\\echo ''
\\echo '================================================================================'
\\echo 'STRATEGY B SELECTIONS (Banded Thresholds, High Edge Required)'
\\echo '================================================================================'
\\echo ''

-- Main selection with Path B logic
WITH race_data AS (
    SELECT 
        r.race_id, r.race_date, r.off_time,
        TO_CHAR(r.off_time, 'HH24:MI') as race_time,
        c.course_name, r.class,
        ru.horse_id, h.horse_name, t.trainer_name,
        ru.num as runner_num, ru.age, ru.lbs,
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
with_blending AS (
    SELECT *,
        CASE 
            WHEN decimal_odds < 8.0 THEN 0.40   -- 5-8: 40% market
            WHEN decimal_odds < 12.0 THEN 0.15  -- 8-12: 15% market (trust model!)
            ELSE 0.50                            -- 12+: 50% market (hedge)
        END as lambda,
        CASE 
            WHEN decimal_odds < 8.0 THEN 0.15   -- 5-8: 15pp min
            WHEN decimal_odds < 12.0 THEN 0.15  -- 8-12: 15pp min
            ELSE 0.16                            -- 12+: 16pp min
        END as edge_min_required
    FROM with_calcs
),
with_blend_prob AS (
    SELECT *,
        (1 - lambda) * p_model + lambda * q_vigfree as p_blend
    FROM with_blending
),
with_metrics AS (
    SELECT *,
        p_blend - q_vigfree as edge_pp,
        p_blend * (decimal_odds - 1) * 0.98 - (1 - p_blend) as ev
    FROM with_blend_prob
),
filtered AS (
    SELECT * FROM with_metrics
    WHERE edge_pp >= edge_min_required
    AND ev >= 0.02
    AND overround <= 1.18
),
best_per_race AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY edge_pp DESC) as rank_in_race
    FROM filtered
),
with_stakes AS (
    SELECT *,
        0.04 as stake_units,
        ROUND((0.04 * $UNIT_GBP)::numeric, 2) as stake_gbp
    FROM best_per_race
    WHERE rank_in_race = 1
)
SELECT 
    '🎯 STRATEGY B BET #' || ROW_NUMBER() OVER (ORDER BY off_time) as bet_num,
    race_time as "Time",
    course_name as "Course",
    horse_name as "Horse",
    ROUND(decimal_odds::numeric, 2) as "Odds",
    market_rank as "Rank",
    '' as "---",
    ROUND((q_vigfree * 100)::numeric, 1) || '%' as "Mkt%",
    ROUND((p_model * 100)::numeric, 1) || '%' as "Model%",
    ROUND((p_blend * 100)::numeric, 1) || '%' as "Blend%",
    '' as "----",
    '+' || ROUND((edge_pp * 100)::numeric, 1) || 'pp' as "Edge",
    '+' || ROUND((ev * 100)::numeric, 1) || '%' as "EV",
    '' as "-----",
    '£' || stake_gbp as "Stake"
FROM with_stakes
ORDER BY off_time;

\\echo ''
\\echo '================================================================================'

-- Summary
SELECT 
    '📊 SUMMARY' as info,
    COUNT(*) as bets,
    ROUND(AVG(decimal_odds)::numeric, 1) as avg_odds,
    '+' || ROUND(AVG(edge_pp * 100)::numeric, 0) || 'pp' as avg_edge,
    '£' || ROUND(SUM(stake_gbp)::numeric, 2) as total_stake
FROM with_stakes;

\\echo ''
\\echo '💡 Strategy B: High selectivity = High ROI'
\\echo '⚠️  PAPER TRADE ONLY - Not validated yet!'
\\echo '📈 Backtest: 634 bets @ +65% ROI (needs real-world confirmation)'
\\echo ''
\\echo 'Expected: 0-2 bets (many days will show ZERO bets - this is normal!)'
\\echo 'When bets found: Average £2-4 stake, 15-18pp edge'
\\echo ''

EOF

echo ""
echo "================================================================================"
echo "✅ Strategy B Selections Complete"
echo "================================================================================"
echo ""
echo "Note: Strategy B is VERY selective!"
echo "  - Many days will have 0 bets (this is normal)"
echo "  - When bets found, they have high edge (15-18pp)"
echo "  - Focus on quality over quantity"
echo ""
echo "⚠️  IMPORTANT: Paper trade Nov-Dec before using real money!"
echo "    Must validate +20% ROI in real-world first"
echo ""

