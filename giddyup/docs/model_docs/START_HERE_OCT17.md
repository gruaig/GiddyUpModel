# Your Questions Answered - Oct 17, 2025

---

## ❓ **Q1: What do I need for tomorrow (Oct 18)?**

### **Answer: Just ODDS from your racing database**

**What you have NOW (Oct 17 evening)**:
- ✅ 52 races scheduled for Oct 18
- ✅ Runners loaded (partial)
- ❌ **Odds NOT available yet**

**What you need TOMORROW (Oct 18, 8 AM)**:
- ✅ **Odds** (`win_ppwap` or `dec`) populated in `racing.runners`

**That's it!** Just odds. Everything else is already there.

---

### **How to Check if Odds are Ready**

Run this tomorrow morning:

```bash
docker exec horse_racing psql -U postgres -d horse_db -c "
SELECT 
    COUNT(*) as runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL OR dec IS NOT NULL) as have_odds
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '2025-10-18';
"
```

**If `have_odds` > 400**: ✅ Ready!  
**If `have_odds` < 100**: ⏳ Wait, odds still loading

---

### **How to Get Tomorrow's Selections**

Once odds are ready, run this SQL (saved in `DAILY_WORKFLOW.md`):

```sql
-- Returns 0-5 horses to bet on
-- Shows: time, course, horse, odds, stake
-- All gates applied automatically
```

**Expected**: 0-3 bets for Oct 18  
**Stake**: ~0.03 units total (~£1.50 with £50 units)

---

## ❓ **Q2: How do I select bets going forward?**

### **Answer: Run the same SQL query every morning**

**Daily routine**:
```
8:00 AM: Check if odds ready
8:15 AM: Run selection SQL query
8:30 AM: Log bets to spreadsheet
Throughout day: Races run
Evening: Check results, update P&L
```

**Frequency**: Every racing day (300/year)  
**Bets/day**: 0-5 (average 3-4)  
**Time required**: 10 minutes/day

---

### **What You're Betting On**

Based on backtest (1,794 bets, +3.1% ROI):

**Typical bet**:
- **Odds**: 7-12 range
- **Market Rank**: 3rd-6th favorite (never favorite or 2nd fav)
- **Disagreement**: Model sees 2.5x+ higher probability than market
- **Edge**: 8pp+ minimum
- **Stake**: 0.01-0.02 units (~£0.50-1.00 with £50 units)

**Real example** (from backtest):
```
Zealandia (FR) - Newcastle, Jan 1, 2024
Odds: 9.45 | Rank: 4
Model: 16% | Market: 10.6%
Bet: 0.012u | Result: WON | Profit: +0.10u
```

---

## ❓ **Q3: When do I retrain the model?**

### **Answer: January 1, 2026 (then annually every Jan 1)**

---

### **Your 3-Month Timeline**

#### **NOW - Dec 31, 2025** (2.5 months)

**Use current model** (trained on 2006-2023):
- ✅ Run daily selections
- ✅ Paper trade (NO real money)
- ✅ Track ~160 bets
- ✅ Expected ROI: +3%

**DON'T retrain yet!**

---

#### **January 1, 2026** (Retrain Day)

**Retrain with 2024 data**:
```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# Update config
# Edit train_model.py: train_date_to = "2024-12-31"

# Delete old dataset
rm data/training_dataset.parquet

# Retrain (takes ~60 minutes)
uv run python tools/train_model.py > training_2026.log 2>&1 &

# Wait for completion, then backtest on 2025
uv run python tools/backtest_hybrid.py
```

**New model**:
- Training: 2006-2024 (19 years)
- Validation: 2025 (YOUR paper trading results!)
- Deploy: 2026

**This validates if your paper trading matched the backtest!**

---

#### **Every January 1 After**

```
Jan 1, 2027: Retrain on 2006-2025
Jan 1, 2028: Retrain on 2006-2026
...
```

**Annual schedule**, always hold out most recent year.

---

### **Why NOT Retrain Before Jan 1?**

❌ **Don't retrain based on your own bets**:
- Only ~160 bets in Nov-Dec (tiny sample)
- Selection bias (only bet where model was confident)
- Overfits to your results
- Loses generalization

✅ **Do retrain on ALL races**:
- All ~95,000 races from 2024
- No selection bias
- Keeps model general
- Proper validation

---

## ❓ **Q4: Should I use this until end of year then retrain?**

### **Answer: YES, exactly!** ✅

**Perfect plan**:
```
Oct 17 - Dec 31 (2.5 months):
  ✅ Use current model (2006-2023 training)
  ✅ Paper trade daily
  ✅ Track all bets
  ✅ Target: 200 bets, +3% ROI
  
Jan 1, 2026:
  ✅ Retrain on 2006-2024
  ✅ Validate on 2025 (your results!)
  ✅ Deploy new model
  
Q1 2026:
  ✅ If paper trading was successful: deploy real stakes
  ✅ Monitor weekly
  ✅ Continue through 2026
  
Jan 1, 2027:
  ✅ Retrain again (annual cycle)
```

**This is the correct approach!**

---

## 📊 **Realistic Expectations (Nov-Dec 2025)**

### **Daily**:
```
Selections: 0-5 bets
Avg: 3 bets/day on racing days
Stake: £1-2 total
```

### **Weekly**:
```
Bets: 15-25
Stake: ~£10-15
P&L: -£5 to +£8 (variance)
```

### **Monthly**:
```
Bets: 70-90
Stake: ~£50
P&L: -£10 to +£15
Target ROI: +3%
```

### **2-Month Total (Nov-Dec)**:
```
Bets: 140-180
Stake: ~£100
Expected P&L: +£3-8 (if backtest holds)
ROI: +3-8%
```

**If you get +3% ROI after 160 bets**: ✅ Model works! Deploy with real money Q1 2026.

---

## 📋 **Tomorrow Morning Checklist (Oct 18, 8 AM)**

1. [ ] Run odds availability check (SQL query)
2. [ ] If odds ready: Run selection query
3. [ ] Review 0-3 bets
4. [ ] Log to spreadsheet:
   ```
   Date | Time | Course | Horse | Odds | Rank | Stake | [Result] | [P&L]
   ```
5. [ ] Set reminder to check results evening

**That's it!** 10 minutes of work.

---

## 🎯 **Summary**

| Your Question | Answer |
|---------------|--------|
| **What do I need for tomorrow?** | Odds from database (8 AM Oct 18) |
| **How to select bets?** | Run SQL query daily (provided) |
| **When to retrain?** | Jan 1, 2026 (annually) |
| **Use until year end?** | YES - then retrain Jan 1 |

---

## 📁 **Key Files to Read**

1. **`DAILY_WORKFLOW.md`** - Complete SQL queries for selections
2. **`DEPLOYMENT_GUIDE_HYBRID.md`** - Full deployment plan
3. **`YOUR_COMPLETE_ANSWER.md`** - All answers in detail

---

## 🚀 **Action Items for Right Now**

**Tonight (Oct 17)**:
- ✅ Read DAILY_WORKFLOW.md
- ✅ Create tracking spreadsheet
- ✅ Set 8 AM alarm

**Tomorrow (Oct 18, 8 AM)**:
- ✅ Check odds availability
- ✅ Run selection query
- ✅ Log bets (paper trading)

**That's all you need to start!** 🎯

