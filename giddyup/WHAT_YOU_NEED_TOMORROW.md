# What You Need for Tomorrow's Selections (Oct 18, 2025)

**Status**: Oct 17, 2025 - Preparing for Oct 18 racing  
**Races Tomorrow**: 52 races (Ascot, Catterick, Leopardstown, Limerick, Stratford)

---

## 📋 **Information Required from Database**

### **1. Tomorrow's Races** ✅ (Already Available)

```sql
SELECT race_id, off_time, course_name, class, distance, going
FROM racing.races
WHERE race_date = '2025-10-18'
```

**Status**: ✅ You have 52 races scheduled

---

###  **2. Runners in Each Race** ⚠️ (Partially Available)

```sql
SELECT race_id, horse_id, horse_name, trainer, jockey, 
       draw, age, weight
FROM racing.runners
JOIN racing.horses USING (horse_id)
WHERE race_id IN (SELECT race_id FROM racing.races WHERE race_date = '2025-10-18')
```

**Current Status**: Some runners loaded (4-7 per race), **but odds not yet populated**

---

### **3. Market Odds** ❌ (NOT YET AVAILABLE)

**What you need**:
```sql
-- From racing.runners
SELECT horse_id, win_ppwap, dec
WHERE race_id IN (...)

-- OR from market.price_snapshots  
SELECT horse_id, decimal_odds, snapped_at
WHERE race_id IN (...) AND snapped_at >= NOW() - INTERVAL '2 hours'
```

**Current Status for Oct 18**: 
- `win_ppwap`: 0 horses have this ❌
- `dec`: 0 horses have this ❌

**When available**: Usually populated **morning of race day** or **evening before**

---

## ⏰ **Timeline: When Data Becomes Available**

### **Today (Oct 17, Evening)**

```
Races for Oct 18: ✅ Already loaded
Runners: ⚠️  Partial (some horses loaded, no odds yet)
Odds: ❌ Not available yet
```

**You CAN'T score yet** - need odds!

---

### **Tomorrow (Oct 18, Morning 6-8 AM)**

```
Races: ✅ Complete
Runners: ✅ Complete
Odds: ✅ Morning prices available (win_ppwap, dec)
```

**NOW you can score!**

Run at **8:00 AM on Oct 18**:
```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/score_today_simple.py --date 2025-10-18
```

This will show you **0-5 bets** for today's racing.

---

### **Race Day (Oct 18, Throughout Day)**

```
08:00 AM: Morning odds available → Score and get selections
10:00 AM: Updated odds → Can re-score if needed
12:00 PM: First races start
06:00 PM: Last races finish
Evening: Results available → Update your tracking
```

---

## 📊 **What Information the Model Needs**

### **Minimum Required** (From Database):

#### **A. Race Information**
- `race_id`
- `race_date`  
- `off_time`
- `course_name`
- `class`
- `dist_f` (distance in furlongs)
- `going`
- `ran` (field size)

#### **B. Runner Information**
- `horse_id`
- `horse_name`
- `trainer_id`
- `jockey_id`
- `draw` (stall position)
- `age`
- `lbs` (weight)

#### **C. Market Odds** ⭐ **CRITICAL**
- `decimal_odds` (from `win_ppwap` or `dec`)

**Without odds, we cannot score!**

---

### **Optional (Improves Accuracy)**:
- Historical runs for GPR calculation
- Trainer/jockey stats
- Course form
- Recent form

**But for QUICK selections**, just need race + runner + **odds**.

---

## 🚀 **Simplified Daily Process**

### **Every Morning at 8 AM**:

**Step 1: Check if odds are available**
```sql
SELECT COUNT(*) FROM racing.runners 
WHERE race_id IN (
    SELECT race_id FROM racing.races WHERE race_date = CURRENT_DATE
)
AND (win_ppwap IS NOT NULL OR dec IS NOT NULL);
```

**If count > 0**: ✅ Odds available, proceed to Step 2  
**If count = 0**: ⏳ Wait, odds not loaded yet

---

**Step 2: Run scoring**
```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/score_today_simple.py --date 2025-10-18
```

---

**Step 3: Review selections**

Script outputs:
```
🎯 BET RECOMMENDATIONS FOR 2025-10-18

BET #1
   14:30 Ascot
   Horse: Thunder Road (#5)
   Odds: 9.50 | Rank: 4
   
   Model: 17.2% | Market: 10.5%
   Disagreement: 1.64x | Edge: 6.7pp
   
   💰 BET: 0.015 units @ 9.50 (£0.75 with £50 units)

[More bets...]

Total: 2-4 bets
```

---

**Step 4: Place bets** (During paper trading: just LOG them)

---

**Step 5: Evening - Check results**

```sql
SELECT horse_id, pos_num 
FROM racing.runners
WHERE race_id IN (your_bet_race_ids);
```

Update your tracking:
- Did horse win (pos_num = 1)?
- Calculate P&L
- Update spreadsheet

---

## 📝 **What to Create Today (Oct 17)**

### **1. Tracking Spreadsheet**

Create a Google Sheet or Excel with columns:
```
| Date | Time | Course | Horse | Odds | Rank | Stake | Result | P&L |
|------|------|--------|-------|------|------|-------|--------|-----|
```

---

### **2. Database Query to Check Odds Availability**

Save this query:
```sql
-- Run this each morning to see if odds are ready
SELECT 
    race_date,
    COUNT(DISTINCT race_id) as races,
    COUNT(*) as total_runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) as runners_with_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) / COUNT(*)::numeric, 1) as pct_with_odds
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = CURRENT_DATE  -- Or '2025-10-18'
GROUP BY race_date;
```

When `pct_with_odds` > 80%, you're ready to score!

---

### **3. Set Reminder for Tomorrow Morning**

```
8:00 AM Oct 18:
  1. Check if odds loaded (run query above)
  2. If yes: Run scoring script
  3. Review selections
  4. Log to spreadsheet
```

---

## 🎯 **For ACTUAL Tomorrow (Oct 18)**

Since we're testing the system, here's what to expect:

**Morning (8 AM)**:
- Check database for odds
- If available: Run scorer
- Expected: 0-3 bets (it's picky!)
- Log any selections

**Throughout Day**:
- Races run 9:30 AM - 6:00 PM
- No action needed

**Evening**:
- Check results (which horses won)
- Update P&L
- Compare to predictions

---

## 📊 **Realistic Expectations**

Based on backtest (979 bets/year):

**Daily**:
- Racing days/year: ~300
- Bets/racing day: ~3-4
- **Some days: 0 bets** (50% of days actually)
- **Active days: 5-8 bets**

**Oct 18 specifically**:
- Expect: 0-3 bets (normal)
- If 0: Don't worry, tomorrow might have more
- If 3: Great! Log them and track

---

## ✅ **Summary: What You Need**

### **From Database (Must Have)**:
1. ✅ **Races for tomorrow** - You have this (52 races)
2. ⏳ **Runners** - Partially loaded (will complete tonight/tomorrow)
3. ❌ **Odds** - Not yet available (will appear tomorrow morning)

### **When to Run**:
- **8:00 AM on Oct 18** (not tonight - odds aren't ready)

### **What You'll Get**:
- **0-3 bet recommendations**
- Horse names, courses, times
- Odds, stakes, reasoning
- Total stake for the day

### **What to Do**:
- **Paper trading**: Just log the bets (no real money)
- **Track results**: Update spreadsheet tomorrow evening
- **Repeat daily**: Nov-Dec 2025

---

## 📞 **Quick Test (Use Past Date)**

Want to see what the output looks like? Run on a past date:

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/score_today_simple.py --date 2025-10-01
```

This will show you the format of the selections!

---

**In short**: You need **odds data** from your database, which appears **morning of race day**. Run the scorer at **8 AM tomorrow**! 🚀

