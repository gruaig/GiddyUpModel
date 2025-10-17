# Message for Developer - Urgent

**From**: Sean (Betting Model Owner)  
**Priority**: 🔴 Required for model to work

---

## 🎯 **What I Need**

**Column**: `racing.runners.win_ppwap`  
**Populate with**: Betfair Exchange decimal odds  
**Frequency**: Daily by 8 AM  
**For**: Tomorrow's races

---

## 💡 **What is `win_ppwap`?**

**Simple answer**: **The Betfair price (decimal odds)**

**Example**:
```
Go to Betfair Exchange
Find: Ascot 14:30, Horse "Thunder Road"
Betfair shows: "Back 9.5"

Update database:
  UPDATE racing.runners 
  SET win_ppwap = 9.5
  WHERE [this horse in this race]
```

**That's it! Just the decimal number from Betfair.**

---

## 📊 **Current Status**

```
✅ racing.races table: Has races
✅ racing.runners table: Has runners
❌ racing.runners.win_ppwap: EMPTY (no odds!)

Result: Betting scripts can't run ❌
```

**Check status**:
```sql
SELECT 
    COUNT(*) as runners,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) as have_odds
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = '2025-10-18';  -- Tomorrow

-- Currently shows: runners=509, have_odds=0 ❌
-- Should show: runners=509, have_odds=509 ✅
```

---

## 🔧 **How to Get Betfair Prices**

### **Option 1: Betfair API** (Recommended):

**Endpoint**: Betfair Exchange Betting API  
**Market**: WIN  
**Price**: Best available "Back" price  
**Format**: Decimal (e.g., 9.5, 12.0, 3.25)

```python
# Pseudo-code
for race in tomorrow_races:
    for runner in race.runners:
        price = betfair_api.get_price(race, runner, market="WIN")
        db.execute(
            "UPDATE racing.runners SET win_ppwap = ? WHERE race_id = ? AND horse_id = ?",
            (price, race.id, runner.id)
        )
```

---

### **Option 2: Manual** (For testing tomorrow):

1. Go to: https://www.betfair.com/exchange/plus/horse-racing
2. Find tomorrow's races (Oct 18)
3. For each race, note each horse's "Back" price
4. Update database:
   ```sql
   -- Example for one race
   UPDATE racing.runners SET win_ppwap = 3.50 WHERE race_id = XXX AND horse_id = YYY;
   UPDATE racing.runners SET win_ppwap = 9.00 WHERE race_id = XXX AND horse_id = ZZZ;
   -- ... etc for all runners
   ```

---

## ⏰ **Timing**

**When to capture**:
- Ideally: ~60 minutes before race
- Acceptable: Current prices if < 1 hour to race
- Daily schedule: Fetch at 7 AM, update by 8 AM

---

## ✅ **Validation**

**After updating, verify 100% populated**:

```sql
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) as have_odds,
    CASE 
        WHEN COUNT(*) = COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) 
        THEN '✅ READY' 
        ELSE '❌ NOT READY' 
    END as status
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = CURRENT_DATE + 1;
```

**Should show**: status = '✅ READY'

---

## 🚨 **Why This Is Critical**

**Without odds data**:
```
❌ Can't calculate market probability
❌ Can't calculate edge
❌ Can't select bets
❌ Model is useless
```

**With odds data**:
```
✅ Calculate value
✅ Select bets
✅ Generate daily selections
✅ Model works as designed
```

---

## 📚 **More Details**

**See full documentation**:
- `CRITICAL_FOR_DEVELOPER.md` - Complete explanation
- `docs/FOR_DEVELOPER.md` - 1-page reference
- `docs/DEVELOPER_DATABASE_REQUIREMENTS.md` - Full spec

---

## 🎯 **Summary**

**Need**: Betfair Exchange decimal odds in `win_ppwap` column  
**Format**: Decimal number (9.5, 12.0, 3.25, etc.)  
**Frequency**: Daily by 8 AM  
**Source**: Betfair Exchange API or website  

**It's literally just copying the Betfair price into the database!**

---

**Questions?** See the documentation files listed above.

**Urgent**: This blocks the entire betting system!

---

**Thanks!**  
Sean

