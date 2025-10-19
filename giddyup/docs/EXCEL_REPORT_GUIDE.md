# 📊 HorseBot Excel Report Guide

## 🎯 What You Get

After running the bot, you'll automatically get a **formatted Excel file** with:
- ✅ Color-coded rows (green = bet placed)
- ✅ PNL tracking with auto-calculations
- ✅ Running total PNL
- ✅ Daily summary sheet
- ✅ Price movement tracking

---

## 📁 File Location

**Automatically created at end of bot session:**
```
strategies/logs/automated_bets/betting_report_2025-10-18.xlsx
```

---

## 📋 Sheet 1: Betting Log

### Column Layout

| Column | Name | Description |
|--------|------|-------------|
| A | Time | Race time (UK) |
| B | Course | Race course |
| C | Horse | Horse name |
| D | Strategy | A-Hybrid_V3 or B-Path_B |
| E | Expected | Expected odds (when strategy ran) |
| F | Min | Minimum odds to bet |
| G | Actual | Actual odds at T-60 |
| H | Stake | Bet stake (£) |
| I | Bet? | DRY_RUN / EXECUTED / NO |
| J | Bet ID | Betfair bet ID |
| K | Reason | Why placed/skipped |
| **L** | **Result** | **Manual entry: WIN or LOSS** |
| **M** | **PNL** | **Auto-calculated** |
| **N** | **Running PNL** | **Running total** |

### Color Coding

🟢 **Green rows** = Bet was placed (DRY_RUN or EXECUTED)  
🟡 **Yellow rows** = Market found but skipped  
⬜ **White rows** = Market not found  

### Example

```
┌──────┬──────────┬────────────────────┬────────────┬──────────┬──────┬────────┬───────┬──────────┬─────────────┬─────────────────┬────────┬───────┬────────────┐
│ Time │ Course   │ Horse              │ Strategy   │ Expected │ Min  │ Actual │ Stake │ Bet?     │ Bet ID      │ Reason          │ Result │ PNL   │ Running    │
├──────┼──────────┼────────────────────┼────────────┼──────────┼──────┼────────┼───────┼──────────┼─────────────┼─────────────────┼────────┼───────┼────────────┤
│10:30 │Catterick │Arctic Fox (GB)     │A-Hybrid_V3 │ 8.20     │ 7.79 │ 8.80   │ 0.75  │ DRY_RUN  │DRY_17292... │DRY_RUN @ 8.80   │ WIN    │ +5.85 │ +5.85      │ GREEN
│10:30 │Catterick │Wasthatok (GB)      │B-Path_B    │ 9.00     │ 8.10 │ 7.85   │ 2.00  │ NO       │             │Odds too low     │        │       │            │
│11:00 │Catterick │Eagle Bay (IRE)     │A-Hybrid_V3 │ 7.40     │ 7.03 │ 11.00  │ 0.75  │ DRY_RUN  │DRY_17292... │DRY_RUN @ 11.00  │ LOSS   │ -0.75 │ +5.10      │ GREEN
└──────┴──────────┴────────────────────┴────────────┴──────────┴──────┴────────┴───────┴──────────┴─────────────┴─────────────────┴────────┴───────┴────────────┘
```

---

## 💰 PNL Calculation (Automatic!)

### When You Enter "WIN" in Result Column:
```
PNL = (Actual Odds × Stake) - Stake
Example: (8.80 × £0.75) - £0.75 = £6.60 - £0.75 = £5.85
```

### When You Enter "LOSS" in Result Column:
```
PNL = -Stake
Example: -£0.75
```

### Running PNL:
```
Automatically sums all PNL above current row
Shows cumulative profit/loss for the day
```

---

## 📈 Sheet 2: Daily Summary

Auto-calculates:

```
🏇 Betting Summary - 2025-10-18

📋 Overview
Total Selections:     57
Bets Placed:          12
Bets Skipped:         45

💰 Stakes
Total Staked:         £15.75
Average Stake:        £1.31

📊 Results (Fill in manually)
Wins:                 3      ← Auto-counts "WIN" entries
Losses:               8      ← Auto-counts "LOSS" entries
Pending:              1

💵 Profit & Loss
Total PNL:            +£2.35  ← Auto-calculated
ROI:                  +14.9%  ← Auto-calculated
Win Rate:             27.3%   ← Auto-calculated

🎯 Strategy Breakdown
Strategy A Bets:      8
Strategy B Bets:      4
```

---

## 📊 Sheet 3: Price Movements

Shows all price checks (every 5 minutes):

```
┌──────────────────────┬───────────┬──────────┬────────────────────┬─────────┬────────┬────────────┐
│ Timestamp            │ Race Time │ Course   │ Horse              │ T-Mins  │ Odds   │ Status     │
├──────────────────────┼───────────┼──────────┼────────────────────┼─────────┼────────┼────────────┤
│2025-10-18 07:00:00   │ 11:00     │Catterick │Arctic Fox (GB)     │ 240.0   │ 10.50  │ TRACKING   │
│2025-10-18 07:05:00   │ 11:00     │Catterick │Arctic Fox (GB)     │ 235.0   │ 10.00  │ TRACKING   │
│2025-10-18 09:00:00   │ 11:00     │Catterick │Arctic Fox (GB)     │  60.0   │ 8.80   │ BET_WINDOW │ YELLOW
│2025-10-18 09:05:00   │ 11:00     │Catterick │Arctic Fox (GB)     │  55.0   │ 8.90   │ BET_WINDOW │ YELLOW
└──────────────────────┴───────────┴──────────┴────────────────────┴─────────┴────────┴────────────┘
```

🟡 **Yellow rows** = Within betting window (T-60 to T-5)

---

## 📝 Daily Workflow

### 1. Run the Bot
```bash
python3 HorseBot_Simple.py 2025-10-18 5000
```

Bot runs all day, then auto-generates Excel report at end.

### 2. Open Excel File
```bash
# Open with LibreOffice (Linux)
libreoffice strategies/logs/automated_bets/betting_report_2025-10-18.xlsx

# Or copy to your computer and open in Excel
```

### 3. Fill in Results

For each **green row** (bet placed):
1. Check race result
2. Enter **"WIN"** or **"LOSS"** in column L (Result)
3. PNL auto-calculates!

### 4. Check Summary

Go to **"Daily Summary"** sheet to see:
- Total PNL
- ROI %
- Win rate
- Strategy breakdown

---

## 📊 Manual Report Generation

If you want to regenerate the report after updating results:

```bash
python3 generate_betting_report.py 2025-10-18
```

This recreates the Excel file from the CSV logs.

---

## 💡 Pro Tips

### Track Multiple Days

Each day gets its own Excel file:
```
betting_report_2025-10-18.xlsx
betting_report_2025-10-19.xlsx
betting_report_2025-10-20.xlsx
```

### Weekly Analysis

Create a master spreadsheet that imports from all daily files to track:
- Weekly PNL
- Strategy performance over time
- Best days/courses

### Quick PNL Check

Just open the Excel file and look at:
- **Last row of Running PNL column** = Total for day
- **Daily Summary sheet** = Full breakdown

---

## 🎨 Excel Features

### Conditional Formatting (Already Applied)
- ✅ Green = Bets executed
- ✅ Yellow = In betting window
- ✅ Borders on all cells

### Auto-Calculations
- ✅ PNL per bet
- ✅ Running total
- ✅ Summary statistics
- ✅ Win rate
- ✅ ROI percentage

### Filters (You Can Add)
- Filter by strategy
- Filter by course
- Filter by result
- Sort by PNL

---

## 🚀 Example Session

```bash
# Morning: Run bot
python3 HorseBot_Simple.py 2025-10-18 5000

# ... bot runs all day ...

# End of day:
[18:30:00] ✅ SESSION COMPLETE
[18:30:01] 📊 Generating Excel report...
[18:30:02] ✅ Report generated: betting_report_2025-10-18.xlsx

# Open Excel
libreoffice strategies/logs/automated_bets/betting_report_2025-10-18.xlsx

# Fill in WIN/LOSS for each green row
# Check Daily Summary for totals!
```

---

## 📈 What It Looks Like

### Green Row (Bet Placed - WIN)
```
10:30 | Catterick | Arctic Fox | A-Hybrid_V3 | 8.20 | 7.79 | 8.80 | 0.75 | DRY_RUN | DRY_... | WIN | +5.85 | +5.85
```
*Background: Light Green* 🟢

### Green Row (Bet Placed - LOSS)
```
11:00 | Catterick | Eagle Bay | A-Hybrid_V3 | 7.40 | 7.03 | 11.00 | 0.75 | DRY_RUN | DRY_... | LOSS | -0.75 | +5.10
```
*Background: Light Green* 🟢

### White Row (Skipped - Odds Too Low)
```
10:30 | Catterick | Wasthatok | B-Path_B | 9.00 | 8.10 | 7.85 | 2.00 | NO |  | Odds too low |  |  |
```
*Background: White* ⬜

---

**After every session, you get a beautiful Excel file ready for result entry and PNL tracking!** 📊✨



