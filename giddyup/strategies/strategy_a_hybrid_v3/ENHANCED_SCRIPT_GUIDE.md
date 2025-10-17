# Enhanced Script: Bankroll + Auto-Tracking

**Script**: `get_tomorrows_bets_v2.sh`  
**New Features**: 
- ✅ Takes bankroll input
- ✅ Shows real £ stakes
- ✅ Exports to CSV automatically
- ✅ Generates database INSERT statements

---

## 🚀 Quick Usage

```bash
./get_tomorrows_bets_v2.sh 2025-10-18 5000
                          ↑           ↑
                          date     bankroll (£)
```

**Example**:
```bash
# With £5,000 bankroll
./get_tomorrows_bets_v2.sh 2025-10-18 5000

# With £10,000 bankroll
./get_tomorrows_bets_v2.sh 2025-10-18 10000

# With £1,000 bankroll (smaller)
./get_tomorrows_bets_v2.sh 2025-10-18 1000
```

---

## 📊 What You Get

### **1. Screen Output with Real £ Amounts**

```
================================================================================
🏇 HYBRID MODEL V3 - Bet Selections for 2025-10-18
================================================================================

💰 Bankroll: £5,000
📊 Unit Size: £50.00 (1% of bankroll)

================================================================================

 bet_num  | Time  | Course    | Horse         | Trainer    | Draw | Odds  | Rank | Market | Model  | Disagree | Edge   | Stake
----------|-------|-----------|---------------|------------|------|-------|------|--------|--------|----------|--------|-------
 🎯 BET #1| 14:30 | Ascot     | Thunder Road  | J. Gosden  |  5   | 9.50  |  4   | 10.5%  | 23.0%  | 2.19x    | 12.5pp | £0.75
 🎯 BET #2| 15:45 | Newmarket | Silver Storm  | A. OBrien  |  8   | 10.00 |  5   | 9.9%   | 19.8%  | 2.00x    | 9.9pp  | £0.60
 🎯 BET #3| 17:00 | Leopardstown| Celtic Dawn | J. Bolger  |  3   | 11.00 |  6   | 8.5%   | 15.3%  | 1.80x    | 6.8pp  | £0.50

================================================================================
 info       | total_bets | avg_odds | avg_rank | total_units | total_stake_gbp
------------|------------|----------|----------|-------------|----------------
 📊 SUMMARY |     3      |   10.17  |   5.0    |   0.037     | £1.85

Bankroll: £5,000 | Unit: £50.00
Expected Win Rate: ~11% | Expected ROI: +3.1%

CSV saved to: logs/bets/bets_2025-10-18.csv
```

**Notice**: Stake column now shows **real £ amounts** based on your bankroll!

---

### **2. CSV File for Spreadsheet** 📄

**File**: `logs/bets/bets_2025-10-18.csv`

```csv
race_date,race_time,course_name,horse_name,trainer_name,runner_num,odds,market_rank,market_pct,model_pct,disagree,edge_pp,stake_units,stake_gbp,result,pnl_gbp
2025-10-18,14:30,Ascot,Thunder Road,J. Gosden,5,9.50,4,10.5,23.0,2.19,12.5,0.015,0.75,,
2025-10-18,15:45,Newmarket,Silver Storm (IRE),A. OBrien,8,10.00,5,9.9,19.8,2.00,9.9,0.012,0.60,,
2025-10-18,17:00,Leopardstown,Celtic Dawn,J. Bolger,3,11.00,6,8.5,15.3,1.80,6.8,0.010,0.50,,
```

**Open in Excel/Google Sheets**:
- All bet details already filled in
- `result` column blank - fill in tonight (WON/LOST)
- `pnl_gbp` column blank - calculate after results

---

### **3. SQL Insert Statements** 🗄️

**File**: `logs/bets/bets_2025-10-18.sql`

```sql
-- Insert into modeling.signals for tracking

INSERT INTO modeling.signals (
    as_of, race_id, horse_id, model_id,
    p_win, fair_odds_win, best_odds_win, best_odds_src,
    edge_win, stake_units, liquidity_ok, reasons
)
SELECT 810443, 123456, 1, 0.2300, 4.35, 9.50, 'T-60', 0.1250, 0.015, TRUE, '{"disagreement":2.19,"rank":4}'::jsonb);
SELECT 810444, 123457, 1, 0.1980, 5.05, 10.00, 'T-60', 0.0990, 0.012, TRUE, '{"disagreement":2.00,"rank":5}'::jsonb);
SELECT 810445, 123458, 1, 0.1530, 6.54, 11.00, 'T-60', 0.0680, 0.010, TRUE, '{"disagreement":1.80,"rank":6}'::jsonb);
```

**To log to database**:
```bash
psql -U postgres -d horse_db < logs/bets/bets_2025-10-18.sql
```

---

## 💰 How Bankroll Works

### **Unit Calculation**

```
Unit Size = Bankroll × 1%

Examples:
  £1,000 bankroll → 1 unit = £10
  £5,000 bankroll → 1 unit = £50
  £10,000 bankroll → 1 unit = £100
```

**Why 1%?**
- Conservative (100 units = can handle drawdowns)
- Recommended for fractional Kelly
- Industry standard for value betting

---

### **Stake Calculation**

```
Typical bet: 0.010-0.020 units (1-2% of a unit)
Max bet: 0.300 units (30% of a unit)

With £5,000 bankroll (£50/unit):
  Typical: 0.015 units = £0.75
  Larger: 0.025 units = £1.25
  Max: 0.300 units = £15.00
```

---

## 📊 Different Bankroll Examples

### **Conservative: £1,000 Bankroll**

```bash
./get_tomorrows_bets_v2.sh 2025-10-18 1000

Unit: £10
Typical bet: £0.15-0.20
Daily stake: £0.30-0.60
Monthly stake: ~£10
Expected monthly P&L: £0.30-0.50
```

**Good for**: Testing, learning, small stakes

---

### **Moderate: £5,000 Bankroll** ⭐ **RECOMMENDED**

```bash
./get_tomorrows_bets_v2.sh 2025-10-18 5000

Unit: £50
Typical bet: £0.75-1.00
Daily stake: £1.50-3.00
Monthly stake: ~£50
Expected monthly P&L: £1.50-2.50
```

**Good for**: Serious paper trading → small live deployment

---

### **Larger: £10,000 Bankroll**

```bash
./get_tomorrows_bets_v2.sh 2025-10-18 10000

Unit: £100
Typical bet: £1.50-2.00
Daily stake: £3-6
Monthly stake: ~£100
Expected monthly P&L: £3-5
```

**Good for**: Established profitable track record only

---

## 📝 Daily Workflow with Enhanced Script

### **Morning (8:00 AM)**

```bash
cd /home/smonaghan/GiddyUpModel/giddyup/profitable_models/hybrid_v3

# Run with your bankroll
./get_tomorrows_bets_v2.sh 2025-10-18 5000

# Review output
# CSV automatically created in logs/bets/
```

---

### **Import to Spreadsheet**

```bash
# Open the CSV
open logs/bets/bets_2025-10-18.csv

# Or import to Google Sheets:
# File → Import → Upload → logs/bets/bets_2025-10-18.csv
```

**Spreadsheet has**:
- Date, time, course, horse
- Odds, rank, probabilities
- Stake in £
- **Empty columns**: result, pnl_gbp (fill in tonight)

---

### **Evening (After Racing)**

**Update spreadsheet**:

| result | pnl_gbp | How to calculate |
|--------|---------|------------------|
| WON | +7.33 | (£0.75 × 9.50 × 0.98) - £0.75 = +£6.98 - £0.75 = +£6.23 |
| LOST | -0.75 | Just the stake lost |

**Or simpler**:
- WON: `stake_gbp × (odds - 1) × 0.98`
- LOST: `-stake_gbp`

---

### **(Optional) Log to Database**

```bash
# Insert bets into modeling.signals
psql -U postgres -d horse_db < logs/bets/bets_2025-10-18.sql
```

**Why log to database**:
- Permanent record
- Can query/analyze later
- Track signals over time
- Compare predictions to results

---

## 🔄 Updating Results Later

### **Option A: Manual (Spreadsheet)**

1. Open `logs/bets/bets_2025-10-18.csv`
2. Check which horses won
3. Fill in `result` column (WON/LOST)
4. Calculate `pnl_gbp`:
   ```
   If WON: =(stake_gbp × (odds - 1) × 0.98)
   If LOST: =-stake_gbp
   ```
5. Sum `pnl_gbp` column for daily total

---

### **Option B: Database Query**

```sql
-- Update with results from racing.runners
UPDATE modeling.signals s
SET 
    outcome = CASE WHEN ru.pos_num = 1 THEN 'won' ELSE 'lost' END,
    pnl = CASE 
        WHEN ru.pos_num = 1 THEN stake_units * (best_odds_win - 1) * 0.98
        ELSE -stake_units
    END
FROM racing.runners ru
WHERE s.race_id = ru.race_id
AND s.horse_id = ru.horse_id
AND s.as_of::date = '2025-10-18';

-- Then export to update CSV
\copy (SELECT * FROM modeling.signals WHERE as_of::date = '2025-10-18') TO 'results_2025-10-18.csv' CSV HEADER
```

---

## 📊 Weekly/Monthly Summaries

### **Query Your CSV Files**

```python
import pandas as pd
import glob

# Load all October bets
files = glob.glob('logs/bets/bets_2025-10-*.csv')
df = pd.concat([pd.read_csv(f) for f in files])

# Summary
print(f"Total bets: {len(df)}")
print(f"Total stake: £{df['stake_gbp'].sum():.2f}")
print(f"Total P&L: £{df['pnl_gbp'].sum():.2f}")
print(f"ROI: {df['pnl_gbp'].sum() / df['stake_gbp'].sum() * 100:.1f}%")
```

---

## 🎯 Example: Full Day Workflow

### **Morning (Oct 18, 8:00 AM)**

```bash
$ cd profitable_models/hybrid_v3
$ ./get_tomorrows_bets_v2.sh 2025-10-18 5000

Output:
  3 bets found
  Total stake: £1.85
  CSV: logs/bets/bets_2025-10-18.csv
  SQL: logs/bets/bets_2025-10-18.sql

$ open logs/bets/bets_2025-10-18.csv  # Opens in Excel/Sheets
```

**Spreadsheet shows**:
```
| Time  | Course | Horse         | Odds | Stake | result | pnl_gbp |
|-------|--------|---------------|------|-------|--------|---------|
| 14:30 | Ascot  | Thunder Road  | 9.50 | £0.75 |        |         |
| 15:45 | Newmarket| Silver Storm| 10.00| £0.60 |        |         |
| 17:00 | Leopardstown|Celtic Dawn|11.00| £0.50 |        |         |
```

---

### **During Day (Paper Trading)**

- Review the 3 bets
- Note them (don't place real money yet)
- Watch races if interested

---

### **Evening (After Racing)**

**Check results** (racing websites, Betfair, etc.):
- Thunder Road: Finished 2nd → LOST
- Silver Storm: WON → +£5.28
- Celtic Dawn: Finished 4th → LOST

**Update spreadsheet**:
```
| Time  | Course  | Horse        | Odds  | Stake | result | pnl_gbp |
|-------|---------|--------------|-------|-------|--------|---------|
| 14:30 | Ascot   | Thunder Road | 9.50  | £0.75 | LOST   | -0.75   |
| 15:45 | Newmarket|Silver Storm | 10.00 | £0.60 | WON    | +5.28   |
| 17:00 | Leopardstown|Celtic Dawn|11.00 | £0.50 | LOST   | -0.50   |
|       |         |              |       | TOTAL | 1/3    | +£4.03  |
```

**Day P&L**: +£4.03 ✅ (good day!)

---

### **(Optional) Log to Database**

```bash
psql -U postgres -d horse_db < logs/bets/bets_2025-10-18.sql
```

Now your bets are in `modeling.signals` table for long-term tracking.

---

## 💡 Benefits of Enhanced Script

### **Before (Original)**:
```
❌ Shows generic "0.015 units"
❌ You calculate £ amount manually
❌ Manual CSV creation
❌ Manual database logging
```

### **After (Enhanced)**:
```
✅ Shows actual £ amounts (£0.75, £0.60, etc.)
✅ Automatically adjusts to YOUR bankroll
✅ Auto-generates CSV for spreadsheet
✅ Auto-generates SQL for database
✅ Just import and you're done!
```

---

## 📊 Bankroll Recommendations

### **By Experience Level**

| Experience | Bankroll | Unit | Typical Bet | Monthly Risk |
|------------|----------|------|-------------|--------------|
| **Testing** | £500 | £5 | £0.08-0.15 | £3-5 |
| **Learning** | £1,000 | £10 | £0.15-0.30 | £6-10 |
| **Paper Trading** | £5,000 | £50 | £0.75-1.50 | £30-50 |
| **Small Live** | £5,000 | £50 | £0.75-1.50 | £30-50 |
| **Established** | £10,000 | £100 | £1.50-3.00 | £60-100 |

**Start small!** Even with £10k, use £5k bankroll initially.

---

## 📁 Output Files Location

```
logs/
└── bets/
    ├── bets_2025-10-18.csv    # Spreadsheet import
    ├── bets_2025-10-18.sql    # Database logging
    ├── bets_2025-10-19.csv
    ├── bets_2025-10-19.sql
    └── ...one file per day
```

**After 1 month**: 60 CSV files (one per day)

**To analyze all November bets**:
```bash
cat logs/bets/bets_2025-11-*.csv > november_all_bets.csv
```

---

## 🎯 Comparison

### **Original Script**

```bash
./get_tomorrows_bets.sh 2025-10-18

Output:
  Stake: 0.015 units (~£0.75 with £50 units)
          ↑
  Generic, you calculate manually
```

**Use when**: Quick check, don't need exact amounts

---

### **Enhanced Script** ⭐

```bash
./get_tomorrows_bets_v2.sh 2025-10-18 5000
                                        ↑
                                   your bankroll

Output:
  Stake: £0.75
         ↑
  Exact amount for YOUR bankroll
  + Auto CSV
  + Auto SQL
```

**Use when**: 
- Paper trading (tracking required)
- Real trading (need exact amounts)
- Want automatic record-keeping

---

## 🚀 Recommended: Use Enhanced Script

**For Nov-Dec paper trading**:

```bash
# Every morning
./get_tomorrows_bets_v2.sh $(date -d tomorrow +%Y-%m-%d) 5000

# Automatically:
#   - Shows £ stakes
#   - Creates CSV
#   - Generates SQL
#   - Ready to track!
```

**Much easier than manual tracking!**

---

## 📋 Summary

| Feature | Original | Enhanced |
|---------|----------|----------|
| Takes bankroll input | ❌ | ✅ |
| Shows real £ amounts | ❌ | ✅ |
| Auto-generates CSV | ❌ | ✅ |
| Auto-generates SQL | ❌ | ✅ |
| Easy import to sheets | ❌ | ✅ |
| Database logging ready | ❌ | ✅ |

**Recommendation**: **Use enhanced version** (`get_tomorrows_bets_v2.sh`) for all paper trading and beyond!

---

**Try it tomorrow**: `./get_tomorrows_bets_v2.sh 2025-10-18 5000` 🎯

