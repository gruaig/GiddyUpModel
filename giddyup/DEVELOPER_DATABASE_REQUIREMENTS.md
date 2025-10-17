# Database Requirements for Betting Script - Developer Guide

**To**: Development Team  
**From**: GiddyUp Modeling  
**Date**: October 17, 2025  
**Subject**: Required database schema for daily bet selection script

---

## 🎯 **TL;DR - What We Need**

**Minimum required for script to work**:
1. Races for target date in `racing.races`
2. Runners with **ODDS** in `racing.runners`
3. Horse/course/trainer/jockey names for display

**Critical**: **Odds must be populated** (`win_ppwap` or `dec` column in `racing.runners`)

**Without odds, script cannot run.**

---

## 📋 **Required Tables & Columns**

### **Table 1: `racing.races`** (Race Details)

**Required Columns**:

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `race_id` | BIGINT | ✅ YES | Primary key | 810449 |
| `race_date` | DATE | ✅ YES | Date of race | 2025-10-18 |
| `off_time` | TIMESTAMP | ✅ YES | Race start time | 2025-10-18 14:30:00 |
| `course_id` | BIGINT | ✅ YES | Links to courses table | 15 |
| `class` | TEXT | Recommended | Race class/grade | "(Class 2)", "Group 1" |
| `dist_f` | NUMERIC | Recommended | Distance in furlongs | 8.0 |
| `going` | TEXT | Recommended | Ground condition | "Good", "Soft" |
| `ran` | INT | Recommended | Number of runners | 12 |

**SQL Check**:
```sql
SELECT COUNT(*) FROM racing.races WHERE race_date = '2025-10-18';
-- Should return: ~40-60 races
```

---

### **Table 2: `racing.runners`** ⭐ **MOST CRITICAL**

**Required Columns**:

| Column | Type | Required | Description | Example | Notes |
|--------|------|----------|-------------|---------|-------|
| `race_id` | BIGINT | ✅ YES | Links to races | 810449 | Foreign key |
| `horse_id` | BIGINT | ✅ YES | Links to horses | 123456 | Foreign key |
| **`win_ppwap`** | NUMERIC | ⭐ **CRITICAL** | Betfair exchange WAP odds | 9.50 | **MUST HAVE** |
| **`dec`** | NUMERIC | ⭐ Fallback | Decimal odds (bookmaker) | 9.00 | Use if `win_ppwap` null |
| `trainer_id` | BIGINT | ✅ YES | Links to trainers | 5678 | For display |
| `jockey_id` | BIGINT | ✅ YES | Links to jockeys | 9012 | For display |
| `num` | INT | Recommended | Runner number/draw | 5 | For display |
| `age` | INT | Recommended | Horse age | 4 | For display |
| `lbs` | INT | Recommended | Weight carried | 130 | For display |

**Critical Requirement**:

```sql
-- AT LEAST ONE of these must be NOT NULL:
COALESCE(win_ppwap, dec) IS NOT NULL

-- Preferred: win_ppwap (Betfair exchange odds)
-- Acceptable: dec (bookmaker odds as fallback)
```

**SQL Check**:
```sql
-- Check odds availability for tomorrow
SELECT 
    COUNT(*) as total_runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) as have_exchange_odds,
    COUNT(*) FILTER (WHERE dec IS NOT NULL) as have_book_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / COUNT(*), 0) || '%' as pct_with_odds
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '2025-10-18';

-- Required: pct_with_odds >= 80%
```

---

### **Table 3: `racing.horses`** (Horse Names)

**Required Columns**:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `horse_id` | BIGINT | ✅ YES | Primary key |
| `horse_name` | TEXT | ✅ YES | Horse name for display |

**SQL Check**:
```sql
SELECT COUNT(*) FROM racing.horses WHERE horse_name IS NOT NULL;
-- Should return: ~180,000+
```

---

### **Table 4: `racing.courses`** (Course Names)

**Required Columns**:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `course_id` | BIGINT | ✅ YES | Primary key |
| `course_name` | TEXT | ✅ YES | Course name for display |

**Examples**: "Ascot", "Cheltenham", "Newmarket"

---

### **Table 5: `racing.trainers`** (Trainer Names)

**Required Columns**:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `trainer_id` | BIGINT | ✅ YES | Primary key |
| `trainer_name` | TEXT | Recommended | Trainer name for display |

---

### **Table 6: `racing.jockeys`** (Jockey Names)

**Required Columns**:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `jockey_id` | BIGINT | ✅ YES | Primary key |
| `jockey_name` | TEXT | Recommended | Jockey name for display |

---

## 🔍 **Detailed Requirements**

### **Primary Requirement: ODDS Data**

**The script CANNOT work without odds.** Specifically:

```sql
-- In racing.runners table, for each runner tomorrow:
win_ppwap IS NOT NULL  -- Betfair exchange odds (PREFERRED)
OR
dec IS NOT NULL        -- Bookmaker decimal odds (FALLBACK)
```

**When is this available**:
- **NOT available**: Night before (Oct 17 evening)
- **Available**: Morning of race day (Oct 18, 6-8 AM)
- **Most complete**: 2-3 hours before first race

**Developer Action Required**:
```
Ensure that by 8:00 AM on race day, the following query returns > 80%:

SELECT 
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / COUNT(*), 0) as pct
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = CURRENT_DATE;

If pct < 80%: Odds loading is delayed, check data pipeline
```

---

## 📊 **Data Flow: What Happens**

### **Night Before (Oct 17)**

```
racing.races:
  ✅ Rows for Oct 18 exist (race_id, date, time, course)
  
racing.runners:
  ⚠️  Rows for Oct 18 exist (horse_id, race_id)
  ❌ win_ppwap = NULL (not yet populated)
  ❌ dec = NULL (not yet populated)

Status: CANNOT score yet
```

### **Morning Of (Oct 18, 8:00 AM)**

```
racing.races:
  ✅ Still there
  
racing.runners:
  ✅ win_ppwap NOW POPULATED (e.g., 9.50)
  ✅ dec NOW POPULATED (e.g., 9.00)

Status: ✅ CAN score now!
```

### **Script Runs**

```sql
1. Query: Get all runners for Oct 18 with odds
2. Calculate: Market rank per race (RANK() function)
3. Calculate: Vig-free probabilities (1/odds math)
4. Filter: Apply 6 gates (odds range, rank, disagreement, etc.)
5. Select: Top-1 per race by edge
6. Output: 0-5 bet recommendations
```

---

## 🗄️ **Database Schema Requirements**

### **Relationships**:

```
racing.races
    ↓ (race_id)
racing.runners
    ↓ (horse_id)          ↓ (course_id)      ↓ (trainer_id)   ↓ (jockey_id)
racing.horses         racing.courses      racing.trainers  racing.jockeys
```

**All foreign keys must be valid** for joins to work.

---

### **Indexes Needed** (Performance):

```sql
-- Critical for performance
CREATE INDEX IF NOT EXISTS idx_races_date ON racing.races(race_date);
CREATE INDEX IF NOT EXISTS idx_runners_race ON racing.runners(race_id);
CREATE INDEX IF NOT EXISTS idx_runners_odds ON racing.runners(win_ppwap, dec);

-- Without these, queries will be slow on 450+ runners
```

---

## 🔧 **SQL Query the Script Uses**

**Full query** (simplified):

```sql
-- Step 1: Get base data
WITH race_data AS (
    SELECT 
        r.race_id,
        r.off_time,
        c.course_name,
        h.horse_name,
        ru.win_ppwap as decimal_odds,  -- Or: COALESCE(ru.win_ppwap, ru.dec)
        
        -- Calculate market rank
        RANK() OVER (
            PARTITION BY r.race_id 
            ORDER BY ru.win_ppwap
        ) as market_rank,
        
        -- Calculate probabilities
        1.0 / ru.win_ppwap as q_market,
        SUM(1.0 / ru.win_ppwap) OVER (PARTITION BY r.race_id) as overround
        
    FROM racing.runners ru
    JOIN racing.races r USING (race_id)
    LEFT JOIN racing.courses c USING (course_id)
    LEFT JOIN racing.horses h USING (horse_id)
    WHERE r.race_date = '2025-10-18'
    AND ru.win_ppwap IS NOT NULL
)

-- Step 2: Calculate metrics
-- Step 3: Apply filters (6 gates)
-- Step 4: Select top-1 per race
-- Step 5: Return results
```

---

## 🚨 **Common Issues & Solutions**

### **Issue 1: "No bets found" Every Day**

**Cause**: Odds not populated

**Check**:
```sql
SELECT win_ppwap, dec FROM racing.runners LIMIT 10;
```

**If both NULL**: Odds loading is broken, check ETL pipeline

**Solution**: Ensure odds load by 8 AM daily

---

### **Issue 2: Query Returns 0 Rows**

**Cause**: Missing joins (horse_name NULL, course_name NULL)

**Check**:
```sql
SELECT 
    COUNT(*) as total,
    COUNT(h.horse_name) as have_horse_name,
    COUNT(c.course_name) as have_course_name
FROM racing.runners ru
JOIN racing.races r USING (race_id)
LEFT JOIN racing.horses h USING (horse_id)
LEFT JOIN racing.courses c USING (course_id)
WHERE r.race_date = '2025-10-18';
```

**Solution**: Ensure foreign keys are populated

---

### **Issue 3: Incorrect Market Ranks**

**Cause**: NULL odds mixed with valid odds

**Check**:
```sql
-- Should have no NULLs in result
SELECT COUNT(*) 
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '2025-10-18'
AND (ru.win_ppwap IS NULL AND ru.dec IS NULL);
```

**Solution**: Filter out NULL odds before RANK() calculation

---

## 📊 **Sample Data Requirements**

### **For Oct 18, 2025**:

```
racing.races:
  Expected: 52 rows (52 races)
  Required: race_id, race_date='2025-10-18', off_time, course_id

racing.runners:
  Expected: ~489 rows (~9 horses per race)
  Required: race_id, horse_id, win_ppwap (or dec)
  Critical: win_ppwap >= 1.01 for at least 80% of rows

racing.horses:
  Expected: ~180,000 rows total
  Required: horse_id (must match runners.horse_id), horse_name NOT NULL

racing.courses:
  Expected: ~60 rows (UK/Irish courses)
  Required: course_id (must match races.course_id), course_name NOT NULL
```

---

## 🛠️ **Developer Checklist**

### **Before Script Can Run**:

- [ ] `racing.races` table has rows for target date
- [ ] `racing.runners` table has rows for target date
- [ ] **`win_ppwap` OR `dec` is populated** (⭐ CRITICAL)
- [ ] Foreign keys valid:
  - [ ] `runners.horse_id` → `horses.horse_id`
  - [ ] `runners.race_id` → `races.race_id`
  - [ ] `races.course_id` → `courses.course_id`
  - [ ] `runners.trainer_id` → `trainers.trainer_id` (optional)
  - [ ] `runners.jockey_id` → `jockeys.jockey_id` (optional)
- [ ] `horse_name` NOT NULL for display
- [ ] `course_name` NOT NULL for display

---

### **Validation Query** (Run This Daily):

```sql
-- Run at 7:30 AM before script
SELECT 
    race_date,
    COUNT(DISTINCT r.race_id) as races,
    COUNT(ru.horse_id) as total_runners,
    COUNT(*) FILTER (WHERE ru.win_ppwap IS NOT NULL) as have_exchange_odds,
    COUNT(*) FILTER (WHERE ru.dec IS NOT NULL) as have_book_odds,
    COUNT(*) FILTER (WHERE ru.win_ppwap IS NOT NULL OR ru.dec IS NOT NULL) as have_any_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE ru.win_ppwap IS NOT NULL OR ru.dec IS NOT NULL) / COUNT(*)::numeric, 0) as pct_ready,
    
    -- Data quality checks
    COUNT(*) FILTER (WHERE h.horse_name IS NULL) as missing_horse_names,
    COUNT(*) FILTER (WHERE c.course_name IS NULL) as missing_course_names
    
FROM racing.runners ru
JOIN racing.races r USING (race_id)
LEFT JOIN racing.horses h USING (horse_id)
LEFT JOIN racing.courses c ON c.course_id = r.course_id
WHERE r.race_date = CURRENT_DATE  -- Or tomorrow
GROUP BY race_date;
```

**Success Criteria**:
- ✅ `pct_ready` >= 80%
- ✅ `missing_horse_names` = 0
- ✅ `missing_course_names` = 0

**If any fail**: Data pipeline issue, investigate before script runs.

---

## 🔍 **Detailed Column Requirements**

### **`racing.runners.win_ppwap`** (Preferred)

**What it is**: Betfair Pre-Play Weighted Average Price

**Format**: 
- Type: `NUMERIC` or `DOUBLE PRECISION`
- Range: 1.01 to 1000.0
- Decimals: 2-4 places (e.g., 9.50, 12.3456)

**When available**: 
- **Best**: 8:00 AM on race day
- **Latest**: 2-3 hours before first race
- **Source**: Betfair exchange API

**Example values**:
```
Favorite:     3.50
2nd favorite: 5.20
Mid-field:    9.50, 11.00, 12.00  ← Our target
Outsider:     21.00, 51.00
```

**NULL handling**:
```sql
-- Script uses:
COALESCE(ru.win_ppwap, ru.dec) as decimal_odds

-- Falls back to dec if win_ppwap is NULL
-- If BOTH NULL, runner is excluded
```

---

### **`racing.runners.dec`** (Fallback)

**What it is**: Decimal odds (usually from bookmaker)

**Format**: Same as `win_ppwap`

**When to use**: 
- If Betfair data unavailable
- As fallback if `win_ppwap` NULL

**Note**: 
- Usually 5-10% lower than exchange odds
- May reduce profitability
- But better than nothing

---

## ⏰ **Data Timing Requirements**

### **What Needs to Be Ready When**:

```
Day Before (Oct 17):
  23:59 - racing.races for Oct 18: ✅ MUST exist
        - racing.runners for Oct 18: ✅ MUST exist (can have NULL odds)

Race Day (Oct 18):
  06:00 - win_ppwap starts populating: ⚠️  Loading
  07:00 - win_ppwap ~50% complete: ⚠️  Loading
  08:00 - win_ppwap ~80-95% complete: ✅ READY TO SCORE
  09:00 - win_ppwap 95-100% complete: ✅ Fully ready
```

**Script should run**: **8:00 AM** (or when `pct_ready` >= 80%)

---

## 🔢 **Data Volume Expectations**

### **Typical Racing Day**:

```
Races: 40-60
Runners per race: 8-12 average
Total runners: 400-600

After filtering (script logic):
  - Odds 7-12: ~150 horses (30%)
  - Rank 3-6: ~150 horses (30%)
  - Combined filters: ~5-20 horses
  - Top-1 per race: 2-5 bets
```

---

## 🎯 **Minimum Viable Data Set**

**To test the script, developer needs**:

```sql
-- 1. One race
INSERT INTO racing.races (race_id, race_date, off_time, course_id, class, dist_f, going, ran)
VALUES (999999, '2025-10-18', '2025-10-18 14:30:00', 1, '(Class 2)', 8.0, 'Good', 10);

-- 2. Ten runners with odds
INSERT INTO racing.runners (race_id, horse_id, win_ppwap, num, age, lbs)
VALUES 
  (999999, 1, 3.50, 1, 5, 132),  -- Favorite
  (999999, 2, 5.00, 2, 4, 130),  -- 2nd favorite
  (999999, 3, 7.50, 3, 4, 128),  -- 3rd (rank 3 - qualifies!)
  (999999, 4, 9.50, 4, 5, 126),  -- 4th (rank 4 - qualifies!)
  (999999, 5, 11.0, 5, 3, 125),  -- 5th (rank 5 - qualifies!)
  (999999, 6, 13.0, 6, 6, 124),  -- 6th (rank 6 - qualifies!)
  (999999, 7, 17.0, 7, 4, 123),  -- Too long
  (999999, 8, 21.0, 8, 5, 122),  -- Too long
  (999999, 9, 26.0, 9, 4, 121),  -- Too long
  (999999, 10, 41.0, 10, 3, 120); -- Too long

-- 3. Link to horses table
INSERT INTO racing.horses (horse_id, horse_name)
VALUES 
  (1, 'Test Favorite'),
  (2, 'Test Second'),
  (3, 'Test Third'),
  (4, 'Test Fourth'),
  (5, 'Test Fifth'),
  (6, 'Test Sixth'),
  (7, 'Test Seventh'),
  (8, 'Test Eighth'),
  (9, 'Test Ninth'),
  (10, 'Test Tenth');

-- 4. Link to courses
INSERT INTO racing.courses (course_id, course_name)
VALUES (1, 'Test Track');
```

**Then run**:
```bash
./get_tomorrows_bets.sh 2025-10-18
```

**Expected**: 1-2 bets from the rank 3-6 horses (IDs 3,4,5,6)

---

## 📋 **Pre-Flight Checks**

**Developer should verify**:

### **Check 1: Tomorrow's Races Exist**
```sql
SELECT COUNT(*) FROM racing.races WHERE race_date = '2025-10-18';
-- Expected: > 0 (ideally 40-60)
```

### **Check 2: Runners Exist**
```sql
SELECT COUNT(*) FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '2025-10-18';
-- Expected: > 0 (ideally 400-600)
```

### **Check 3: Odds Populated** ⭐
```sql
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) as with_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / COUNT(*), 0) as pct
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '2025-10-18';
-- Required: pct >= 80
```

### **Check 4: Names Populated**
```sql
SELECT 
    COUNT(*) as total,
    COUNT(h.horse_name) as have_name
FROM racing.runners ru
JOIN racing.races r USING (race_id)
LEFT JOIN racing.horses h USING (horse_id)
WHERE r.race_date = '2025-10-18';
-- Required: have_name ~= total
```

---

## 🚀 **What Developer Needs to Do**

### **Option A: Data Already Complete** (Best Case)

**If your data pipeline already populates**:
- ✅ `racing.races` for tomorrow
- ✅ `racing.runners` with `win_ppwap` by 8 AM
- ✅ All foreign keys valid

**Then**: Nothing! Script will work as-is.

---

### **Option B: Need to Add Odds Loading** (Most Common)

**If odds aren't loading automatically**:

```python
# Create ETL job to run at 7:00 AM daily

import requests  # Or your Betfair API client

def load_tomorrows_odds():
    # 1. Get races for tomorrow
    races = get_races(date=tomorrow)
    
    # 2. For each race, get Betfair odds
    for race in races:
        betfair_odds = fetch_betfair_odds(race_id)
        
        # 3. Update racing.runners
        for horse, odds in betfair_odds.items():
            UPDATE racing.runners
            SET win_ppwap = odds
            WHERE race_id = race_id AND horse_id = horse_id
    
# Run this at 7:00 AM daily
```

---

### **Option C: Manual Population** (Testing)

**For testing tomorrow**:

```sql
-- Manually update odds for Oct 18
UPDATE racing.runners ru
SET win_ppwap = 
    CASE 
        WHEN ru.num = 1 THEN 3.5 + random() * 2  -- Favorites: 3.5-5.5
        WHEN ru.num <= 4 THEN 5.0 + random() * 5  -- Mid-field: 5-10
        ELSE 10.0 + random() * 20                 -- Outsiders: 10-30
    END
FROM racing.races r
WHERE ru.race_id = r.race_id
AND r.race_date = '2025-10-18';

-- Then run script
```

**Only for testing!** Real data is better.

---

## 📄 **Summary for Developer**

### **What You Must Provide**:

1. **Table**: `racing.races` with rows for target date
2. **Table**: `racing.runners` with **odds populated** by 8 AM
3. **Column**: `win_ppwap` (Betfair) OR `dec` (bookmaker) - **NOT NULL**
4. **Foreign Keys**: Valid links to horses, courses, trainers, jockeys
5. **Names**: `horse_name`, `course_name` NOT NULL

### **When**:
- **By**: 8:00 AM on race day
- **Frequency**: Daily (every racing day)
- **Validation**: Run pre-flight checks (queries above)

### **Performance**:
- Query runs in < 5 seconds (with proper indexes)
- Returns 0-5 results
- No heavy computation (just SQL filters)

---

## 🧪 **Testing Instructions**

**For developer to test**:

```bash
# 1. Check data exists
psql -c "SELECT COUNT(*) FROM racing.races WHERE race_date = '2025-10-18';"

# 2. Check odds populated
psql -c "SELECT COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) FROM racing.runners ru JOIN racing.races r USING (race_id) WHERE r.race_date = '2025-10-18';"

# 3. Run script
cd /home/smonaghan/GiddyUpModel/giddyup
./get_tomorrows_bets.sh 2025-10-18

# 4. Verify output
# Should show: 0-5 bets with horse names, courses, odds
```

---

## 📞 **Questions for Developer?**

**Common questions**:

**Q**: "What if `win_ppwap` is NULL?"  
**A**: Script uses `COALESCE(win_ppwap, dec)` - falls back to `dec`. But prefer `win_ppwap`.

**Q**: "When is data ready?"  
**A**: 8:00 AM on race day. Run pre-flight check first.

**Q**: "What if no horses qualify?"  
**A**: Normal! Script returns 0 rows. Happens ~50% of days.

**Q**: "Can we cache the model?"  
**A**: Yes, but not needed yet. Query is fast (<5s).

**Q**: "Need historical data?"  
**A**: No! Just tomorrow's races + odds. Model already trained.

---

## ✅ **Acceptance Criteria**

**Script is working correctly when**:

1. ✅ Returns 0-5 bets per day
2. ✅ Shows horse names (not NULL)
3. ✅ Shows course names (not NULL)
4. ✅ Odds are in 7-12 range
5. ✅ Market rank is 3-6
6. ✅ Query runs in < 5 seconds

**Test on**: Oct 18, 19, 20, 2025 (multiple days)

---

**Any questions? I can clarify any technical details!** 🚀

