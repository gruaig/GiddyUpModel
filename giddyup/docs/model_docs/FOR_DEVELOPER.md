# For Developer: Database Requirements (Simple Version)

**Script**: `get_tomorrows_bets.sh`  
**Needs**: Odds data from database  
**When**: 8:00 AM daily

---

## ✅ **What You Need to Provide**

### **1. Tomorrow's Races** 
```sql
-- Table: racing.races
-- Must have rows WHERE race_date = '2025-10-18'
SELECT race_id, race_date, off_time, course_id 
FROM racing.races 
WHERE race_date = '2025-10-18';
```
**Expected**: 40-60 rows ✅ You already have this

---

### **2. Runners with ODDS** ⭐ **CRITICAL**

```sql
-- Table: racing.runners
-- MUST have win_ppwap OR dec populated
SELECT race_id, horse_id, win_ppwap, dec
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '2025-10-18';
```

**Critical column**: 
- **`win_ppwap`** (Betfair exchange odds) - **PREFERRED**
- **`dec`** (bookmaker decimal odds) - Fallback

**At least ONE must be NOT NULL** ⭐

**Status check**:
```sql
SELECT COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) * 100.0 / COUNT(*) as pct_ready
FROM racing.runners ru JOIN racing.races r USING (race_id) WHERE r.race_date = '2025-10-18';
```
**Need**: pct_ready >= 80%

---

### **3. Horse/Course Names** (For Display)

```sql
-- Table: racing.horses
SELECT horse_id, horse_name FROM racing.horses;

-- Table: racing.courses  
SELECT course_id, course_name FROM racing.courses;
```

**Required**: Foreign keys must link correctly

---

## ⏰ **When is Data Ready?**

```
TODAY (Oct 17, 11 PM):
  Races for Oct 18: ✅ YES
  Odds for Oct 18: ❌ NO (not yet)

TOMORROW (Oct 18, 8 AM):
  Races for Oct 18: ✅ YES
  Odds for Oct 18: ✅ YES (should be populated by now)
```

**Your job**: Ensure odds are loaded by 8 AM

---

## 🔧 **Quick Test**

Run these 3 queries tomorrow morning:

```sql
-- 1. Races exist?
SELECT COUNT(*) FROM racing.races WHERE race_date = '2025-10-18';
-- Want: > 40

-- 2. Odds ready?
SELECT COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL)
FROM racing.runners ru JOIN racing.races r USING (race_id) 
WHERE r.race_date = '2025-10-18';
-- Want: > 400

-- 3. Names exist?
SELECT COUNT(*) FROM racing.runners ru 
JOIN racing.horses h USING (horse_id)
WHERE ru.race_id IN (SELECT race_id FROM racing.races WHERE race_date = '2025-10-18')
AND h.horse_name IS NOT NULL;
-- Want: > 400
```

**If all 3 pass**: ✅ Script will work

---

## 📊 **What Columns Are Used**

### **Must Have**:
- `racing.races`: race_id, race_date, off_time, course_id
- `racing.runners`: race_id, horse_id, **win_ppwap** or **dec**
- `racing.horses`: horse_id, horse_name
- `racing.courses`: course_id, course_name

### **Nice to Have**:
- `racing.runners`: num, age, lbs, trainer_id, jockey_id
- `racing.trainers`: trainer_id, trainer_name
- `racing.jockeys`: jockey_id, jockey_name

### **Not Used**:
- Everything else (won't break if missing)

---

## 🚨 **Common Issues**

**"Script returns 0 bets every day"**:
- Check: `win_ppwap` and `dec` both NULL?
- Solution: Populate odds by 8 AM

**"Missing horse names"**:
- Check: Foreign key `runners.horse_id` → `horses.horse_id` broken?
- Solution: Ensure all horse_ids exist in horses table

**"Query is slow"**:
- Check: Missing indexes?
- Solution: Add index on `races(race_date)` and `runners(race_id)`

---

## ✅ **Summary**

**You need**:
1. Races for tomorrow ✅ (already exists)
2. **ODDS** by 8 AM ⭐ (`win_ppwap` column)
3. Names linked correctly ✅ (already exists)

**That's it!**

**Test tomorrow**: Run `./get_tomorrows_bets.sh 2025-10-18` at 8 AM

---

**Questions? See `DEVELOPER_DATABASE_REQUIREMENTS.md` for full technical spec.**

