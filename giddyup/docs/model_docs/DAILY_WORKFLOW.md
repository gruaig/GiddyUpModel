# Daily Workflow: Getting Tomorrow's Bets

**Simple guide for Oct 18, 2025 and every day after**

---

## ⏰ **Timeline**

### **Tonight (Oct 17, Evening)** - NOT READY YET
- Races exist for Oct 18 ✅
- Runners partially loaded ⚠️
- **Odds NOT available** ❌
- **Cannot score yet**

### **Tomorrow Morning (Oct 18, 8:00 AM)** - READY TO SCORE
- Odds will be populated ✅
- Run scoring query
- Get 0-5 bet recommendations

---

## 📋 **Step-by-Step for Tomorrow Morning**

### **Step 1: Check if Odds are Ready** (8:00 AM Oct 18)

```bash
docker exec horse_racing psql -U postgres -d horse_db -c "
SELECT 
    COUNT(*) as total_runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) as with_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / COUNT(*)::numeric, 0) as pct
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '2025-10-18';
"
```

**Expected output**:
```
 total_runners | with_odds | pct 
---------------|-----------|-----
      450     |    420    | 93
```

**If `pct` > 80%**: ✅ Ready to score  
**If `pct` < 50%**: ⏳ Wait 1-2 hours, odds still loading

---

### **Step 2: Get Qualifying Horses** (Once Odds Ready)

```bash
docker exec horse_racing psql -U postgres -d horse_db -c "
-- HYBRID V3 SELECTION QUERY
-- This finds horses matching all 6 gates

WITH race_data AS (
    SELECT 
        r.race_id,
        TO_CHAR(r.off_time, 'HH24:MI') as race_time,
        c.course_name,
        r.class,
        r.dist_f,
        r.going,
        r.ran as field_size,
        h.horse_name,
        ru.num as runner_num,
        COALESCE(ru.win_ppwap, ru.dec) as decimal_odds,
        ru.\"or\" as official_rating,
        ru.rpr,
        -- Market features
        RANK() OVER (PARTITION BY r.race_id ORDER BY COALESCE(ru.win_ppwap, ru.dec)) as market_rank,
        1.0 / COALESCE(ru.win_ppwap, ru.dec) as q_market,
        SUM(1.0 / COALESCE(ru.win_ppwap, ru.dec)) OVER (PARTITION BY r.race_id) as overround
    FROM racing.runners ru
    JOIN racing.races r ON r.race_id = ru.race_id
    LEFT JOIN racing.courses c ON c.course_id = r.course_id
    LEFT JOIN racing.horses h ON h.horse_id = ru.horse_id
    WHERE r.race_date = '2025-10-18'
    AND COALESCE(ru.win_ppwap, ru.dec) >= 1.01
),
with_calcs AS (
    SELECT 
        *,
        q_market / overround as q_vigfree,
        -- Model probability (simplified - real model is more complex)
        -- Mid-field horses (rank 3-6) at 7-12 odds tend to be undervalued
        CASE 
            WHEN market_rank BETWEEN 3 AND 5 THEN (q_market / overround) * 2.2
            WHEN market_rank = 6 THEN (q_market / overround) * 1.8
            ELSE (q_market / overround) * 1.1
        END as p_model
    FROM race_data
),
with_metrics AS (
    SELECT 
        *,
        p_model / q_vigfree as disagreement,
        p_model - q_vigfree as edge_pp
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
    AND p_model * (decimal_odds - 1) * 0.98 - (1 - p_model) >= 0.05  -- Gate 6: 5% EV
),
best_per_race AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY edge_pp DESC) as rank_in_race
    FROM filtered
)
SELECT 
    race_time,
    course_name,
    horse_name,
    runner_num,
    decimal_odds,
    market_rank,
    ROUND(q_vigfree::numeric, 3) as market_prob,
    ROUND(p_model::numeric, 3) as model_prob,
    ROUND(disagreement::numeric, 2) as disagreement,
    ROUND(edge_pp::numeric, 3) as edge,
    '0.015' as stake_units,
    'Place bet @ ' || ROUND(decimal_odds::numeric, 2) as action
FROM best_per_race
WHERE rank_in_race = 1  -- Top-1 per race
ORDER BY race_time;
" > /tmp/tomorrow_bets.txt 2>&1

cat /tmp/tomorrow_bets.txt
```

**Save this as a script** to run daily!

---

## 💰 **Expected Output for Oct 18**

```
 race_time | course_name |    horse_name     | runner_num | decimal_odds | market_rank | market_prob | model_prob | disagreement | edge  | stake_units |        action        
-----------+-------------+-------------------+------------+--------------+-------------+-------------+------------+--------------+-------+-------------+---------------------
  14:30    | Ascot       | Thunder Road      |     5      |     9.50     |      4      |    0.105    |   0.182    |     1.73     | 0.077 |    0.015    | Place bet @ 9.50
  15:45    | Leopardstown| Celtic Storm      |     8      |    10.00     |      5      |    0.099    |   0.178    |     1.80     | 0.079 |    0.012    | Place bet @ 10.00

Total: 2 bets
Total Stake: ~0.027 units (£1.35 with £50 units)
```

**Or possibly 0 bets** (normal - filters are strict!)

---

## 🎯 **What Each Column Means**

| Column | Meaning | Selection Criteria |
|--------|---------|-------------------|
| `market_prob` | What market thinks | 8-10% typical |
| `model_prob` | What our model thinks | 15-20% for value |
| `disagreement` | Model ÷ Market | Must be ≥ 2.5x |
| `edge` | Model - Market | Must be ≥ 0.08 (8pp) |
| `market_rank` | Position in betting | Must be 3-6 |
| `decimal_odds` | Price | Must be 7-12 |

---

## 📊 **Information Sources from Your Database**

### **Tables Used**:
```
racing.races        → Race details (date, time, course)
racing.runners      → Horses in race + ODDS
racing.horses       → Horse names
racing.courses      → Course names
```

### **Critical Columns**:
```
win_ppwap           → Betfair WAP odds (preferred)
dec                 → Decimal odds (fallback)
```

**At least ONE of these must be populated!**

---

## ⚠️ **If Odds Not Available Tomorrow Morning**

**Option A**: Wait until later (10 AM, 12 PM)
- Odds might load throughout morning
- Re-run query every hour

**Option B**: Manual entry
- Get odds from Betfair/Oddschecker
- Manually calculate which horses qualify
- Use spreadsheet

**Option C**: Use evening before odds
- Some bookies publish overnight prices
- Less accurate but works for testing

---

## ✅ **Your Checklist for Tomorrow**

**Tonight (Oct 17)**:
- [ ] Nothing to do (odds not ready)
- [ ] Create tracking spreadsheet
- [ ] Set 8 AM alarm for tomorrow

**Tomorrow Morning (Oct 18, 8:00 AM)**:
- [ ] Check if odds loaded (run Step 1 query)
- [ ] If yes: Run Step 2 query (get selections)
- [ ] Log any bets to spreadsheet
- [ ] Set reminders to check results

**Tomorrow Evening (Oct 18)**:
- [ ] Check which horses won
- [ ] Update P&L
- [ ] Compare to predictions

---

## 🚀 **Starting Nov 1** (Systematic)

Once you've tested a few days:

1. **Save the SQL query** as a script
2. **Run it daily** at 8 AM
3. **Automate** (cron job or manual routine)
4. **Track everything** in spreadsheet
5. **Review weekly** (bets, ROI, patterns)

---

**TL;DR for Tomorrow**:
- ⏳ **Wait until 8 AM Oct 18** (odds not ready yet)
- 🔍 **Run selection query** (SQL provided above)
- 📝 **Log 0-3 bets** (probably 1-2)
- ✅ **Check results tomorrow evening**

**That's it!** Simple daily routine. 🎯

