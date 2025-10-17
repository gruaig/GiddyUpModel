# 📋 Daily Workflow - Both Strategies

**Complete step-by-step guide for running both strategies every day**

**By**: Sean MoonBoots  
**Date**: October 17, 2025

---

## ✅ **YES - Both Strategies Use T-60!**

**BOTH strategies use the exact same timing**:
- ⏰ **T-60** (60 minutes before race off time)
- 📊 Same exchange prices (Betfair `win_ppwap`)
- 🎯 Same workflow (just different bets)

**The ONLY difference**: **Which bets they select**
- **Strategy A**: Rank 3-6 (mid-field by betting)
- **Strategy B**: Odds 7-16 with 15pp+ edge

---

## 🚀 **One Command, Both Strategies**

### **Morning Run** (8:00 AM):

```bash
cd /home/smonaghan/GiddyUpModel/giddyup/strategies
./RUN_BOTH_STRATEGIES.sh 2025-10-18 5000
```

**What this does**:
1. ✅ Runs Strategy A selection
2. ✅ Runs Strategy B selection  
3. ✅ Creates ONE spreadsheet with both
4. ✅ Adds reasoning for each bet
5. ✅ Shows what to check at T-60
6. ✅ Appends to ongoing log (doesn't overwrite)

**Time**: 2 minutes

---

## 📊 **Spreadsheet Columns Explained**

The script creates a CSV with these columns:

| Column # | Name | What It Is | Who Fills It |
|----------|------|------------|--------------|
| 1 | `date` | Race date (2025-10-18) | ✅ Script |
| 2 | `time` | Race time (14:30) | ✅ Script |
| 3 | `course` | Course name (Ascot) | ✅ Script |
| 4 | `horse` | Horse name (Thunder Road) | ✅ Script |
| 5 | `trainer` | Trainer name | ✅ Script |
| 6 | `odds` | Current odds (8am) | ✅ Script |
| 7 | `strategy` | A-Hybrid_V3 or B-Path_B | ✅ Script |
| 8 | `reasoning` | WHY bet (edge, disagree, etc.) | ✅ Script |
| 9 | `min_odds_needed` | Minimum at T-60 (9.0) | ✅ Script |
| 10 | **`t60_actual_odds`** | **What odds were at T-60** | **⏳ YOU FILL** |
| 11 | **`action_taken`** | **BET or SKIP** | **⏳ YOU FILL** |
| 12 | `stake_gbp` | Stake amount (£0.75) | ✅ Script |
| 13 | **`result`** | **WON or LOST** | **⏳ YOU FILL (evening)** |
| 14 | **`pnl_gbp`** | **Profit/loss** | **⏳ YOU FILL (evening)** |

**Script fills 9 columns, you fill 4 columns throughout the day** ✅

---

## 📝 **Complete Daily Workflow**

### **STEP 1: Morning (8:00 AM) - 10 minutes**

```bash
cd /home/smonaghan/GiddyUpModel/giddyup/strategies
./RUN_BOTH_STRATEGIES.sh 2025-10-18 5000
```

**Output shows**:
```
═══════════════════════════════════════════════════════════════════════════════
🎯 STRATEGY A: HYBRID V3
═══════════════════════════════════════════════════════════════════════════════

  #  | Time  | Course | Horse         | Odds | Why Betting | Action at T-60 | Stake
-----|-------|--------|---------------|------|-------------|----------------|-------
  1  | 14:30 | Ascot  | Thunder Road  | 9.50 | Rank 4 of 12| If ≥9.0 → BET | £0.75
                                              | Disagree 2.5x
                                              | Edge +12pp
                                              
═══════════════════════════════════════════════════════════════════════════════
💎 STRATEGY B: PATH B
═══════════════════════════════════════════════════════════════════════════════

  #  | Time  | Course    | Horse        | Odds | Why Betting | Action at T-60 | Stake
-----|-------|-----------|--------------|------|-------------|----------------|-------
  1  | 16:00 | Newmarket | Storm King   | 8.20 | Odds 8.2   | If ≥7.4 → BET | £2.00
                                               | Edge +17pp
                                               | EV +8%
```

**Action**: Import CSV to spreadsheet, set T-60 alerts

---

### **STEP 2: At T-60 for Each Race** - 2 min per race

**Example**: 14:30 race (Thunder Road from Strategy A)

#### **13:30 (T-60 - 60 minutes before 14:30 off)**:

1. **Open Betfair** on phone/computer
2. **Find race**: Ascot 14:30
3. **Find horse**: Thunder Road
4. **Check current odds**: Shows 10.2

5. **Open spreadsheet**, find Thunder Road row:
   ```
   Fill column 10 't60_actual_odds': 10.2
   ```

6. **Compare**: 
   ```
   Actual: 10.2
   Minimum needed: 9.0 (from column 9)
   
   10.2 >= 9.0? YES ✅
   ```

7. **Fill column 11 'action_taken'**: `BET`

8. **Place bet on Betfair**:
   ```
   Horse: Thunder Road
   Odds: 10.2 (or best available)
   Stake: £0.75 (from column 12)
   ```

9. **Done for this race!**

---

#### **If Odds Steamed Off**:

**Example**: Storm King at 16:00 (Strategy B)

**15:00 (T-60)**:
1. Check Betfair: Storm King shows 6.8 odds
2. Minimum needed: 7.4 (from column 9)
3. Compare: 6.8 < 7.4 ❌
4. Fill spreadsheet:
   ```
   Column 10 't60_actual_odds': 6.8
   Column 11 'action_taken': SKIP
   ```
5. **Do NOT bet** - edge is gone
6. Leave columns 13-14 blank (no bet placed)

---

### **STEP 3: Evening (After Racing) - 5 minutes**

**For each BET placed** (not SKIP):

1. **Check results** (Racing Post, Betfair, etc.)

2. **Fill column 13 'result'**:
   - Horse won → `WON`
   - Horse lost → `LOST`

3. **Calculate column 14 'pnl_gbp'**:

**If WON**:
```
Formula: stake × (odds - 1) × 0.98

Example:
  Thunder Road: £0.75 stake × (10.2 - 1) × 0.98
              = £0.75 × 9.2 × 0.98
              = £6.76 profit
              
Fill: +6.76
```

**If LOST**:
```
Formula: -stake

Example:
  Thunder Road: -£0.75
  
Fill: -0.75
```

**If SKIP**:
```
Leave blank (no bet placed)
```

4. **Sum column 14** at bottom for daily P&L

---

## 📊 **Example: Full Day**

### **Morning Output**:
```
Strategy A: 3 bets found
Strategy B: 1 bet found
Total: 4 bets for today
```

### **Spreadsheet After Morning**:

| time | course | horse | odds | strategy | reasoning | min_odds | t60_actual | action | stake | result | pnl |
|------|--------|-------|------|----------|-----------|----------|------------|--------|-------|--------|-----|
| 14:30| Ascot |Thunder Road|9.50|A-Hybrid_V3|Rank 4, Disagree 2.5x, Edge +12pp|9.0| | |£0.75| | |
| 15:45|Newmarket|Silver Storm|10.00|A-Hybrid_V3|Rank 5, Disagree 2.0x, Edge +10pp|9.5| | |£0.60| | |
| 16:00|York|Storm King|8.20|B-Path_B|Odds 8.2, Edge +17pp, EV +8%|7.4| | |£2.00| | |
| 17:30|Leopardstown|Celtic Dawn|11.00|A-Hybrid_V3|Rank 6, Disagree 1.8x, Edge +7pp|10.5| | |£0.50| | |

**Columns 10-14 are blank - YOU fill these throughout the day**

---

### **At T-60 for Each Race** (You Fill):

**13:30 (Thunder Road)**:
- Check Betfair: 10.2 odds ✅
- Fill: `t60_actual_odds` = 10.2
- 10.2 >= 9.0 → BET ✅
- Fill: `action_taken` = BET
- Place bet: £0.75 @ 10.2

**14:45 (Silver Storm)**:
- Check Betfair: 8.5 odds ❌
- Fill: `t60_actual_odds` = 8.5
- 8.5 < 9.5 → SKIP ❌
- Fill: `action_taken` = SKIP
- DO NOT bet

**15:00 (Storm King)**:
- Check Betfair: 8.8 odds ✅
- Fill: `t60_actual_odds` = 8.8
- 8.8 >= 7.4 → BET ✅
- Fill: `action_taken` = BET
- Place bet: £2.00 @ 8.8

**16:30 (Celtic Dawn)**:
- Check Betfair: 11.5 odds ✅
- Fill: `t60_actual_odds` = 11.5
- 11.5 >= 10.5 → BET ✅
- Fill: `action_taken` = BET
- Place bet: £0.50 @ 11.5

---

### **Evening Results** (You Fill):

**Check race results**:
- Thunder Road: Finished 2nd → LOST
- Silver Storm: N/A (skipped)
- Storm King: WON ✅
- Celtic Dawn: Finished 4th → LOST

**Fill results & calculate P&L**:

| horse | action | t60_odds | stake | result | pnl_gbp |
|-------|--------|----------|-------|--------|---------|
| Thunder Road | BET | 10.2 | £0.75 | LOST | -0.75 |
| Silver Storm | SKIP | 8.5 | - | - | - |
| Storm King | BET | 8.8 | £2.00 | WON | +15.02 |
| Celtic Dawn | BET | 11.5 | £0.50 | LOST | -0.50 |

**Daily totals**:
```
Bets placed: 3 (1 skipped)
Total stake: £3.25
Total P&L: +£13.77 ✅ (good day!)

By strategy:
  Strategy A: 2 bets, -£1.25 P&L
  Strategy B: 1 bet, +£15.02 P&L
```

---

## ⏰ **T-60 Timing - SAME FOR BOTH**

### **What is T-60?**

```
T-60 = 60 minutes before scheduled race off time

Example race times:
  10:15 off → T-60 = 09:15
  14:30 off → T-60 = 13:30
  17:00 off → T-60 = 16:00
```

### **Why T-60 for Both?**

**Both models calibrated on T-60 prices**:
- ✅ Strategy A: Trained on `win_ppwap` (T-60 snapshot)
- ✅ Strategy B: Same data, same timing
- ✅ Backtests use T-60 prices
- ✅ To match backtest results → use T-60

**Both strategies need T-60, not morning or late!**

---

## 📱 **Recommended: Mobile Workflow**

### **Morning (Laptop)**:
```
1. Run: ./RUN_BOTH_STRATEGIES.sh 2025-10-18 5000
2. Import CSV to Google Sheets
3. Review bets, set T-60 alerts on phone
```

### **Throughout Day (Phone)**:
```
For each T-60 alert:
1. Open Betfair app
2. Find race, find horse
3. Check odds
4. Text yourself or note:
   "Thunder Road: 10.2 odds, BET"
```

### **Evening (Laptop)**:
```
1. Update spreadsheet:
   - Fill t60_actual_odds (from your notes)
   - Fill action_taken (BET/SKIP)
   - Fill result (WON/LOST)
   - Calculate pnl_gbp
2. Review daily P&L
3. Done!
```

**Total time**: ~30 min/day

---

## 🎯 **Strategy Differences at T-60**

### **Strategy A** (More Lenient):

```
Morning shows: 9.50 odds
Minimum needed: 9.0 (5% buffer)

At T-60:
  ✅ 9.2 odds → BET (still above 9.0)
  ✅ 10.5 odds → BET (even better!)
  ❌ 8.8 odds → SKIP (below 9.0)
```

**Typically 70%** of morning selections still qualify at T-60

---

### **Strategy B** (Stricter):

```
Morning shows: 8.20 odds
Minimum needed: 7.4 (10% buffer)

At T-60:
  ✅ 7.8 odds → BET (above 7.4)
  ✅ 9.0 odds → BET (even better!)
  ❌ 7.0 odds → SKIP (below 7.4)
```

**Typically 60%** of morning selections still qualify at T-60  
(More selective = more steam-offs)

---

## 📋 **Spreadsheet Template**

After running the script, your CSV will look like:

```csv
date,time,course,horse,trainer,odds,strategy,reasoning,min_odds_needed,t60_actual_odds,action_taken,stake_gbp,result,pnl_gbp
2025-10-18,14:30,Ascot,Thunder Road,J. Gosden,9.50,A-Hybrid_V3,"Rank 4 of 12 | Disagree 2.5x | Edge +12pp",9.0,,,0.75,,
2025-10-18,16:00,York,Storm King,A. OBrien,8.20,B-Path_B,"Odds 8.2 | Edge +17pp | EV +8%",7.4,,,2.00,,
```

**You fill columns 10-14 (t60_actual_odds, action_taken, result, pnl_gbp)**

---

## ✅ **Daily Checklist**

### **Morning**:
- [ ] Run `./RUN_BOTH_STRATEGIES.sh 2025-10-18 5000`
- [ ] Import CSV to spreadsheet
- [ ] Review bets (4-6 total)
- [ ] Set T-60 alerts for each race
- [ ] Note: Strategy A = ranks, Strategy B = high edge

### **At T-60 (Each Race)**:
- [ ] Open Betfair
- [ ] Find race & horse
- [ ] Check current odds
- [ ] Fill spreadsheet: `t60_actual_odds`
- [ ] Compare to `min_odds_needed`
- [ ] If >= min → BET, fill `action_taken` = BET
- [ ] If < min → SKIP, fill `action_taken` = SKIP
- [ ] Place bet if BET

### **Evening**:
- [ ] Check which horses won
- [ ] Fill `result` column (WON/LOST for bets placed)
- [ ] Calculate `pnl_gbp`:
  - WON: stake × (odds - 1) × 0.98
  - LOST: -stake
  - SKIP: blank
- [ ] Sum P&L for daily total
- [ ] Track by strategy

---

## 💡 **Key Points**

### **1. Both Strategies = T-60**
```
✅ Strategy A at T-60 (60 min before off)
✅ Strategy B at T-60 (60 min before off)

SAME timing! Just different bets.
```

### **2. Different Buffers**
```
Strategy A: 5% buffer (9.50 → need 9.0)
Strategy B: 10% buffer (8.20 → need 7.4)

B is stricter = fewer bets but higher edge
```

### **3. Track Separately**
```
Spreadsheet has 'strategy' column:
  - A-Hybrid_V3
  - B-Path_B

Can analyze each strategy's performance separately!
```

### **4. Many Days Zero for Strategy B**
```
Strategy A: 3-4 bets most days
Strategy B: 0-2 bets (many days ZERO)

This is NORMAL for Strategy B!
High selectivity = high ROI
```

---

## 📊 **Example: Full Week**

| Day | Strategy A Bets | Strategy B Bets | Total | Combined P&L |
|-----|----------------|----------------|-------|--------------|
| Mon | 4 | 1 | 5 | +£2.50 |
| Tue | 3 | 0 | 3 | -£0.80 |
| Wed | 4 | 2 | 6 | +£15.20 |
| Thu | 3 | 1 | 4 | +£3.10 |
| Fri | 5 | 0 | 5 | -£1.50 |
| Sat | 6 | 2 | 8 | +£18.60 |
| Sun | 2 | 0 | 2 | +£0.90 |
| **Total** | **27** | **6** | **33** | **+£38.00** |

**Notice**:
- Strategy A: Every day (steady)
- Strategy B: Only 4/7 days (selective)
- Combined: Excellent weekly result!

---

## 🎯 **Quick Reference Card**

```
═══════════════════════════════════════════════════════════════════════════════
DAILY ROUTINE - BOTH STRATEGIES

MORNING (8am - 10 min):
  ./RUN_BOTH_STRATEGIES.sh 2025-10-18 5000
  Import CSV, set T-60 alerts

AT T-60 (Each race - 2 min):
  1. Betfair → Find race & horse
  2. Check current odds
  3. Spreadsheet: Fill t60_actual_odds
  4. If >= min_odds_needed → BET (fill action_taken = BET)
  5. If < min_odds_needed → SKIP (fill action_taken = SKIP)
  6. Place bet if BET

EVENING (After racing - 5 min):
  1. Check results
  2. Fill result (WON/LOST)
  3. Calculate pnl_gbp:
     WON: stake × (odds - 1) × 0.98
     LOST: -stake
  4. Sum daily P&L

BOTH STRATEGIES USE T-60! ⏰
═══════════════════════════════════════════════════════════════════════════════
```

---

## 📁 **Files Created Daily**

```
logs/daily_bets/
├── betting_log_2025.csv          Master log (appends daily)
└── quick_ref_2025-10-18.txt      Today's quick reference
```

**Master CSV grows over time**:
- Nov 1: 4 bets
- Nov 2: +5 bets = 9 total
- Nov 3: +3 bets = 12 total
- ...
- Dec 31: ~220 bets total (60 days)

**All in one file!** Easy monthly/annual analysis.

---

## ✅ **Summary**

**Both strategies**:
- ⏰ Use T-60 timing (60 min before off)
- 📊 Use Betfair exchange prices
- 🎯 Same workflow (just different bets)
- 📋 Track in ONE spreadsheet

**Your job at T-60**:
1. Check Betfair odds
2. Fill spreadsheet (actual odds, action)
3. Bet if odds >= minimum

**Simple, systematic, repeatable!** 🎯

---

**By**: Sean MoonBoots  
**File**: `strategies/RUN_BOTH_STRATEGIES.sh`  
🏇 **One command, both strategies, complete tracking!** 🏇

