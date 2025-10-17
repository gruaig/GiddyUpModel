# Hybrid Model: Path A Training + Market-Aware Scoring

**Goal**: Combine Path A's independence with market awareness for better volume/ROI balance

**Target**: 200-500 bets/year at +5-15% ROI

---

## 🎯 **The Hybrid Approach**

### **Core Principle**

```
Training:  Use ONLY ability features (Path A)
           → Model stays independent
           → Can predict differently from market

Scoring:   Add market features for FILTERING
           → Identify when model disagrees with market
           → Use market efficiency as quality signal
           → Filter out false positives
```

**Key insight**: Market features are **not used to predict winners**, but to **identify mispricing**.

---

## 📋 **Step-by-Step Implementation**

### **Phase 1: Keep Path A Training (Already Done)** ✅

```python
# Train with 23 ability features
ABILITY_FEATURES = [
    "gpr", "gpr_sigma",
    "days_since_run", "last_pos", "avg_btn_last_3",
    "career_runs", "career_strike_rate",
    "trainer_sr_total", "trainer_wins_total", "trainer_runs_total",
    "jockey_sr_total", "jockey_wins_total", "jockey_runs_total",
    "runs_at_course", "wins_at_course",
    "field_size", "class_numeric", "is_flat", "is_aw",
    "dist_f", "draw", "age", "lbs",
]

# Result: p_model = independent probability
```

**This stays exactly as is** - we don't retrain.

---

### **Phase 2: Add Market Features at Scoring**

At prediction time, join **market snapshot** data:

```python
# src/giddyup/data/market.py

def get_market_features(race_id, horse_id, snapshot_time="T-60"):
    """
    Get market features for scoring.
    NOT used in training, ONLY at prediction time.
    """
    return {
        "decimal_odds": float,        # Best back odds
        "market_rank": int,            # 1=favorite, 2=2nd fav, etc.
        "q_vigfree": float,            # Vig-free market probability
        "overround": float,            # Race overround
        "volume_traded": float,        # Betting volume (optional)
        "price_movement": float,       # Opening to current (optional)
        "is_favorite": bool,           # Is market favorite
        "odds_percentile": float,      # Where in field (0-100)
    }
```

**Key features for hybrid model**:

1. **`q_vigfree`** - Market's vig-free probability
2. **`market_rank`** - Position in betting (1=fav, 2=2nd fav, etc.)
3. **`decimal_odds`** - For edge calculation
4. **`overround`** - Market efficiency indicator
5. **`volume_traded`** - Confidence indicator (optional)

---

### **Phase 3: Hybrid Selection Logic**

Instead of just comparing probabilities, use **market context**:

```python
# tools/score_hybrid.py

def score_hybrid(race_df, model):
    """
    Hybrid scoring: ability model + market filtering.
    """
    
    # 1. Predict with ability model
    p_model = model.predict(race_df[ABILITY_FEATURES])
    
    # 2. Get market features
    q_market = race_df["q_vigfree"]
    market_rank = race_df["market_rank"]
    odds = race_df["decimal_odds"]
    overround = race_df["overround"]
    
    # 3. Calculate disagreement metrics
    disagreement = p_model / q_market  # Ratio
    edge_absolute = p_model - q_market  # Absolute difference
    
    # 4. Multi-factor filtering
    
    # GATE 1: Significant disagreement
    passes_disagreement = disagreement >= 1.4  # Model thinks 40%+ higher
    
    # GATE 2: Not on favorite (even if model likes it)
    passes_rank = market_rank >= 3  # 3rd favorite or worse
    
    # GATE 3: Absolute edge minimum
    passes_edge = edge_absolute >= 0.04  # 4pp minimum
    
    # GATE 4: Odds range (where model works)
    passes_odds = (odds >= 4.0) & (odds <= 15.0)
    
    # GATE 5: Market quality (not crazy overround)
    passes_market = (overround >= 1.02) & (overround <= 1.30)
    
    # GATE 6: Not extreme longshot (model unreliable)
    passes_confidence = odds <= 20.0
    
    # Combine all gates
    qualifies = (
        passes_disagreement & 
        passes_rank & 
        passes_edge & 
        passes_odds & 
        passes_market & 
        passes_confidence
    )
    
    return qualifies
```

**Key differences from Path A**:
- ✅ Uses `market_rank` to avoid favorites
- ✅ Uses `disagreement ratio` (not just edge)
- ✅ Uses `overround` to assess market quality
- ✅ Allows 4-15 odds (not just 8-12)
- ✅ Should get 200-500 bets/year (vs 10-30)

---

### **Phase 4: Adaptive Blending Based on Market Signals**

Instead of fixed lambda by odds, **adapt based on market quality**:

```python
def get_adaptive_lambda(odds, market_rank, volume, overround):
    """
    Adjust blending based on market quality signals.
    
    Trust market MORE when:
    - Favorite or 2nd favorite (heavy money)
    - High volume traded
    - Low overround (competitive market)
    
    Trust model MORE when:
    - Mid-field horse (rank 4-8)
    - Lower volume
    - Higher overround (less competitive)
    """
    
    # Base lambda by odds
    if odds < 5.0:
        base_lambda = 0.40
    elif odds < 8.0:
        base_lambda = 0.30
    elif odds < 12.0:
        base_lambda = 0.20
    else:
        base_lambda = 0.45
    
    # Adjust for market rank
    if market_rank == 1:  # Favorite
        base_lambda += 0.20  # Trust market much more
    elif market_rank == 2:  # 2nd favorite
        base_lambda += 0.10  # Trust market more
    elif market_rank >= 6:  # Outsider
        base_lambda -= 0.10  # Trust model more
    
    # Adjust for overround (market efficiency)
    if overround < 1.10:  # Very competitive
        base_lambda += 0.10
    elif overround > 1.20:  # Less competitive
        base_lambda -= 0.05
    
    # Clamp to [0.1, 0.7]
    return max(0.1, min(0.7, base_lambda))
```

**Example**:
```
Horse A: 6.0 odds, rank 5, overround 1.15
  → lambda = 0.30 (base) - 0.10 (outsider) = 0.20
  → 80% model, 20% market (trust model)

Horse B: 4.0 odds, rank 1, overround 1.08
  → lambda = 0.40 (base) + 0.20 (favorite) + 0.10 (efficient) = 0.70
  → 30% model, 70% market (trust market)
```

---

### **Phase 5: Expected Value with Market Context**

```python
def calculate_hybrid_ev(p_model, q_market, odds, market_rank, lam):
    """
    Calculate EV considering market context.
    """
    
    # Blend
    p_blend = blend_to_market(p_model, q_market, lam)
    
    # Calculate EV
    ev_base = p_blend * (odds - 1) * (1 - COMMISSION) - (1 - p_blend)
    
    # Penalty for favorites (even if EV looks good)
    if market_rank <= 2:
        ev_adjusted = ev_base * 0.5  # Halve EV estimate (be skeptical)
    else:
        ev_adjusted = ev_base
    
    return ev_adjusted, p_blend
```

**Why penalize favorites**:
- Market is most efficient on favorites
- Even if model sees edge, likely to be wrong
- Commission eats into thin margins
- Better to be conservative

---

### **Phase 6: Selection Rules (Hybrid)**

```python
# Hybrid selection criteria

def select_bets_hybrid(df, model):
    """
    Hybrid bet selection.
    """
    
    # Predict
    df["p_model"] = model.predict(df[ABILITY_FEATURES])
    
    # Calculate metrics
    df["disagreement_ratio"] = df["p_model"] / df["q_vigfree"]
    df["edge_absolute"] = df["p_model"] - df["q_vigfree"]
    
    # Adaptive blending
    df["lambda"] = df.apply(
        lambda r: get_adaptive_lambda(
            r["decimal_odds"], 
            r["market_rank"], 
            r.get("volume_traded", 0),
            r["overround"]
        ),
        axis=1
    )
    
    df["p_blend"] = df.apply(
        lambda r: blend_to_market(r["p_model"], r["q_vigfree"], r["lambda"]),
        axis=1
    )
    
    # Calculate EV
    df["ev_adjusted"] = df.apply(
        lambda r: calculate_hybrid_ev(
            r["p_model"], r["q_vigfree"], r["decimal_odds"], 
            r["market_rank"], r["lambda"]
        )[0],
        axis=1
    )
    
    # FILTERS (all must pass)
    
    candidates = df[
        (df["disagreement_ratio"] >= 1.3) &     # Model 30%+ higher than market
        (df["market_rank"] >= 3) &              # Not favorite or 2nd fav
        (df["edge_absolute"] >= 0.03) &         # At least 3pp edge
        (df["decimal_odds"] >= 4.0) &           # Skip short prices
        (df["decimal_odds"] <= 15.0) &          # Skip longshots
        (df["ev_adjusted"] >= 0.02) &           # Positive EV after adjustments
        (df["overround"] <= 1.25)               # Reasonable market
    ]
    
    # Top-1 per race by edge
    candidates = candidates.sort_values(["race_id", "edge_absolute"], ascending=[True, False])
    candidates = candidates.groupby("race_id").head(1)
    
    return candidates
```

---

### **Phase 7: Backtest the Hybrid**

Expected improvements over Path A:

| Metric | Path A | Hybrid (Expected) |
|--------|--------|-------------------|
| **Bets/Year** | 10-30 | 200-500 |
| **Avg Odds** | 9-10 | 6-10 |
| **ROI** | +50-100% | +5-15% |
| **Volume** | Too low | ✅ Viable |
| **Statistical confidence** | Low | ✅ High |

**Why hybrid should work better**:
1. **More bets** by relaxing pure ability constraints
2. **Market rank filter** prevents favorite trap
3. **Disagreement ratio** ensures we only bet when truly different from market
4. **Adaptive blending** uses market context intelligently

---

## 🛠️ **Implementation Steps**

### **Step 1: Create Market Features Module**

```bash
# File: src/giddyup/data/market.py
```

```python
import polars as pl
from sqlalchemy import create_engine, text
import os

def get_market_snapshot(
    race_ids: list,
    snapshot_time: str = "T-60",
    conn_str: str = None
) -> pl.DataFrame:
    """
    Get market snapshot features for races.
    
    Args:
        race_ids: List of race IDs
        snapshot_time: When to snapshot (T-60, T-30, etc.)
        
    Returns:
        DataFrame with market features per horse
    """
    
    engine = create_engine(conn_str or os.getenv("PG_DSN"))
    
    # Parse snapshot time (e.g., "T-60" = 60 minutes before)
    minutes = int(snapshot_time.replace("T-", ""))
    
    sql = text("""
    WITH target_times AS (
        SELECT 
            race_id,
            off_time,
            off_time - INTERVAL :minutes MINUTE AS target_time
        FROM racing.races
        WHERE race_id = ANY(:race_ids)
    ),
    snapshots AS (
        SELECT 
            s.race_id,
            s.horse_id,
            s.decimal_odds,
            s.source,
            s.snapped_at,
            ABS(EXTRACT(EPOCH FROM (s.snapped_at - t.target_time))) AS time_diff
        FROM market.price_snapshots s
        JOIN target_times t USING (race_id)
        WHERE s.snapped_at BETWEEN t.target_time - INTERVAL '15 minutes'
                                AND t.target_time + INTERVAL '15 minutes'
    ),
    best_snapshot AS (
        SELECT 
            race_id,
            horse_id,
            decimal_odds,
            ROW_NUMBER() OVER (PARTITION BY race_id, horse_id ORDER BY time_diff) AS rn
        FROM snapshots
    )
    SELECT race_id, horse_id, decimal_odds
    FROM best_snapshot
    WHERE rn = 1 AND decimal_odds >= 1.01
    """)
    
    with engine.begin() as cx:
        df = pl.read_database(sql, connection=cx.connection, 
                             params={"race_ids": race_ids, "minutes": minutes})
    
    # Calculate market features
    
    # 1. Market rank (1=favorite)
    df = df.with_columns([
        pl.col("decimal_odds").rank(method="min").over("race_id").alias("market_rank")
    ])
    
    # 2. Vig-free probability
    df = df.with_columns([
        (1.0 / pl.col("decimal_odds")).alias("q_market")
    ])
    
    overround = df.group_by("race_id").agg([
        pl.col("q_market").sum().alias("overround")
    ])
    
    df = df.join(overround, on="race_id")
    
    df = df.with_columns([
        (pl.col("q_market") / pl.col("overround")).alias("q_vigfree")
    ])
    
    # 3. Is favorite
    df = df.with_columns([
        (pl.col("market_rank") == 1).alias("is_favorite")
    ])
    
    # 4. Odds percentile in field
    df = df.with_columns([
        (pl.col("market_rank") / pl.col("market_rank").max().over("race_id") * 100)
            .alias("odds_percentile")
    ])
    
    return df
```

---

### **Step 2: Create Hybrid Scorer**

```bash
# File: tools/score_hybrid.py
```

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
import mlflow
from datetime import datetime, timedelta

from giddyup.data.build import build_training_data
from giddyup.data.market import get_market_snapshot
from giddyup.data.feature_lists import ABILITY_FEATURES
from giddyup.price.value import blend_to_market, logit, invlogit

# ===== Hybrid Configuration =====

# Disagreement thresholds
MIN_DISAGREEMENT_RATIO = 1.30  # Model must be 30%+ higher than market
MIN_EDGE_ABSOLUTE = 0.03       # Minimum 3pp edge

# Market rank filters
MAX_RANK = 8                    # Don't bet on horses worse than 8th favorite
MIN_RANK = 3                    # Don't bet favorite or 2nd favorite

# Odds range
ODDS_MIN = 4.0
ODDS_MAX = 15.0

# Market quality
MAX_OVERROUND = 1.25            # Skip uncompetitive markets

# EV after penalties
MIN_EV_ADJUSTED = 0.02

# Staking
KELLY_FRACTION = 0.10
MAX_STAKE = 0.3
MAX_BETS_PER_RACE = 1
MAX_DAILY_STAKE = 15.0


def get_adaptive_lambda(row):
    """Calculate blending parameter based on market context."""
    odds = row["decimal_odds"]
    rank = row["market_rank"]
    overround = row["overround"]
    
    # Base by odds
    if odds < 5.0:
        lam = 0.40
    elif odds < 8.0:
        lam = 0.30
    elif odds < 12.0:
        lam = 0.20
    else:
        lam = 0.45
    
    # Adjust for rank (trust market more on favorites)
    if rank == 1:
        lam += 0.25
    elif rank == 2:
        lam += 0.15
    elif rank >= 6:
        lam -= 0.10
    
    # Adjust for market efficiency
    if overround < 1.10:
        lam += 0.10  # Very efficient, trust more
    elif overround > 1.20:
        lam -= 0.05  # Less efficient, trust model
    
    return max(0.10, min(0.70, lam))


def score_race_hybrid(race_id, target_date, model):
    """
    Score a single race with hybrid approach.
    """
    
    # 1. Get ability features
    df = build_training_data(
        date_from=target_date,
        date_to=target_date,
        output_path=None
    )
    
    df = df.filter(pl.col("race_id") == race_id)
    
    # 2. Predict with ability model
    X = df.select(ABILITY_FEATURES).fill_null(0)
    p_model = model.predict(X.to_pandas())
    
    df = df.with_columns(pl.Series("p_model", p_model))
    
    # 3. Get market features
    market_df = get_market_snapshot([race_id], "T-60")
    
    df = df.join(market_df, on=["race_id", "horse_id"], how="inner")
    
    # 4. Calculate disagreement
    df = df.with_columns([
        (pl.col("p_model") / pl.col("q_vigfree")).alias("disagreement_ratio"),
        (pl.col("p_model") - pl.col("q_vigfree")).alias("edge_absolute"),
    ])
    
    # 5. Adaptive blending
    df_pd = df.to_pandas()
    df_pd["lambda"] = df_pd.apply(get_adaptive_lambda, axis=1)
    df_pd["p_blend"] = df_pd.apply(
        lambda r: blend_to_market(r["p_model"], r["q_vigfree"], r["lambda"]),
        axis=1
    )
    
    df = pl.from_pandas(df_pd)
    
    # 6. Calculate EV with favorite penalty
    def calc_ev_adjusted(row):
        p = row["p_blend"]
        odds = row["decimal_odds"]
        rank = row["market_rank"]
        
        ev_base = p * (odds - 1) * 0.98 - (1 - p)
        
        # Penalize favorites
        if rank <= 2:
            ev_adjusted = ev_base * 0.5
        else:
            ev_adjusted = ev_base
        
        return ev_adjusted
    
    df_pd = df.to_pandas()
    df_pd["ev_adjusted"] = df_pd.apply(calc_ev_adjusted, axis=1)
    df = pl.from_pandas(df_pd)
    
    # 7. Apply all gates
    candidates = df.filter(
        (pl.col("disagreement_ratio") >= MIN_DISAGREEMENT_RATIO) &
        (pl.col("market_rank") >= MIN_RANK) &
        (pl.col("market_rank") <= MAX_RANK) &
        (pl.col("edge_absolute") >= MIN_EDGE_ABSOLUTE) &
        (pl.col("decimal_odds") >= ODDS_MIN) &
        (pl.col("decimal_odds") <= ODDS_MAX) &
        (pl.col("overround") <= MAX_OVERROUND) &
        (pl.col("ev_adjusted") >= MIN_EV_ADJUSTED)
    )
    
    # 8. Top-1 by edge
    if len(candidates) > 0:
        candidates = candidates.sort("edge_absolute", descending=True).head(1)
    
    return candidates
```

---

### **Step 3: Backtest Hybrid Approach**

```bash
# File: tools/backtest_hybrid.py
```

```python
def backtest_hybrid(date_from="2024-01-01", date_to="2025-10-16"):
    """
    Backtest hybrid approach on holdout data.
    """
    
    # Load test data
    df = build_training_data(date_from, date_to)
    
    # Load Path A model
    model = mlflow.pyfunc.load_model("runs:/.../ensemble")
    
    # Get market features
    race_ids = df["race_id"].unique().to_list()
    market_df = get_market_snapshot(race_ids, "T-60")
    
    # Join
    df = df.join(market_df, on=["race_id", "horse_id"], how="inner")
    
    # Score with hybrid logic
    bets = select_bets_hybrid(df, model)
    
    # Calculate results
    results = analyze_results(bets)
    
    return results
```

**Expected results**:
```
Bets: 200-500/year (vs 10-30 for Path A)
Avg Odds: 6-10
ROI: +5-15% (vs +50-100% for Path A, but more volume)
Win Rate: 15-25%
```

---

## 📊 **Expected Hybrid Performance**

### **Comparison to Path A**

| Metric | Path A | Hybrid (Projected) | Why Different |
|--------|--------|-------------------|---------------|
| **Bets/Year** | 10-30 | 200-500 | More permissive filters |
| **Avg Odds** | 9-10 | 6-10 | Wider range (4-15) |
| **ROI** | +50-100% | +5-15% | Lower per bet, more volume |
| **Total P&L** | +5-30u | +10-75u | More bets = more total |
| **Validation** | Hard (few bets) | ✅ Easier (many bets) |
| **Deployable** | ⚠️ Marginal | ✅ Yes |

---

### **By Odds Band (Projected)**

| Odds | Gates | Expected Bets | Est. ROI |
|------|-------|---------------|----------|
| 4-5 | Strict (rank≥3, disagree≥1.4) | 50-100 | +3-8% |
| 5-8 | Moderate (rank≥3, disagree≥1.3) | 80-150 | +5-12% |
| 8-12 | Easier (rank≥3, disagree≥1.2) | 50-150 | +8-18% |
| 12-15 | Strict (disagree≥1.5) | 20-50 | +5-15% |

**Total**: 200-450 bets/year

---

## 🔧 **Implementation Timeline**

### **Week 1: Build Core**
- Day 1-2: Create `market.py` module (market snapshot queries)
- Day 3-4: Create `score_hybrid.py` with all gates
- Day 5: Create `backtest_hybrid.py`

### **Week 2: Test & Tune**
- Day 1: Run backtest on 2024-2025
- Day 2-3: Tune thresholds (disagreement ratio, edge mins)
- Day 4: Test on sample races (verify outputs)
- Day 5: Documentation

### **Week 3: Deploy Paper Trading**
- Set up daily scoring job
- Run for 1 month without betting
- Track: signals, results, calibration
- Compare to backtest expectations

### **Week 4+: Decision**
- If ROI > +3% after 50+ bets → Deploy with small stakes
- If ROI < 0% → Retune or abandon
- If ROI 0-3% → Continue paper trading

---

## 📝 **Code Structure**

```
giddyup/
├── src/giddyup/
│   ├── data/
│   │   ├── market.py          ← NEW: Market feature queries
│   │   └── hybrid.py          ← NEW: Hybrid scoring logic
│   └── models/
│       └── hybrid_selector.py ← NEW: Multi-gate selection
├── tools/
│   ├── score_hybrid.py        ← NEW: Daily hybrid scoring
│   ├── backtest_hybrid.py     ← NEW: Hybrid backtest
│   └── train_model.py         ← UNCHANGED (still Path A training)
```

---

## 🎯 **Key Differences from Path A**

| Aspect | Path A | Hybrid |
|--------|--------|--------|
| **Training** | Ability only | ✅ Same (ability only) |
| **Prediction** | p_model from ability | ✅ Same |
| **Market Usage** | Only for q_vigfree | ✅ Plus rank, overround, volume |
| **Selection** | Edge threshold only | ✅ Multi-factor (disagree + rank + edge) |
| **Blending** | Fixed by odds | ✅ Adaptive (by rank + efficiency) |
| **Filters** | Simple (edge, odds) | ✅ Complex (6 gates) |
| **Volume** | 10-30/year | ✅ 200-500/year |

---

## 💡 **Why Hybrid Should Work**

### **1. Keep Path A's Independence**

Training still uses **NO market features** → model can disagree with market.

### **2. Add Market Intelligence**

At scoring, use market to:
- **Avoid favorite trap** (rank ≥ 3)
- **Assess market quality** (overround check)
- **Calibrate confidence** (adaptive blending)
- **Validate opportunities** (disagreement ratio)

### **3. Better Volume/ROI Balance**

```
Path A: 10 bets at +100% ROI = +10 units total
Hybrid: 300 bets at +8% ROI = +24 units total

Hybrid has:
  - 3x more profit potential
  - Better statistical validation
  - More operational (regular activity)
```

---

## 🚨 **Potential Risks**

### **1. Market Dependency**

Using market rank/overround at scoring means:
- Partial dependency on market
- Less "pure" than Path A
- Could lose some independence

**Mitigation**: Use market as **filter**, not **feature** in prediction.

### **2. Overfitting to Backtest**

Tuning many gates on 2024-2025 could overfit.

**Mitigation**: 
- Use simple, interpretable rules
- Validate on separate period (2023?)
- Paper trade before live

### **3. Market Changes**

Market behavior could shift:
- Odds ranges change
- Efficiency improves
- Our edge disappears

**Mitigation**:
- Monthly monitoring
- Retrain every 6 months
- Be ready to stop if edge fades

---

## 📊 **Success Criteria for Hybrid**

After backtesting on 2024-2025:

| Metric | Target | Why |
|--------|--------|-----|
| **Bets** | 200-500 | Enough for validation |
| **ROI** | > +3% | Profitable after commission |
| **Avg Odds** | 6-10 | Not all favorites or longshots |
| **Win Rate** | 18-25% | Above expectation for odds |
| **Monthly positive** | > 50% | Consistency |
| **Max DD** | < 20u | Manageable risk |

If **all criteria met** → Deploy to paper trading.

---

## 🛠️ **Quick Start Implementation**

Want me to build it? I can:

1. **Create `market.py`** - Market feature extraction
2. **Create `score_hybrid.py`** - Hybrid scoring with all gates
3. **Create `backtest_hybrid.py`** - Run on 2024-2025
4. **Tune thresholds** - Optimize for target metrics
5. **Show real examples** - Actual 2024-2025 bets with outcomes

**Timeline**: 2-3 hours to build and test  
**Result**: Know if hybrid approach is viable

---

## ❓ **Decision Points**

### **Question 1: Volume Target**

How many bets/year do you want?
- **Option A**: 50-100 (very selective) → Tighter gates
- **Option B**: 200-500 (moderate) → Balanced gates ⭐ **Recommended**
- **Option C**: 500-1000 (active) → Looser gates

### **Question 2: ROI Target**

What ROI is acceptable?
- **Option A**: +15%+ (aggressive) → Very tight, lower volume
- **Option B**: +5-15% (realistic) → Moderate, good volume ⭐ **Recommended**
- **Option C**: +2-5% (conservative) → Easier, higher volume

### **Question 3: Independence Level**

How much market influence is OK?
- **Option A**: Minimal (λ ≤ 0.30) → More independent, harder
- **Option B**: Moderate (λ ≤ 0.50) → Balanced ⭐ **Recommended**
- **Option C**: High (λ ≤ 0.70) → Less independent, easier

---

## 🎯 **My Recommendation**

**Build hybrid with**:
- **Target**: 200-500 bets/year, +5-15% ROI
- **Gates**: Disagreement≥1.3, Rank 3-8, Edge≥3pp, Odds 4-15
- **Blending**: Adaptive (λ=0.15-0.50 based on context)
- **Timeline**: 2-3 hours to build, test, and see results

**This gives you**:
- ✅ Enough bets to validate (200-500 vs 10-30)
- ✅ Realistic ROI (+5-15% vs +100%)
- ✅ Operational viability (regular activity)
- ✅ Statistical confidence (large sample)

---

## 🚀 **Want Me to Build It Now?**

I can implement the full hybrid model and run backtest today:

1. Create market features module
2. Build hybrid scorer with all 6 gates
3. Run backtest on 2024-2025
4. Show you results (bets, ROI, examples)
5. If good → Create production scoring script

**Estimated time**: 2-3 hours  
**Expected outcome**: Know if hybrid is viable or not

**Shall I proceed?** Or do you have questions first?

