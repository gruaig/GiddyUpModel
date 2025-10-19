# Example: What the Script Shows You

**Script**: `get_tomorrows_bets.sh`  
**Shows**: Race time, course, horse name, odds (price), and stake

---

## 📺 **Example Output for Oct 18, 2025**

When you run:
```bash
cd profitable_models/hybrid_v3
./get_tomorrows_bets.sh 2025-10-18
```

**You get this**:

```
================================================================================
🏇 HYBRID MODEL V3 - Bet Selections for 2025-10-18
================================================================================

📊 Data Availability Check
 status                    | total_runners | have_odds | pct_ready
---------------------------|---------------|-----------|----------
 ✅ Data ready             |     489       |    467    | 95%

================================================================================

 bet_num  | race_time | race                          | selection                           | details              | price              | probabilities            | value                    | stake
----------|-----------|-------------------------------|-------------------------------------|----------------------|--------------------|--------------------------|--------------------------|--------
 🎯 BET #1| 14:30     | Ascot - (Class 2)            | Thunder Road (J. Gosden)            | #5 | 4yo | 130lbs   | 9.50 odds (Rank 4) | 10.5% mkt → 23.0% model | 2.19x | +12.5pp edge    | 0.015 units (~£0.75)
 🎯 BET #2| 15:45     | Newmarket - (Grade 3)        | Silver Storm (IRE) (A. OBrien)      | #8 | 3yo | 126lbs   | 10.00 odds (Rank 5)| 9.9% mkt → 19.8% model  | 2.00x | +9.9pp edge     | 0.012 units (~£0.60)
 🎯 BET #3| 17:00     | Leopardstown - (Grade 2)     | Celtic Dawn (J. Bolger)             | #3 | 4yo | 128lbs   | 11.00 odds (Rank 6)| 8.5% mkt → 15.3% model  | 1.80x | +6.8pp edge     | 0.010 units (~£0.50)

================================================================================
 info       | total_bets | avg_odds | avg_rank | total_stake
------------|------------|----------|----------|-------------
 📊 SUMMARY |     3      |   10.17  |   5.0    | 0.037 units

Expected Win Rate: ~11%
Expected ROI: +3.1%
Paper Trading: LOG these bets, do NOT place real money yet
```

---

## 📋 **What Each Column Shows**

### **bet_num**
```
🎯 BET #1, BET #2, etc.
```
Numbers your bets for the day

---

### **race_time** ⏰
```
14:30
```
**When the race starts** (24-hour format)  
Use this to know when to place bet before race

---

### **race** 🏇
```
Ascot - (Class 2)
```
**Which course and what class**  
Example: Ascot is the track, Class 2 is the race grade

---

### **selection** 🐴
```
Thunder Road (J. Gosden)
```
**Horse name and trainer**  
Example: Thunder Road trained by John Gosden

---

### **details** 📊
```
#5 | 4yo | 130lbs
```
**Runner number, age, weight**  
- #5 = Stall/draw position
- 4yo = 4 years old
- 130lbs = Weight carried

---

### **price** 💰 ⭐ **THIS IS THE ODDS**
```
9.50 odds (Rank 4)
```
**The price/odds and market position**  
- **9.50** = Decimal odds ⭐ **THIS IS WHAT YOU BET AT**
- Rank 4 = 4th favorite in the betting

**Example**: Bet £1 at 9.50 odds = £9.50 return if wins (£8.50 profit)

---

### **probabilities** 🧮
```
10.5% mkt → 23.0% model
```
**What market thinks vs what model thinks**  
- Market: 10.5% chance to win
- Model: 23.0% chance to win
- **Model sees value** (much higher probability)

---

### **value** 📈
```
2.19x | +12.5pp edge
```
**How much disagreement and edge**  
- 2.19x = Model is 2.19 times higher than market
- +12.5pp = 12.5 percentage point advantage

---

### **stake** 💵
```
0.015 units (~£0.75 with £50 units)
```
**How much to bet**  
- 0.015 units in betting units
- ~£0.75 if you use £50 per unit
- ~£1.50 if you use £100 per unit

---

## 🎯 **Complete Example Bet**

From the output above, **Bet #1** tells you:

```
WHEN:  2:30 PM (14:30)
WHERE: Ascot
WHAT:  Thunder Road
WHO:   Trained by J. Gosden
DRAW:  Stall #5
PRICE: 9.50 odds ⭐
RANK:  4th favorite
BET:   £0.75 (if using £50 units)

If WINS:
  Return: £0.75 × 9.50 × 0.98 = £6.98
  Profit: £6.23
  
If LOSES:
  Loss: -£0.75
```

**You log this to your spreadsheet** (paper trading).

---

## 📊 **Summary Section**

```
Total Bets: 3
Avg Odds: 10.17
Total Stake: 0.037 units (£1.85 with £50 units)
```

**For the entire day**:
- 3 bets to place
- Average price is 10.17
- Total risk: £1.85

---

## ✅ **Yes, It Shows You Everything!**

**The script gives you**:
- ✅ **Race TIME** (14:30, 15:45, etc.)
- ✅ **Course NAME** (Ascot, Newmarket, etc.)
- ✅ **Horse NAME** (Thunder Road, Silver Storm, etc.)
- ✅ **PRICE/ODDS** (9.50, 10.00, 11.00) ⭐
- ✅ **Trainer** (J. Gosden, A. OBrien, etc.)
- ✅ **Stake amount** (£0.75, £0.60, etc.)
- ✅ **Why to bet** (disagreement, edge, probabilities)

**Everything you need to place the bets!**

---

## 📝 **How to Use the Output**

**From the example above, you'd**:

1. **At 2:25 PM**: Go to Betfair Exchange
2. **Find**: Ascot 2:30 PM race
3. **Search**: Thunder Road (#5)
4. **Check odds**: Should be around 9.50 (might be 9.0-10.0 by post time)
5. **Place back bet**: £0.75 at best available odds
6. **Repeat**: For Bet #2 and #3

**During paper trading**: Just LOG these in spreadsheet, don't actually bet!

---

## 🎯 **What You Log in Spreadsheet**

| Date | Time | Course | Horse | Odds | Stake | Result | P&L |
|------|------|--------|-------|------|-------|--------|-----|
| 2025-10-18 | 14:30 | Ascot | Thunder Road | 9.50 | £0.75 | WON | +£6.23 |
| 2025-10-18 | 15:45 | Newmarket | Silver Storm | 10.00 | £0.60 | LOST | -£0.60 |
| 2025-10-18 | 17:00 | Leopardstown | Celtic Dawn | 11.00 | £0.50 | LOST | -£0.50 |

**Day total**: +£5.13

---

**So YES - the script shows you the PRICE (odds), RACE TIME, HORSE NAME, COURSE, and STAKE amount. Everything you need!** ✅
