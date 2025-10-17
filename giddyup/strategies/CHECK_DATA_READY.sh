#!/bin/bash
#
# Check if database is ready for betting selections
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

# Check races
echo "📅 RACES:"
docker exec horse_racing psql -U postgres -d horse_db -t -c "
SELECT COUNT(*) || ' races found' FROM racing.races WHERE race_date = '$TARGET_DATE';
"

# Check runners
echo ""
echo "🏇 RUNNERS:"
docker exec horse_racing psql -U postgres -d horse_db -t -c "
SELECT COUNT(*) || ' runners found' 
FROM racing.runners ru 
JOIN racing.races r USING (race_id) 
WHERE r.race_date = '$TARGET_DATE';
"

# Check odds
echo ""
echo "💰 ODDS DATA:"
docker exec horse_racing psql -U postgres -d horse_db -t -c "
SELECT 
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) || ' of ' || COUNT(*) || ' runners have odds (' ||
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / NULLIF(COUNT(*), 0), 0) || '% ready)'
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';
"

echo ""
echo "================================================================================"

# Verdict
READY_PCT=$(docker exec horse_racing psql -U postgres -d horse_db -t -A -c "
SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / NULLIF(COUNT(*), 0), 0)
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '$TARGET_DATE';
" | tr -d ' ')

echo ""
if [ "$READY_PCT" = "100" ]; then
    echo "✅ READY - Data is populated! You can run ./RUN_BOTH_STRATEGIES.sh"
elif [ -n "$READY_PCT" ] && [ "$READY_PCT" -gt "0" ]; then
    echo "⚠️  PARTIAL - Only $READY_PCT% of runners have odds"
    echo "   Some bets may appear, but selections will be limited"
else
    echo "❌ NOT READY - No odds data available!"
    echo ""
    echo "📋 DEVELOPER MUST:"
    echo "   1. Fetch Betfair Exchange prices"
    echo "   2. Update racing.runners.win_ppwap column"
    echo "   3. See: CRITICAL_FOR_DEVELOPER.md"
fi

echo ""
echo "================================================================================"
echo ""

# Show sample races
echo "📋 Sample races for $TARGET_DATE:"
echo ""
docker exec horse_racing psql -U postgres -d horse_db -c "
SELECT 
    TO_CHAR(r.off_time, 'HH24:MI') as time,
    c.course_name as course,
    COUNT(*) as runners,
    COUNT(*) FILTER (WHERE ru.win_ppwap IS NOT NULL OR ru.dec IS NOT NULL) as with_odds
FROM racing.races r
LEFT JOIN racing.courses c ON c.course_id = r.course_id
JOIN racing.runners ru ON ru.race_id = r.race_id
WHERE r.race_date = '$TARGET_DATE'
GROUP BY r.off_time, c.course_name
ORDER BY r.off_time
LIMIT 10;
"

echo ""
