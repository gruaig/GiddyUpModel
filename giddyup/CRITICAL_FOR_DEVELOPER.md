# ⚠️ CRITICAL: Daily Odds Data Required

**For**: Developer  
**From**: Sean MoonBoots  
**Date**: October 17, 2025

---

## 🚨 **Models Can't Run Without This Data!**

**Current Status**:
```
✅ Database has races (44 races on Oct 17)
✅ Database has runners (403 runners)
❌ Database has NO ODDS (0 runners with prices)

Result: Selection scripts return ZERO bets ❌
```

**Scripts need odds to calculate value!**

---

## ✅ **What You Must Populate**

### **Column**: `racing.runners.win_ppwap`

**What it means**:
- **win** = Win market (not place)
- **pp** = Pre-Play (before race starts)
- **wap** = Weighted Average Price (from Betfair)

**In simple terms**: **Betfair exchange odds for the horse to win**

---

## 📊 **Exact Requirements**

### **Source**: Betfair Exchange

**NOT**:
- ❌ Bookmaker odds (Paddy Power, Bet365, etc.)
- ❌ Starting Price (SP/BSP)
- ❌ In-play odds

**YES**:
- ✅ **Betfair Exchange "Back" price**
- ✅ Captured ~60 minutes before race
- ✅ Or current price if < 60 min available

---

## 💡 **Simple Explanation**

### **What is `win_ppwap`?**

**It's just the Betfair price!**

**Example**:
```
Race: Ascot 14:30
Horse: Thunder Road

Go to Betfair Exchange:
  Market: "Win"
  Back price showing: 9.50
  
Database update:
  UPDATE racing.runners
  SET win_ppwap = 9.50
  WHERE race_id = [ascot_1430_race_id]
  AND horse_id = [thunder_road_horse_id];
```

**That's it!** The decimal odds from Betfair.

---

## 🔧 **How to Get Betfair Prices**

### **Option 1: Betfair API** (Professional)

**Endpoint**: Exchange API
```
GET /betting/exchange/odds
Market: WIN
Type: BACK
Time: Pre-play (or current if < 1h to off)
```

**Response example**:
```json
{
  "runners": [
    {"selectionId": 12345, "ex": {"availableToBack": [{"price": 9.5}]}}
  ]
}
```

**Map to database**:
```
price 9.5 → win_ppwap = 9.5
```

---

### **Option 2: Betfair Website** (Manual - Testing Only)

**For testing tomorrow**:

1. Go to: https://www.betfair.com/exchange/plus/horse-racing
2. Find tomorrow's races (Oct 18)
3. For each race, note the "Back" price for each horse
4. Manually update database:
   ```sql
   UPDATE racing.runners ru
   SET win_ppwap = [price_from_betfair]
   FROM racing.races r
   WHERE ru.race_id = r.race_id
   AND r.race_date = '2025-10-18'
   AND ru.horse_id = [horse_id];
   ```

**This is ONLY for testing - not sustainable daily!**

---

### **Option 3: Betfair Stream API** (Recommended)

**Best for production**:
```
Subscribe to Betfair Exchange stream
Capture prices every 15 minutes
Store latest pre-play price (T-60 or closest)
Update database automatically
```

---

## 📋 **Exact Data Format**

### **Column Specifications**:

```sql
Column name: win_ppwap
Type: NUMERIC or DECIMAL
Range: 1.01 to 1000.00 (typical: 2.0 to 30.0)
Required: YES (for every runner)
Timing: ~60 minutes before race (or current if less time)
```

**Examples**:
```
Favorite: win_ppwap = 2.50 (Betfair shows 2.50)
Mid-price: win_ppwap = 8.00 (Betfair shows 8.00)
Longshot: win_ppwap = 25.00 (Betfair shows 25.00)
```

---

## 🎯 **Required Timing**

### **When to Capture Prices**:

**Ideal**: 60 minutes before scheduled off time (T-60)

**Acceptable**:
- 75-45 minutes before off (T-75 to T-45)
- Current prices if < 1 hour until race

**NOT acceptable**:
- ❌ Morning prices (T-12 hours - too early, volatile)
- ❌ After race starts (too late, in-play)

### **Daily Schedule**:

```
7:00 AM: Fetch Betfair prices for all today's races
7:30 AM: Update racing.runners.win_ppwap
8:00 AM: User runs selection scripts ✅
```

**Must be ready by 8 AM daily!**

---

## ✅ **Validation Query**

**Run this to check data is ready**:

```sql
-- Check if today's races have odds
SELECT 
    r.race_date,
    COUNT(*) as total_runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) as have_odds,
    ROUND(100.0 * COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) / COUNT(*), 0) as pct_ready
FROM racing.runners ru
JOIN racing.races r ON r.race_id = ru.race_id
WHERE r.race_date = CURRENT_DATE + 1  -- Tomorrow
GROUP BY r.race_date;
```

**Should show**: `pct_ready = 100`

**Currently shows**: `pct_ready = 0` ❌

---

## 🧪 **Test With Sample Data**

**To test the selection scripts work**, populate just ONE race:

```sql
-- Example: Populate Ascot 14:30 race with sample Betfair prices
UPDATE racing.runners 
SET win_ppwap = CASE 
    WHEN num = 1 THEN 3.50   -- Favorite
    WHEN num = 2 THEN 5.00   -- Second favorite
    WHEN num = 3 THEN 7.50   -- Mid-field
    WHEN num = 4 THEN 9.00   -- Mid-field
    WHEN num = 5 THEN 12.00  -- Outsider
    ELSE 15.00               -- Longshots
END
WHERE race_id = (
    SELECT race_id FROM racing.races 
    WHERE race_date = '2025-10-18' 
    LIMIT 1
);
```

**Then run script** - should show 1-2 bets from that race!

---

## 📚 **Full Documentation**

**Simple guide**: `docs/FOR_DEVELOPER.md`

**Complete spec**: `docs/DEVELOPER_DATABASE_REQUIREMENTS.md`

**Both explain**:
- What `win_ppwap` is
- Where to get it (Betfair API)
- When to populate it (by 8 AM daily)
- How to validate it's ready

---

## 🎯 **Summary for Developer**

### **What to Do**:

1. **Set up Betfair API access** (or manual for testing)
2. **Daily (by 8 AM)**:
   ```
   - Fetch Betfair Exchange prices for today's races
   - Update racing.runners.win_ppwap column
   - Verify 100% of runners have prices
   ```
3. **User can then run**: `./RUN_BOTH_STRATEGIES.sh` successfully

### **What `win_ppwap` Should Contain**:

```
Betfair Exchange decimal odds (e.g., 9.50, 12.00, 3.25)

Examples from Betfair website/API:
  "Back 9.5" on Betfair → win_ppwap = 9.5
  "Back 12.0" on Betfair → win_ppwap = 12.0
  "Back 3.25" on Betfair → win_ppwap = 3.25
```

**It's that simple - just the Betfair price number!**

---

**Questions?** See `docs/FOR_DEVELOPER.md` or `docs/DEVELOPER_DATABASE_REQUIREMENTS.md`

---

**By**: Sean MoonBoots  
**Priority**: 🔴 **CRITICAL** - Models can't run without this!

