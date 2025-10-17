# Your Question: Exchange or Bookmaker Prices?

**Short Answer**: ⭐ **Use EXCHANGE (Betfair) prices** ⭐

---

## 📊 **Why Exchange (Betfair)**

### **1. Model is Built For It**

```
Backtest used: win_ppwap (Betfair exchange odds)
Commission assumed: 2%
Result: +3.1% ROI (AFTER commission)

This means:
  - Model expects exchange-level odds (~10% better)
  - Commission already factored in
  - If you use bookmaker odds (worse), ROI will drop
```

---

### **2. Better Odds**

**Same horse, same race**:

| Source | Odds | Your £1 Returns | Effective Value |
|--------|------|-----------------|-----------------|
| **Bookmaker** | 9.00 | £9.00 (no commission) | £9.00 |
| **Exchange** | 10.00 | £9.80 (2% commission) | £9.80 ✅ **9% better** |

**Even with 2% commission, exchange is better!**

---

### **3. Won't Get Banned**

**Bookmakers**:
```
Month 1: Bet £10, all accepted ✅
Month 3: Win 60%, account flagged ⚠️
Month 6: Stake limited to £2 max ❌
Month 12: Account closed ❌
```

**Exchange**:
```
Month 1: Bet £10, all accepted ✅
Month 3: Win 60%, they make commission ✅
Month 6: Bet £50, still accepted ✅
Year 5: Bet £500, welcomed (more commission for them) ✅
```

**Exchanges LOVE winners** (they profit from commission regardless of who wins)

---

### **4. What This Means for You**

**Using Exchange (Betfair)**:
- Sustainable long-term
- Better odds (10% higher)
- Can scale up (£10 → £50 → £200 bets)
- Model optimized for this (+3.1% ROI proven)

**Using Bookmakers**:
- Limited after 3-6 months
- Worse odds (5-10% lower)
- Can't scale (max £5-10/bet)
- ROI will be lower (maybe +1% instead of +3%)

---

## 💰 **Commission Breakdown**

### **Betfair Commission**

**How it works**:
```
Bet: £1.00 @ 10.0 odds
Win: £10.00 gross
Commission: 2% of net winnings
  = 2% of £9.00 (profit)
  = £0.18
Net return: £9.82

Loss: £0 commission (only on winnings)
```

**Annual cost** (based on 979 bets/year, 11% win rate):
```
Wins: ~110/year
Avg profit per win: ~£8 (at 10.0 odds, £1 stake)
Commission per win: ~£0.16
Annual commission: ~£18

Gross profit: £50
Commission: -£18
Net profit: £32 (still profitable!)
```

**Commission is ALREADY in the +3.1% ROI!**

---

## 🗄️ **Database Column**

### **What to Use in Script**:

**Priority 1** (Best):
```sql
ru.win_ppwap  -- Betfair Pre-Play WAP
```

**Priority 2** (Fallback):
```sql
COALESCE(ru.win_ppwap, ru.dec)  -- Exchange first, bookmaker if missing
```

**Current script uses**: ✅ `COALESCE(win_ppwap, dec)` - **Perfect!**

---

## 🎯 **Tell Your Developer**

**Simple instruction**:

> "Use **`win_ppwap`** column from `racing.runners` table.  
> This is Betfair exchange odds.  
> Make sure it's populated by 8 AM daily.  
> If not available, fall back to `dec` column."

**Technical check**:
```sql
-- Developer runs this at 7:30 AM
SELECT 
    COUNT(*) FILTER (WHERE win_ppwap IS NOT NULL) as have_exchange,
    COUNT(*) FILTER (WHERE dec IS NOT NULL) as have_book,
    COUNT(*) as total
FROM racing.runners ru
JOIN racing.races r USING (race_id)
WHERE r.race_date = CURRENT_DATE;

-- Need: have_exchange > 80% of total
-- Or: have_book > 80% if exchange not available
```

---

## 💡 **Recommendation**

### **For You**:
1. ✅ **Open Betfair Exchange account** (not Sportsbook)
2. ✅ **Fund with £500-1000** initially
3. ✅ **Understand 2% commission** (already factored in ROI)
4. ✅ **Place bets on exchange** when script shows selections

### **For Developer**:
1. ✅ **Ensure `win_ppwap` populates** by 8 AM daily
2. ✅ **Run validation query** before 8 AM
3. ✅ **Alert if data not ready** (< 80% coverage)

---

## 📋 **Quick Decision Matrix**

| Factor | Exchange | Bookmaker | Winner |
|--------|----------|-----------|--------|
| **Odds** | 10.00 | 9.00 | ✅ Exchange (+11%) |
| **Commission** | 2% on wins | 0% | ⚠️ Bookmaker |
| **Net Value** | 9.80 | 9.00 | ✅ Exchange (+9%) |
| **Sustainability** | Unlimited | 3-6 months | ✅ Exchange |
| **Model Fit** | Designed for | Not optimized | ✅ Exchange |
| **Scaling** | Can grow | Gets limited | ✅ Exchange |

**Overall**: ✅ **Exchange wins** (4 out of 6 factors)

---

## ✅ **Final Answer**

**Use**: **Betfair Exchange** (`win_ppwap` column)

**Why**: 
- Better odds (even with commission)
- Model built for this
- Won't get banned
- Can scale up

**Tell developer**: 
> "Make sure `win_ppwap` is populated in `racing.runners` by 8 AM daily. Script won't work without it!"

---

**That's it! Exchange prices = the way to go.** 🎯

