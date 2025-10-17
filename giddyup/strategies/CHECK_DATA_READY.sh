#!/bin/bash
#
# Check if database is ready for betting selections
# Run this before RUN_BOTH_STRATEGIES.sh
#

if [ -z "$1" ]; then
    TARGET_DATE=$(date -d "tomorrow" +%Y-%m-%d)
else
    TARGET_DATE=$1
fi

echo "================================================================================"
echo "📊 DATABASE READINESS CHECK - $TARGET_DATE"
echo "================================================================================"
echo ""

docker exec horse_racing psql -U postgres -d horse_db << EOF

SELECT '🔍 Checking data for $TARGET_DATE...' as status;

\\echo ''

-- Race count
SELECT 
    '📅 RACES:' as category,
    COUNT(*) as count,
    CASE WHEN COUNT(*) > 0 THEN '✅ Found' ELSE '❌ Missing' END as status
FROM racing.races
WHERE race_date = '$TARGET_DATE';

\\echo ''

-- Runner count
SELECT 
    '🏇 RUNNERS:' as category,
    COUNT(*) as count,
    CASE WHEN COUNT(*) > 0 THEN '✅ Found' ELSE '❌ Missing' END as status
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';

\\echo ''

-- Odds availability
SELECT 
    '💰 ODDS DATA:' as category,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) as have_odds,
    COUNT(*) as total_runners,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / NULLIF(COUNT(*), 0), 0) || '%' as pct_ready,
    CASE 
        WHEN COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) = COUNT(*) 
        THEN '✅ Ready'
        WHEN COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) > 0 
        THEN '⚠️  Partial'
        ELSE '❌ Missing'
    END as status
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';

\\echo ''
\\echo '================================================================================'

-- Sample races
SELECT 
    '📋 Sample races for $TARGET_DATE:' as info;

SELECT 
    TO_CHAR(r.off_time, 'HH24:MI') as time,
    c.course_name as course,
    r.class,
    COUNT(*) as runners,
    COUNT(*) FILTER (WHERE ru.win_ppwap IS NOT NULL) as with_odds
FROM racing.races r
LEFT JOIN racing.courses c ON c.course_id = r.course_id
JOIN racing.runners ru ON ru.race_id = r.race_id
WHERE r.race_date = '$TARGET_DATE'
GROUP BY r.off_time, c.course_name, r.class
ORDER BY r.off_time
LIMIT 10;

\\echo ''
\\echo '================================================================================'
\\echo 'VERDICT:'
\\echo ''

SELECT CASE 
    WHEN COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) = COUNT(*) 
    THEN '✅ READY - You can run ./RUN_BOTH_STRATEGIES.sh'
    WHEN COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) > 0 
    THEN '⚠️  PARTIAL - Some odds missing, selections may be limited'
    ELSE '❌ NOT READY - No odds data! Developer must populate win_ppwap column'
END as verdict
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';

\\echo ''

-- If not ready, show what's missing
SELECT CASE 
    WHEN COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) < COUNT(*)
    THEN '
📋 DEVELOPER ACTION REQUIRED:

1. Fetch Betfair Exchange prices for ' || COUNT(*) || ' runners
2. Update racing.runners.win_ppwap column
3. Source: Betfair Exchange API (win back prices)
4. Timing: ~60 minutes before race (or current if less time)
5. Must complete by 8 AM daily

See: CRITICAL_FOR_DEVELOPER.md for details
'
    ELSE '✅ All set! Odds data is populated.'
END as action_needed
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';

\\echo '================================================================================'

EOF

echo ""
echo "💡 TIP: Run this every morning before running betting selections"
echo "     to verify developer has populated odds data"
echo ""

