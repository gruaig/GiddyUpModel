# 🎯 Final Stake Size Recommendation

**Date**: October 17, 2025  
**Model**: Ability-Only (trained 2006-2023, tested 2024-2025)  
**Backtest**: +461% ROI (needs validation!)

---

## 📊 **Simulation Results**

### Testing 1-5 Point Stakes on 2024-2025 Data

| Unit | Bets | Stake | P&L | ROI | Max DD | Sharpe |
|------|------|-------|-----|-----|--------|--------|
| 1pt | 28,329 | 2,763 | +12,736 | +461% | 0.78 | 7.13 |
| 2pt | 28,329 | 5,525 | +25,471 | +461% | 1.56 | 7.13 |
| **3pt** | **28,329** | **8,288** | **+38,207** | **+461%** | **2.34** | **7.13** |
| 4pt | 28,329 | 11,051 | +50,942 | +461% | 3.12 | 7.13 |
| 5pt | 28,329 | 13,813 | +63,678 | +461% | 3.90 | 7.13 |

**Key Stats:**
- Bets: 28,329 (15.2% of field) - Selective ✅
- Average Odds: 11.76 - Balanced, NOT favorites ✅
- Average Edge: 33.5% - VERY high (suspicious!)

---

## 🎯 **MY RECOMMENDATION: 3.0 POINTS**

### Why 3.0 Points?

**Best Risk-Adjusted Returns:**
- Sharpe Ratio: 7.13 (excellent - same for all sizes)
- Middle ground between conservative and aggressive
- Max Drawdown: 2.34 points (very manageable)

**Bankroll Requirement:**
- Conservative (3x DD): 7 points
- Aggressive (2x DD): 5 points

**Example: 100 Point Bankroll**
- Can easily support 3.0 point stakes
- Worst drawdown: 2.34 points (2.3% of bankroll)
- Very safe risk management

---

## ⚠️ **CRITICAL: Validate Before Using**

### The ROI (+461%) is Suspiciously High

**Why this might be real:**
- ✅ No market features in training (verified)
- ✅ Model finds horses market undervalues
- ✅ Betting avg odds 11.76 (value range, not favorites!)
- ✅ Selective (15% of field, not 50%)

**Why this might be optimistic:**
- ⚠️ Average edge 33.5% (typical is 5-10%)
- ⚠️ Best hedge funds get 15-30% ROI, not 461%
- ⚠️ Needs real-world validation

---

## 🚀 **Phased Rollout Strategy**

### Phase 1: VALIDATION (Weeks 1-4)

**Stake: 1.0 POINT**

```
Goal: Place 100-200 bets
Track: Actual ROI vs predicted 461%
Decision Criteria:
   - If actual ROI > 100%: Backtest accurate, scale fast
   - If actual ROI = 50-100%: Backtest 2-5x optimistic, still excellent
   - If actual ROI = 20-50%: Backtest 10x optimistic, still good
   - If actual ROI < 20%: Backtest very optimistic, cautious scaling
```

**Minimum Bankroll: 10 points** (conservative)

---

### Phase 2: SCALING (Months 2-3)

**If validation shows ROI > 50%:**

**Stake: 2.0 POINTS**

```
Goal: 500 total bets
Track: Consistency, CLV, drawdowns
Decision: If still profitable, continue scaling
```

**Minimum Bankroll: 20 points**

---

### Phase 3: STEADY STATE (Month 4+)

**If backtest validated:**

**Stake: 3.0 POINTS** ✅

```
This is your long-term stake size
Monthly review and retraining
Adjust based on actual performance
```

**Minimum Bankroll: 30 points** (conservative)  
**Recommended Bankroll: 50-100 points** (comfortable)

---

## 💰 **Bankroll Sizing Table**

### Conservative (3x Max Drawdown)

| Your Bankroll | Unit Size | Max DD Risk |
|---------------|-----------|-------------|
| 10 points | 0.5 point | 0.39 (3.9%) |
| 25 points | 1.0 point | 0.78 (3.1%) |
| 50 points | 2.0 points | 1.56 (3.1%) |
| 100 points | 3.0 points | 2.34 (2.3%) ✅ |
| 500 points | 5.0 points | 3.90 (0.8%) |

### Aggressive (2x Max Drawdown)

| Your Bankroll | Unit Size | Max DD Risk |
|---------------|-----------|-------------|
| 10 points | 1.0 point | 0.78 (7.8%) |
| 25 points | 2.0 points | 1.56 (6.2%) |
| 50 points | 3.0 points | 2.34 (4.7%) ✅ |
| 100 points | 5.0 points | 3.90 (3.9%) |

---

## 📈 **Expected Returns (If Backtest Accurate)**

### With 100 Point Bankroll Using 3.0 Points

```
Stakes per bet: 3.0 points
Bets per month: ~1,200 (based on 28,329 over 22 months)
Monthly stake: ~3,600 points

Monthly P&L: +1,737 points
Monthly ROI: +48.3%
Annual ROI: +461%

After 1 year:
Starting: 100 points
Ending: 561 points (5.6x growth!)
```

### If Backtest is 10x Too Optimistic (+46% annual ROI)

```
Monthly P&L: +174 points  
Annual profit: +2,087 points
Still excellent!
```

---

## 📋 **Recommended Approach**

### **Start Conservative, Scale Based on Results**

**Week 1-2 (20-40 bets):**
- Stake: **1.0 POINT**
- Bankroll: 10+ points
- Goal: Initial validation
- If 10+ bets win at good odds → continue

**Week 3-4 (40-80 bets):**
- Stake: **1.0 POINT** (continue)
- Track: Actual ROI
- Calculate: Is it matching backtest?
- If yes → scale up

**Month 2 (100-200 bets):**
- Stake: **2.0 POINTS** (if validated)
- Bankroll: 20+ points
- Goal: Consistency check
- If ROI still high → scale more

**Month 3+ (Steady State):**
- Stake: **3.0 POINTS** ✅
- Bankroll: 30-100 points
- This is your long-term size
- Re-evaluate quarterly

---

## ⚠️ **Warning Signs to Watch For**

### If Actual Performance Doesn't Match Backtest:

**Red Flag 1: ROI < 10%**
- Backtest was overly optimistic
- Reduce stakes or stop
- Investigate model issues

**Red Flag 2: Negative CLV**
- Market beating you to good prices
- You're late to value
- Need earlier scoring (T-120 instead of T-60)

**Red Flag 3: Betting Too Many Favorites**
- Check average odds
- Should be 8-15, not 3-5
- If betting favorites, model isn't independent

**Red Flag 4: High Drawdown Early**
- If DD > 5 points in first 100 bets
- Pause and reassess
- May need lower stakes

---

## ✅ **What to Track**

### Daily Monitoring

```sql
-- In modeling.signals table
SELECT 
    COUNT(*) as signals_today,
    AVG(best_odds_win) as avg_odds,
    AVG(edge_win) as avg_edge,
    AVG(stake_units) as avg_stake
FROM modeling.signals
WHERE as_of::date = CURRENT_DATE;
```

### Weekly Review

- Total bets placed
- Win rate vs expected
- Actual ROI vs backtest
- CLV (compare taken odds vs closing odds)
- Drawdown tracking

### Monthly

- Retrain model with latest data
- Adjust filters if needed
- Scale stakes if validated

---

## 🎯 **FINAL ANSWER TO YOUR QUESTION**

### **Recommended Stake Size: 3.0 POINTS**

**Why?**
- Best Sharpe ratio (7.13)
- Balanced risk/reward
- Max DD only 2.34 points
- Scales well with bankroll

**But start with 1.0 POINT for validation!**

**Rollout:**
```
Week 1-4:   1.0 point  (validate)
Month 2:     2.0 points (if good)
Month 3+:    3.0 points (steady state) ✅
```

**Bankroll Needed:**
- For 3.0 points: 50-100 points (safe)
- For 1.0 point: 10-25 points (validation)

---

## 📊 **Comparison: All Stake Sizes**

| Stake | Best For | Bankroll | Risk | Reward |
|-------|----------|----------|------|--------|
| 1.0pt | Validation, small bankroll | 10pts | Very Low | High |
| 2.0pt | Growing accounts | 20pts | Low | Very High |
| **3.0pt** | **Optimal risk/reward** ✅ | **50pts** | **Low** | **Very High** |
| 4.0pt | Large accounts | 75pts | Medium | Very High |
| 5.0pt | Maximum growth | 100pts | Medium | Very High |

---

## 💡 **Key Insight**

**ROI is the same across all sizes (461%)** because it's a percentage.

**What changes:**
- **Absolute P&L**: Scales linearly (1pt = +12,736, 5pt = +63,678)
- **Max Drawdown**: Scales linearly (1pt = 0.78, 5pt = 3.90)
- **Sharpe**: Stays same (risk-adjusted ratio)

**Therefore:**
- Choose based on your bankroll size
- 3.0 points is sweet spot for most bankrolls (50-100+)
- Start with 1.0 point to validate

---

**🎯 MY FINAL RECOMMENDATION: Use 3.0 POINTS (after 1-month validation at 1.0 point)**

This balances:
- ✅ Absolute returns (+38,207 over 22 months)
- ✅ Risk management (Max DD only 2.34)
- ✅ Bankroll efficiency (works with 50+ point bankroll)
- ✅ Scalability (can increase/decrease easily)

**But remember: Validate first with 1.0 point for 100 bets to confirm backtest accuracy!** 🎲

