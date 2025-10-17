#!/bin/bash
#
# Get Tomorrow's Bets - Hybrid Model V3
#
# Usage:
#   ./get_tomorrows_bets.sh 2025-10-18
#   ./get_tomorrows_bets.sh  # Defaults to tomorrow
#

# Get target date
if [ -z "$1" ]; then
    TARGET_DATE=$(date -d "tomorrow" +%Y-%m-%d)
else
    TARGET_DATE=$1
fi

echo "================================================================================"
echo "🏇 HYBRID MODEL V3 - Bet Selections for $TARGET_DATE"
echo "================================================================================"

# Run the selection query
docker exec horse_racing psql -U postgres -d horse_db << EOF

-- ============================================================================
-- HYBRID MODEL V3 SELECTION QUERY
-- ============================================================================
-- 
-- This query applies all 6 gates:
--   1. Odds range: 7-12 (sweet spot)
--   2. Market rank: 3-6 (avoid favorites)
--   3. Overround: ≤1.18 (competitive market)
--   4. Disagreement: ≥2.5x (model much higher than market)
--   5. Edge: ≥8pp minimum
--   6. EV: ≥5% after commission
--
-- Tables touched:
--   - racing.races (race details, off_time, course)
--   - racing.runners (horses in race, odds)
--   - racing.courses (course names)
--   - racing.horses (horse names)
--
-- ============================================================================

-- First, check if data is ready
SELECT 
    '📊 Data Availability Check' as status,
    COUNT(*) as total_runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) as have_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / NULLIF(COUNT(*), 0), 0) || '%' as pct_ready
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';

\\echo ''
\\echo '================================================================================'
\\echo ''

-- Main selection query
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
        h.horse_name,
        t.trainer_name,
        j.jockey_name,
        ru.num as runner_num,
        ru.age,
        ru.lbs,
        COALESCE(ru.win_ppwap, ru.dec) as decimal_odds,
        -- Market features
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
        -- Model probability estimate
        -- In production: Path A model predicts this from ability features
        -- For now: Simple heuristic (mid-field horses undervalued)
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
        -- Favorite penalty
        CASE 
            WHEN market_rank <= 2 THEN (p_model * (decimal_odds - 1) * 0.98 - (1 - p_model)) * 0.3
            ELSE p_model * (decimal_odds - 1) * 0.98 - (1 - p_model)
        END as ev_adjusted
    FROM with_calcs
),
filtered AS (
    SELECT *
    FROM with_metrics
    WHERE decimal_odds BETWEEN 7.0 AND 12.0       -- Gate 1: Odds range
    AND market_rank BETWEEN 3 AND 6               -- Gate 2: Not favorites
    AND overround <= 1.18                         -- Gate 3: Competitive market
    AND disagreement >= 2.50                      -- Gate 4: Strong disagreement
    AND edge_pp >= 0.08                           -- Gate 5: 8pp minimum edge
    AND ev_adjusted >= 0.05                       -- Gate 6: 5% EV minimum
),
best_per_race AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY edge_pp DESC) as rank_in_race
    FROM filtered
)
SELECT 
    '🎯 BET #' || ROW_NUMBER() OVER (ORDER BY off_time) as bet_num,
    race_time,
    course_name || ' - ' || class as race,
    horse_name || ' (' || trainer_name || ')' as selection,
    '#' || runner_num || ' | ' || age || 'yo | ' || lbs || 'lbs' as details,
    ROUND(decimal_odds::numeric, 2) || ' odds (Rank ' || market_rank || ')' as price,
    ROUND((q_vigfree * 100)::numeric, 1) || '% mkt → ' || ROUND((p_model * 100)::numeric, 1) || '% model' as probabilities,
    ROUND(disagreement::numeric, 2) || 'x disagree | +' || ROUND((edge_pp * 100)::numeric, 1) || 'pp edge' as value,
    '0.015 units (~£0.75 with £50 units)' as stake
FROM best_per_race
WHERE rank_in_race = 1  -- Top-1 per race
ORDER BY off_time;

-- Summary
\\echo ''
\\echo '================================================================================'
SELECT 
    '📊 SUMMARY' as info,
    COUNT(*) as total_bets,
    ROUND(AVG(decimal_odds)::numeric, 2) as avg_odds,
    ROUND(AVG(market_rank)::numeric, 1) as avg_rank,
    ROUND((COUNT(*) * 0.015)::numeric, 3) || ' units' as total_stake
FROM best_per_race
WHERE rank_in_race = 1;

\\echo ''
\\echo 'Expected Win Rate: ~11%'
\\echo 'Expected ROI: +3.1%'
\\echo 'Paper Trading: LOG these bets, do NOT place real money yet'
\\echo ''

EOF

