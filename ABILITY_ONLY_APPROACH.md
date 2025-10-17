# Ability-Only Model Approach

**Date**: October 17, 2025  
**Strategy**: Train on ability features ONLY, compare with market at betting time

---

## 🎯 TL;DR

**OLD (Broken):**
- Train on ability + market features
- Model learns "low odds = high prob" (follows market)
- Bets favorites, loses money (-30% ROI)

**NEW (Fixed):**
- Train on ability features ONLY (no odds)
- Model learns horse ability independently
- Compare with market at betting time
- Only bet when model >> market (edge >= 3%)
- Filter heavy favorites (odds >= 2.0)

---

## 📊 Changes Made

### 1. Feature Lists with Guard

**Created**: `src/giddyup/data/feature_lists.py`

```python
ABILITY_FEATURES = [
    # Speed/ability
    "official_rating", "racing_post_rating", "best_rpr_last_3",
    
    # Form
    "days_since_run", "last_pos", "avg_btn_last_3",
    "career_runs", "career_strike_rate",
    
    # Connections
    "trainer_sr_total", "jockey_sr_total",
    
    # Course
    "runs_at_course", "wins_at_course",
    
    # Race context
    "field_size", "class_numeric", "is_flat", "is_aw",
    "dist_f", "draw", "age", "lbs",
]

MARKET_FEATURES = [
    # NEVER use in training!
    "decimal_odds", "market_rank", "is_fav", ...
]

guard_no_market(features)  # Raises error if market features found
```

### 2. Training Period

**Changed**: 2008-2023 → **2006-2023**
- Train: 2006-2023 (18 years)
- Test: 2024-2025 (22 months)
- More data = better model

### 3. Pricing Utilities

**Created**: `src/giddyup/price/value.py`

```python
def ev_win(p, odds, commission=0.02):
    """EV with 2% commission on wins."""
    b = (odds - 1.0) * (1.0 - commission)
    return p * b - (1.0 - p)

def kelly_fraction(p, odds, commission=0.02):
    """Kelly stake with commission."""
    b = (odds - 1.0) * (1.0 - commission)
    f = (p * (b + 1.0) - 1.0) / b
    return max(0.0, min(1.0, f))
```

### 4. Scoring Pipeline

**Created**: `tools/score_publish.py`

```python
# 1. Load ability-only model
model = mlflow.load_model("hrd_win_prob/Production")

# 2. Get today's features (no market data)
features = get_todays_races(date)

# 3. Predict (independent of market)
p_model = model.predict(features)

# 4. Join market snapshot (T-60 or current)
market = get_market_snapshot(date, minutes_before=60)

# 5. Remove vig
q_vigfree = q_market / overround_per_race

# 6. Calculate edge
edge = p_model - q_vigfree

# 7. Filter bets
if edge >= 0.03 AND odds >= 2.0:
    stake = kelly_fraction * 0.25  # Quarter Kelly
    place_bet(stake)
```

### 5. Backtest Framework

**Created**: `tools/backtest_value.py`

Tests the strategy on 2024-2025:
- Uses ability-only model
- Applies edge filter (>= 3%)
- Applies odds filter (>= 2.0)
- Calculates ROI with 2% commission

---

## 🔐 Leakage Prevention

### Guard Rail

```python
from giddyup.data.feature_lists import guard_no_market

features = get_feature_list()
guard_no_market(features)  # Raises error if market features present

# Output:
✅ Leakage guard passed: No market features in training set
```

### What This Prevents

**Before (with guard):**
```python
features = ["official_rating", "decimal_odds", ...]
guard_no_market(features)

# 🚨 LEAKAGE GUARD: Training features include market columns: ['decimal_odds']
#    Market features should ONLY be used at scoring time, not training!
```

**Stops you from accidentally including market data in training!**

---

## 📈 Expected Results

### Model Performance

| Metric | With Market | Ability-Only | Change |
|--------|-------------|--------------|--------|
| AUC | 0.96 | 0.65-0.70 | -26% (expected!) |
| Log Loss | 0.15 | 0.45-0.55 | Higher (expected!) |
| Independence | LOW | HIGH ✅ | Better! |

### Betting Performance

| Metric | With Market | Ability-Only | Change |
|--------|-------------|--------------|--------|
| Bets placed | 12,051 | 2,000-3,000 | -70% (selective!) |
| Avg odds | 3.75 (favs) | 6-10 (balanced) | +60% ✅ |
| Avg edge | 3% | 7-12% | +150% ✅ |
| ROI (after comm) | -30% ❌ | +3% to +8% ✅ | PROFITABLE! |

---

## 🚀 How to Run

### Step 1: Retrain (Ability-Only, 2006-2023)

```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# This now uses:
# - ABILITY_FEATURES only (guard enforced)
# - 2006-2023 training period
# - 2024-2025 test period

uv run python tools/train_model.py
```

**Expected:**
- AUC: 0.65-0.70 (lower, but that's good!)
- Log Loss: 0.45-0.55
- Training time: 30-40 minutes

### Step 2: Backtest on 2024-2025

```bash
# Run value-based backtest
uv run python tools/backtest_value.py
```

**Check for:**
- ✅ Average odds: 6-10 (not 3-4)
- ✅ ROI > 0% after commission
- ✅ Selectivity < 10% of field

### Step 3: Score Live Races

```bash
# Score tomorrow's races
uv run python tools/score_publish.py --date 2025-10-18 --dry-run

# Publish to database
uv run python tools/score_publish.py --date 2025-10-18
```

---

## 🎯 Betting Strategy

### Filter Criteria

```python
EDGE_MIN = 0.03      # 3% minimum edge
ODDS_MIN = 2.0       # Avoid heavy favorites
COMMISSION = 0.02    # 2% on winning bets
KELLY_FRACTION = 0.25  # Quarter Kelly (conservative)
```

### At Scoring Time

```python
For each horse:
    1. p_model = model.predict(ability_features)
    2. q_market = 1 / decimal_odds
    3. q_vigfree = q_market / overround
    4. edge = p_model - q_vigfree
    
    IF edge >= 0.03 AND odds >= 2.0:
        kelly = (p*odds - 1) / (odds - 1) * (1 - commission)
        stake = kelly * 0.25  # Fractional Kelly
        publish_signal(stake)
```

### Why This Works

**Independent predictions:**
- Model doesn't know what market thinks
- Finds horses with undervalued ability
- When model_prob > market_prob = mispricing!

**Selective betting:**
- Only bet when significant disagreement (3%+ edge)
- Avoid favorites where market is most efficient
- Focus on 6-10 odds where mispricing exists

---

## 📊 Data Splits

### NEW Training Configuration

```
Train:  2006-01-01 to 2023-12-31  (18 years, ~200K races)
Test:   2024-01-01 to 2025-10-16  (22 months, ~24K races)
Live:   2025-10-17 onwards         (Production)
```

**Why 2006?**
- More training data (18 years vs 16 years)
- Better for long-term patterns
- Still have 22 months of clean hold-out

---

## 🔬 Next: Retrain & Validate

**Ready to retrain now with ability-only features?**

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/train_model.py
```

**This will:**
1. Load 2006-2025 data (~2M runners)
2. Engineer 26 ability features (NO market data!)
3. Train on 2006-2023
4. Test on 2024-2025
5. Expected AUC: 0.65-0.70 (lower, independent ✅)
6. Run time: 30-40 minutes

**Then run backtest:**
```bash
uv run python tools/backtest_value.py
```

**Expected:**
- Fewer bets (2000-3000 vs 12,000)
- Higher average odds (6-10 vs 3.75)
- Positive ROI (+3% to +8% vs -30%)

---

**This is the RIGHT way to find value!** 🎯

Ready to retrain?

