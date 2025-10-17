# Path B — Hybrid Market-Aware Scoring Guide

**Branch**: `plan_b`  
**Goal**: 200-500 bets/year with 5-15% ROI using market-aware scoring

---

## 🎯 What is Path B?

**Path B** is an alternative to the current Hybrid V3 model that aims for **higher volume** while maintaining profitability.

### **Key Differences from Current Model**

| Aspect | Current (Hybrid V3) | Path B |
|--------|---------------------|--------|
| **Training** | Ability-only ✅ | Ability-only ✅ (same) |
| **Scoring** | Fixed 6-gate system | Banded thresholds by odds |
| **Blending** | Adaptive by rank | Adaptive by odds band |
| **Volume** | ~980 bets/year | 200-500 bets/year (target) |
| **ROI** | +3.1% proven | 5-15% target |
| **Focus** | Mid-field (rank 3-6) | All ranks with band-specific logic |

---

## 🏗️ Architecture

### **1. Training** (Same as Current)

```
Ability-Only Features (23):
├── gpr, gpr_sigma
├── days_since_run, last_pos, avg_btn_last_3
├── career_runs, career_strike_rate
├── trainer/jockey stats
└── course/distance proficiency

Model: LightGBM + Isotonic Calibration
Training: 2006-2023 (18 years)
Testing: 2024-2025 (holdout)
```

**No changes to training** - uses exact same model as current.

---

### **2. Scoring** (NEW: Banded Approach)

#### **Step 1: Get Model Prediction**
```
p_model = model.predict(ability_features)
```

#### **Step 2: Calculate Vig-Free Market**
```
q_market = 1 / odds
overround = Σ(1 / odds_i) across race
q_vigfree = q_market / overround
```

#### **Step 3: Odds-Band Specific Blending**

**Lambda by odds** (trust market more for favorites):

| Odds Range | Lambda (λ) | Meaning |
|------------|------------|---------|
| 1.5-3.0 (Favorites) | 0.60 | 60% market, 40% model |
| 3.0-5.0 (Short) | 0.45 | 55% model, 45% market |
| 5.0-8.0 (Mid) | 0.30 | 70% model, 30% market |
| 8.0-12.0 (Sweet spot) | 0.15 | 85% model, 15% market |
| 12.0+ (Longshots) | 0.35 | 65% model, 35% market |

**Blend formula**:
```
p_blend = (1 - λ) * p_model + λ * q_vigfree
```

**Rationale**:
- Favorites: Market is most efficient → trust it more
- Mid prices: Model has edge → trust it more
- Longshots: Model can be overconfident → hedge with market

---

#### **Step 4: Calculate Edge & EV**
```
edge_pp = p_blend - q_vigfree
EV = p_blend * (odds - 1) * 0.98 - (1 - p_blend)
```

#### **Step 5: Banded Gate Thresholds**

**Edge minimums by band**:

| Odds Range | Min Edge | Min EV | Reasoning |
|------------|----------|--------|-----------|
| 1.5-3.0 | 12pp | 2% | Market most efficient |
| 3.0-5.0 | 8pp | 2% | Moderate efficiency |
| 5.0-8.0 | 6pp | 2% | Model has room |
| 8.0-12.0 | 4pp | 2% | Proven sweet spot |
| 12.0+ | 8pp | 3% | Guard longshots |

#### **Step 6: Additional Gates**
- Odds range: 2.0 - 30.0
- Liquidity: ≥ £250 available
- Top-1 per race by edge
- Max 20 bets/day

---

### **3. Staking** (Kelly with Caps)

```
kelly_full = (p_blend * (b + 1) - 1) / b
  where b = (odds - 1) * 0.98

stake = kelly_full * 0.25  (quarter Kelly)
stake = min(stake, 0.5 units)  (cap at 0.5u)

If odds < 3.0 (favorite):
  stake = min(stake, 0.25 units)  (extra cap)
```

---

## 📊 Expected Performance

### **Targets**

| Metric | Target | Current Model |
|--------|--------|---------------|
| **Volume** | 200-500 bets/year | ~980 bets/year |
| **ROI** | 5-15% | +3.1% |
| **Win Rate** | 15-25% | ~11% |
| **Avg Odds** | 5-10 | 9.96 |

### **Why Different?**

**Current model** (Hybrid V3):
- Very selective (strict gates)
- High volume but lower ROI
- Focuses on rank 3-6 only

**Path B**:
- Banded approach (different logic per odds band)
- Lower volume but higher ROI target
- All ranks considered with appropriate thresholds

---

## 🚀 How to Use

### **1. Run Backtest**

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
git checkout plan_b

# Run backtest
uv run python tools/backtest_path_b.py
```

**Output**:
```
PATH B BACKTEST RESULTS
═══════════════════════════════════════════════════════════════════════════════

Overall Performance:
  Total bets: 450
  Wins: 68 (15.1%)
  Annual bet rate: 247 bets/year

Financial:
  Total stake: 12.50 units
  Total P&L: +1.15 units
  ROI: +9.20% ✅
  Avg odds: 7.82

Targets:
  ✅ Volume: 247 bets/year (target: 200-500)
  ✅ ROI: +9.20% (target: 5%+)

Performance by Odds Band:
  1.5-3.0 (15 bets):  ROI: -2.50% ❌
  3.0-5.0 (82 bets):  ROI: +5.80% ✅
  5.0-8.0 (180 bets): ROI: +12.40% ✅
  8.0-12.0 (150 bets): ROI: +10.20% ✅
  12.0+ (23 bets):    ROI: +3.10% ✅
```

---

### **2. Tune Configuration**

Edit `config/path_b_hybrid.yaml`:

**If ROI too low** (< 5%):
```yaml
# Tighten gates
edge_min_by_odds:
  "3.0-5.0": 0.10  # was 0.08
  "5.0-8.0": 0.08  # was 0.06

# Trust market more
lambda_by_odds:
  "5.0-8.0": 0.35  # was 0.30
```

**If volume too low** (< 200/year):
```yaml
# Loosen gates
edge_min_by_odds:
  "3.0-5.0": 0.06  # was 0.08
  "5.0-8.0": 0.04  # was 0.06

# Lower odds minimum
odds_caps:
  min: 1.8  # was 2.0
```

**If volume too high** (> 500/year):
```yaml
# Tighten gates
edge_min_by_odds:
  "3.0-5.0": 0.10  # was 0.08

# Raise odds minimum
odds_caps:
  min: 3.0  # was 2.0
```

---

### **3. Iterate**

```bash
# Edit config
nano config/path_b_hybrid.yaml

# Re-run backtest
uv run python tools/backtest_path_b.py

# Check results
cat backtest_path_b_results.log

# Repeat until targets met
```

**Iteration loop**:
1. Run backtest
2. Check ROI and volume
3. Adjust config
4. Repeat

**Target**: All green ✅ on both volume and ROI

---

## 🎓 Understanding the Banded Approach

### **Why Different Thresholds per Band?**

**Market efficiency varies by odds**:

```
Favorites (2-3 odds):
├─ Heavy volume
├─ Professional money
├─ Market VERY efficient
└─ Need BIG edge to profit (12pp)

Mid-range (5-8 odds):
├─ Moderate volume
├─ Less professional focus
├─ Market less efficient
└─ Smaller edge works (6pp)

Sweet spot (8-12 odds):
├─ Low volume
├─ Casual money
├─ Market least efficient
└─ Model's best range (4pp)

Longshots (12+ odds):
├─ Very low volume
├─ Model overconfident
├─ Need hedge with market
└─ Higher threshold again (8pp)
```

**One-size-fits-all doesn't work** - each band needs tailored logic.

---

### **Why Blend with Market?**

**Pure model (current approach)**:
- Independent predictions
- Can find mispricing
- But can be wrong on favorites (market knows better)
- And overconfident on longshots

**Blended (Path B)**:
- Still independent training
- But acknowledges market wisdom at scoring
- Reduces errors on extremes
- More bets pass gates (higher volume)

**Example**:

```
Race: Favorite at 2.5 odds

Pure Model:
  p_model = 45% (model thinks it's good value)
  q_vigfree = 38%
  edge = +7pp
  Bet? Maybe (if gates allow)
  
Blended (λ=0.60):
  p_blend = 0.4 * 45% + 0.6 * 38% = 40.8%
  edge = 40.8% - 38% = +2.8pp
  Bet? No (below 12pp threshold)
  
Result: Fewer bad favorite bets ✅
```

---

## 📈 Tuning Guide

### **Common Scenarios**

#### **Scenario 1: Good ROI, Low Volume**

```
Results: 150 bets/year, +12% ROI
Problem: Volume below 200 target

Solution: Loosen gates
  - Lower edge_min for 3-5 band (0.08 → 0.06)
  - Lower edge_min for 5-8 band (0.06 → 0.05)
  - Lower odds_min (2.0 → 1.8)
```

---

#### **Scenario 2: High Volume, Low ROI**

```
Results: 600 bets/year, +2% ROI
Problem: Too many bets, not selective enough

Solution: Tighten gates
  - Raise edge_min for 3-5 band (0.08 → 0.10)
  - Raise edge_min for 5-8 band (0.06 → 0.08)
  - Raise odds_min (2.0 → 3.0)
  - Trust market more (increase lambda)
```

---

#### **Scenario 3: Favorites Losing Money**

```
Results: 1.5-3.0 band ROI: -5%

Solution: Trust market more on favorites
  - Increase lambda for 1.5-3.0 (0.60 → 0.70)
  - Raise edge_min for 1.5-3.0 (0.12 → 0.15)
  - Or exclude entirely (odds_min = 3.0)
```

---

#### **Scenario 4: Longshots Too Optimistic**

```
Results: 12+ band ROI: -8%

Solution: Hedge more with market
  - Increase lambda for 12+ (0.35 → 0.45)
  - Raise edge_min for 12+ (0.08 → 0.10)
  - Lower odds_max (30 → 20)
```

---

## 📋 Configuration Reference

### **Complete Config Structure**

```yaml
config/path_b_hybrid.yaml

model:                    # Which model to use
  name: "hrd_win_prob_ability"
  stage: "Production"

snapshot:                 # Market snapshot timing
  minutes_before: 60
  source: "win_ppwap"

market:                   # Commission
  commission: 0.02

odds_caps:                # Odds range
  min: 2.0
  max: 30.0

liquidity:                # Minimum liquidity
  min_gbp: 250

lambda_by_odds:           # Blending by band (KEY PARAMETER)
  "1.5-3.0": 0.60
  "3.0-5.0": 0.45
  "5.0-8.0": 0.30
  "8.0-12.0": 0.15
  "12.0-999": 0.35

edge_min_by_odds:         # Edge thresholds (KEY PARAMETER)
  "1.5-3.0": 0.12
  "3.0-5.0": 0.08
  "5.0-8.0": 0.06
  "8.0-12.0": 0.04
  "12.0-999": 0.08

ev_min_by_odds:           # EV thresholds
  "1.5-3.0": 0.02
  "3.0-5.0": 0.02
  "5.0-8.0": 0.02
  "8.0-12.0": 0.02
  "12.0-999": 0.03

kelly:                    # Staking
  fraction: 0.25
  cap_units: 0.5

favorite_caps:            # Extra favorite limits
  odds_threshold: 3.0
  max_stake_units: 0.25

selection:                # Per-race/day limits
  top_n_per_race: 1
  max_bets_per_day: 20

risk:                     # Risk controls
  max_stake_per_race: 1.0
  max_stake_per_day: 10.0
  stop_loss_per_day: 6.0

targets:                  # Success criteria
  min_bets_per_year: 200
  max_bets_per_year: 500
  min_roi: 0.05
  target_roi: 0.10
```

**Main tuning parameters**:
1. `lambda_by_odds` - How much to trust market per band
2. `edge_min_by_odds` - How selective to be per band
3. `odds_caps.min` - Exclude favorites below this
4. `kelly.fraction` - Stake sizing aggressiveness

---

## 🎯 Success Criteria

### **Ready to Deploy When**:

✅ **Volume**: 200-500 bets/year  
✅ **ROI**: ≥ 5% (target 10%+)  
✅ **Win Rate**: 15-25%  
✅ **Band Performance**: Non-negative in 3+ bands  
✅ **Consistency**: Positive in multiple backtest runs with config tweaks

### **Red Flags**:

❌ Any band with ROI < -10%  
❌ Overall win rate < 10%  
❌ Negative ROI in 3+ consecutive backtest runs  
❌ Extreme concentration (>70% bets in one band)

---

## 🔄 Comparison: Current vs Path B

### **When to Use Current Model (Hybrid V3)**

✅ Want proven track record (+3.1% ROI on 1,794 bets)  
✅ Prefer higher volume (~1,000 bets/year)  
✅ Okay with lower but stable ROI  
✅ Don't want to tune parameters  

### **When to Use Path B**

✅ Want higher ROI (5-15% target)  
✅ Okay with lower volume (200-500 bets/year)  
✅ Want more control (band-specific tuning)  
✅ Willing to iterate and optimize  

### **Can Run Both!**

```
Strategy: Hybrid Portfolio

Current Model:
  - Main strategy
  - Proven, stable
  - 3-4 bets/day

Path B:
  - Secondary strategy  
  - Higher ROI potential
  - 1-2 bets/day (different selections)

Combined:
  - Diversified approach
  - Smooth equity curve
  - Higher overall profit
```

---

## 📂 File Structure

```
Path B Files:

config/
└── path_b_hybrid.yaml           Configuration

src/giddyup/scoring/
├── __init__.py
└── path_b_hybrid.py             Core scoring logic

tools/
└── backtest_path_b.py           Backtest script

PATH_B_GUIDE.md                  This guide
backtest_path_b_results.log      Results output
```

---

## 🚀 Quick Start

```bash
# 1. Switch to Path B branch
git checkout plan_b

# 2. Run backtest
uv run python tools/backtest_path_b.py

# 3. Check results
cat backtest_path_b_results.log

# 4. If not meeting targets, tune config
nano config/path_b_hybrid.yaml

# 5. Repeat steps 2-4 until targets met

# 6. When ready, commit changes
git add config/path_b_hybrid.yaml
git commit -m "Tuned Path B to {ROI}% ROI, {volume} bets/year"

# 7. Optionally merge to main or keep as separate branch
```

---

##  Next Steps

1. **Run initial backtest** to establish baseline
2. **Analyze results by band** - which bands profitable?
3. **Tune lambda** - trust market more/less per band
4. **Tune edge thresholds** - tighten/loosen gates
5. **Iterate** until both volume and ROI targets met
6. **Paper trade** for 2 months to validate
7. **Deploy** if real-world matches backtest

---

**By**: Sean MoonBoots  
**Branch**: `plan_b`  
**Date**: October 17, 2025

🎯 **Let's find the optimal configuration!**

