# Path A: Pure Ability Model (Independent of Market)

**Branch**: `model_a`  
**Date**: October 17, 2025  
**Status**: ⏳ Training in progress

---

## 🎯 What is Path A?

Path A is a **truly independent** horse racing win probability model that:

1. **Trains ONLY on ability features** - no market data, no expert ratings (OR/RPR)
2. **Predicts independent probabilities** - not correlated with market consensus
3. **Identifies value at scoring time** - compares model probability to vig-free market probability
4. **Bets on mispricing** - only when we have clear edge after commission

---

## ❌ What We REMOVED (Why AUC Was 0.96)

### **Problem: Market Proxy Features**

Previous models included:
- `official_rating` (BHA Official Rating)
- `racing_post_rating` (RPR)
- `best_rpr_last_3`
- `gpr_minus_or` (delta from OR)
- `gpr_minus_rpr` (delta from RPR)

**Why this was bad**:
- OR and RPR are **expert consensus** ratings
- They incorporate the SAME information the market uses
- Result: Model learns `p_win ≈ f(OR, RPR)` which is essentially **learning the market**
- AUC 0.96 looked great but meant **no independent edge**

### **The Fix**

Remove ALL expert ratings and market proxies from training:

```python
# PATH A FEATURES (24 total)
ABILITY_FEATURES = [
    # Our own rating
    "gpr", "gpr_sigma",
    
    # Raw form
    "days_since_run", "last_pos", "avg_btn_last_3",
    "career_runs", "career_strike_rate",
    
    # Connections (objective stats)
    "trainer_sr_total", "trainer_wins_total", "trainer_runs_total",
    "jockey_sr_total", "jockey_wins_total", "jockey_runs_total",
    
    # Course/distance
    "runs_at_course", "wins_at_course",
    
    # Race context
    "field_size", "class_numeric", "is_flat", "is_aw",
    "dist_f", "draw", "age", "lbs",
]
```

**24 features** (down from 28) - all **purely objective**, no expert opinion.

---

## 🛡️ Leakage Guards

We implemented **multiple layers** of protection:

### **1. Regex Pattern Matching**

```python
# src/giddyup/data/guards.py
BANNED = re.compile(
    r"(odds|price|rank|fav|bsp|sp|ip|wap|traded|overround|market|"
    r"official_rating|racing_post_rating|rpr|or\b)",
    re.IGNORECASE
)
```

Catches:
- All odds/price fields
- Rankings and favorites
- **Official Rating (OR)**
- **Racing Post Rating (RPR)**
- Trading/volume data

### **2. Assertion Guards**

```python
def assert_no_market_features(df_cols, feature_cols):
    bad_df = [c for c in df_cols if BANNED.search(c)]
    bad_fx = [c for c in feature_cols if BANNED.search(c)]
    
    if bad_df or bad_fx:
        raise AssertionError("🚫 Market features detected!")
```

**Fails immediately** if any market-like features are present.

### **3. Double-Check in Training**

```python
features = get_feature_list()
guard_no_market(features)  # ← Runs both regex + explicit list check
```

---

## 📊 Expected Results

### **Training Metrics (Realistic)**

| Metric | Path A (Independent) | Previous (With OR/RPR) | Why Different |
|--------|---------------------|------------------------|---------------|
| **AUC** | 0.60-0.75 | 0.96 | No expert ratings = harder |
| **Log Loss** | 0.45-0.55 | 0.16 | More uncertainty (good!) |
| **ROI** | +3% to +10% | Would fail live | Actually independent |

**Lower AUC is GOOD** = we're independent of market = can find mispricing!

### **Why Lower AUC is Better Here**

```
High AUC (0.96) = Model ranks horses similar to market
                → No differentiation
                → No edge

Moderate AUC (0.70) = Model ranks horses DIFFERENTLY from market
                    → When we disagree, we might be right
                    → VALUE opportunities!
```

---

## 💰 Value Betting Strategy

### **Triple Gate System**

Only bet when **ALL THREE** conditions met:

```python
✅ EDGE_MIN = 0.04  (4pp probability advantage)
✅ ODDS_MIN = 3.0   (avoid short-priced favorites)
✅ EV_MIN = 0.03    (3% expected value after commission)
```

### **How It Works**

#### **Step 1: Model Prediction**
```python
X = ability_features  # NO market data!
p_model = model.predict(X)  # e.g., 0.18 (18% win probability)
fair_odds = 1 / 0.18 = 5.56
```

#### **Step 2: Market Probability (Vig-Free)**
```python
# Get T-60 market odds
market_odds = 8.0

# Remove bookmaker margin
q_market = 1 / 8.0 = 0.125
overround = sum(1/odds for all horses) = 1.12
q_vigfree = 0.125 / 1.12 = 0.112 (11.2%)
```

#### **Step 3: Calculate Edge**
```python
edge = p_model - q_vigfree
     = 0.18 - 0.112
     = 0.068 (6.8 percentage points)
✅ > 0.04 (passes gate 1)
```

#### **Step 4: Expected Value**
```python
EV = p × (odds-1) × (1-commission) - (1-p)
   = 0.18 × 7.0 × 0.98 - 0.82
   = 0.235 (23.5% expected return)
✅ > 0.03 (passes gate 2)
```

#### **Step 5: Odds Check**
```python
odds = 8.0
✅ > 3.0 (passes gate 3)
```

#### **Step 6: Kelly Staking**
```python
kelly_full = 0.044 (4.4% of bankroll)
stake = 0.25 × kelly_full = 0.011 (1.1% of bankroll)
stake_capped = min(0.011, 0.005) = 0.5 units

🎯 BET: Horse @ 8.0 for 0.5 units
```

---

## 🔍 Backtest Protocol

### **Data**
- **Training**: 2006-2023 (never use 2024-2025)
- **Test**: 2024-2025 (pure holdout, 189K runners)
- **Market odds**: T-60 snapshots

### **Metrics to Track**

1. **Overall ROI** (target: +3% to +10%)
2. **Number of bets** (target: 500-2000 per year)
3. **Average odds** (target: 6-12, not all favorites)
4. **CLV** (Closing Line Value - should be positive)
5. **Max drawdown** (manage risk)
6. **Sharpe ratio** (risk-adjusted returns)

### **Segmented Analysis**

#### **By GPR Level**
| GPR Range | Interpretation | Expected Performance |
|-----------|----------------|---------------------|
| < 70 | Weak horses | Few bets, low ROI |
| 70-80 | Below average | Some value at long odds |
| 80-90 | Average | Main betting range |
| 90-100 | Good | High ROI expected |
| > 100 | Elite | Rare, but valuable |

#### **By Odds Band**
| Odds | Bet % | Expected ROI | Risk |
|------|-------|--------------|------|
| 3-5 | 15-25% | +3% to +6% | Low variance |
| 5-8 | 30-40% | +5% to +10% | Moderate |
| 8-15 | 30-40% | +6% to +12% | Higher variance |
| 15+ | 5-10% | +8% to +15% | High variance |

---

## 🚨 Red Flags (Stop & Debug If)

| Issue | Problem | Action |
|-------|---------|--------|
| AUC > 0.85 | Market leakage | Check features, look for OR/RPR |
| ROI < 0% | No edge | Tighten filters, check calibration |
| Avg odds < 4.0 | Too many favorites | Increase `ODDS_MIN` |
| Bets < 100/year | Filters too tight | Relax `EDGE_MIN` slightly |
| ROI > +20% | Too good to be true | Likely data leakage |

---

## ✅ Validation Checklist

### **Feature Engineering**
- [ ] Only 24 features (no OR, no RPR)
- [ ] All features pass `guard_no_market()`
- [ ] Point-in-time GPR (no look-ahead)
- [ ] All rolling windows use `.shift(1)`

### **Training Metrics**
- [ ] AUC: 0.60-0.75 (not 0.95+)
- [ ] Log Loss: 0.45-0.55
- [ ] Feature importances: GPR in top 3
- [ ] No single feature > 50% importance

### **Backtest Results**
- [ ] Overall ROI: +3% to +10%
- [ ] Bet volume: 500-2000
- [ ] Avg odds: 6-12
- [ ] CLV > 0 (beating closing line)
- [ ] Max DD < 30 units

### **Production Readiness**
- [ ] Guards in place and enforced
- [ ] Model logged to MLflow
- [ ] Scoring script tested
- [ ] Risk controls implemented

---

## 📁 File Changes (Path A)

### **Created**
- `src/giddyup/data/guards.py` - Regex-based leak detection

### **Modified**
- `src/giddyup/data/feature_lists.py` - Removed OR/RPR (24 features now)
- `tools/train_model.py` - Added Path A header
- (Training dataset will be rebuilt without OR/RPR columns)

### **Unchanged**
- `src/giddyup/ratings/gpr.py` - GPR calculation (still used)
- `src/giddyup/models/trainer.py` - Training logic
- `src/giddyup/price/value.py` - EV/Kelly calculations

---

## 🎓 Key Learnings

### **1. Expert Ratings Are Market Proxies**

**Official Rating (OR)** and **Racing Post Rating (RPR)** are created by:
- Watching races
- Analyzing form
- Considering market expectations
- Adjusting based on performance

They are **expert consensus** that highly correlates with market odds.

**Result**: Using OR/RPR in training → Model learns market → No independent edge.

### **2. Independence vs Accuracy**

```
Goal: NOT to predict winners better than market
Goal: Predict DIFFERENTLY enough to find mispricing

Market Odds: 8.0 (12.5% implied)
Our Model:   18% win probability
Difference:  +5.5pp edge → VALUE BET!
```

### **3. Lower AUC Can Mean More Profit**

- **AUC 0.96** = Ranks horses like market = No differentiation
- **AUC 0.70** = Ranks horses differently = Opportunity when correct

We don't need to be right more often than the market, just **right when we disagree**.

### **4. Calibration > Discrimination**

For value betting:
- **Log Loss** (calibration) is more important than AUC
- Probabilities must be **accurate**, not just **ranked correctly**
- Bad calibration → Wrong stakes → Lose money even with edge

---

## 🚀 Next Steps (After Training Completes)

### **Immediate**
1. ✅ Check metrics: AUC should be 0.60-0.75
2. ✅ Verify features: Only 24, no OR/RPR
3. ✅ Feature importance: GPR should be top 3
4. ✅ Run backtest on 2024-2025

### **If Backtest Shows Edge (ROI > +3%)**
1. Register model in MLflow as "path_a_v1"
2. Create scoring script
3. Paper trade for 1-2 months
4. Monitor metrics weekly
5. Consider small real stakes

### **If Backtest Shows No Edge (ROI ≤ 0%)**
1. Check calibration (is Log Loss reasonable?)
2. Review feature engineering (any bugs?)
3. Try different thresholds
4. Consider adding more features (within ability-only constraint)

---

## 📊 Current Status

**Training**: In progress  
**Log**: `training_pathA_20251017_HHMMSS.log`  
**Branch**: `model_a`  
**ETA**: ~60-90 minutes

**What's happening**:
1. Fetching 2M+ runners (2006-2025)
2. Computing point-in-time GPR (20 years)
3. Engineering 24 ability features
4. Training LightGBM (5 folds)
5. Isotonic calibration
6. Evaluation on 2024-2025 test set

---

## 📚 References

**Why This Approach Works**:
- "Prediction vs Odds: Finding Value in Betting Markets" (academic)
- "The Kelly Criterion in Blackjack Sports Betting and the Stock Market" (Thorp)
- "Advances in Financial Machine Learning" (López de Prado) - backtesting chapter

**Our Implementation**:
- `METHOD.md` - Full methodology
- `FIX_LOOK_AHEAD_BIAS.md` - Why we had problems before
- `GPR_IMPLEMENTATION_SUMMARY.md` - GPR technical details

---

*Last Updated: October 17, 2025 13:15 UTC*  
*Status: Training Path A model (no OR/RPR)*

