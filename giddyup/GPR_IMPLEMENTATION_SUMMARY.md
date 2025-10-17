# GPR Implementation Summary

## ✅ What We Built

### 1. **GiddyUp Performance Rating (GPR) System**
   - **Location**: `src/giddyup/ratings/gpr.py`
   - **Purpose**: Creates a pounds-scale performance rating comparable to BHA Official Rating
   - **Components**:
     - Distance bands (5-6f, 7-9f, 10-12f, 12f+)
     - Lbs per length adjustment by distance
     - Context de-biasing (course/going/distance)
     - Recency weighting (exponential decay, 120-day half-life)
     - Shrinkage toward prior (Empirical Bayes)
     - Calibration to OR scale

### 2. **GPR Features Added to Model**
   - `gpr`: The GiddyUp Performance Rating
   - `gpr_minus_or`: GPR − Official Rating (our edge vs. official handicapper)
   - `gpr_minus_rpr`: GPR − Racing Post Rating (our edge vs. RPR)
   - `gpr_sigma`: Uncertainty/confidence in GPR

### 3. **Feature Engineering Pipeline**
   - **Location**: `src/giddyup/data/build.py`
   - **Enhancements**:
     - Integrated GPR computation into feature building
     - Proper temporal filtering (no look-ahead bias)
     - Computes GPR per horse using only past runs
     - Added GPR features to ABILITY_FEATURES list

### 4. **Training Pipeline**
   - **Location**: `tools/train_model.py`
   - **Features**:
     - Prints complete feature list for verification
     - Guards against market feature leakage
     - Checks for suspicious keywords (odds, price, etc.)
     - Training: 2006-2023 (18 years)
     - Testing: 2024-2025 (22 months, pure OOT)

### 5. **Scoring & Publishing Pipeline**
   - **Location**: `tools/score_publish.py`
   - **Workflow**:
     1. Load ability-only model from MLflow
     2. Fetch today's races with GPR features
     3. Join T-60 market snapshot
     4. Compute vig-free market probabilities
     5. Calculate edge: `p_model − q_vigfree`
     6. Calculate EV after commission
     7. Filter by thresholds (edge ≥ 3pp, odds ≥ 2.0, EV ≥ 2%)
     8. Size stakes using fractional Kelly
     9. Publish signals to `modeling.signals`

### 6. **Enhanced Backtest Script**
   - **Location**: `tools/backtest_value_gpr.py`
   - **Analysis Dimensions**:
     - **By GPR Delta**: Performance by `gpr_minus_or` buckets
       - Expect: GPR >> OR → positive ROI
       - Expect: GPR << OR → negative ROI (avoid)
     - **By Odds Bands**: 2-3, 3-5, 5-8, 8-15, 15+
     - **By Month**: Stability check over 22 months
     - **Overall**: ROI, Max Drawdown, Sharpe Ratio
   - **Metrics**:
     - P&L after 2% commission
     - Win rate vs expected
     - Closing Line Value (if available)

### 7. **Price Race Tool**
   - **Location**: `tools/price_race.py`
   - **Usage**:
     ```bash
     # By date/course/time
     python price_race.py --date 2025-10-18 --course "Ascot" --time "14:30"
     
     # By race ID
     python price_race.py --race-id 12345
     ```
   - **Output**:
     - Fair odds vs market odds for every horse
     - GPR and GPR-OR delta per horse
     - Value bets highlighted (edge, EV, recommended stake)

---

## 🎯 Key Design Principles

### 1. **No Data Leakage**
   - **Training**: Uses ONLY ability features (no market data)
   - **Scoring**: Joins market data at T-60 (before race)
   - **GPR**: Computed from PAST runs only (no future information)

### 2. **Value Betting Strategy**
   - **Not**: Trying to predict winners better than market
   - **Instead**: Finding MISPRICED horses where our probability > market probability
   - **Edge Calculation**: `edge = p_model − q_market_vigfree`
   - **Filtering**: Require edge ≥ 3pp AND odds ≥ 2.0 AND EV ≥ 2%

### 3. **Calibration Focus**
   - **AUC**: Not the goal (would be ~0.95 with market features)
   - **Log Loss**: The critical metric for probability calibration
   - **Isotonic Calibration**: Applied to ensure probabilities are accurate
   - **Expected**: AUC ~0.65-0.72 with ability-only features (this is GOOD)

### 4. **GPR as Core Feature**
   - **Why**: Official Ratings lag behind true ability
   - **Hypothesis**: Horses with `gpr_minus_or > 0` are underrated → value
   - **Validation**: Backtest should show positive ROI for high GPR-OR delta bets

---

## 📊 Expected Results

### Training Metrics (Ability-Only Model)
- **AUC**: 0.65 - 0.72 (normal for ability-only)
- **Log Loss**: 0.45 - 0.55 (lower is better)
- **Top Features**: GPR, gpr_minus_or, official_rating, RPR, trainer_sr, jockey_sr

### Backtest Metrics (2024-2025 on filtered bets)
- **Bet Volume**: ~500-2000 bets (depends on thresholds)
- **Avg Odds**: 6-10 (filtering out short-priced favorites)
- **ROI Target**: +3% to +10% (after 2% commission)
- **Max Drawdown**: Monitor and size stakes accordingly
- **Sharpe**: Should be positive if edge is real

### GPR Delta Analysis
Expected pattern in backtest:
- `gpr_minus_or < -10`: Negative ROI (overrated horses)
- `gpr_minus_or -5 to 0`: Break-even
- `gpr_minus_or 0 to +5`: Slightly positive ROI
- `gpr_minus_or +5 to +10`: Strong positive ROI
- `gpr_minus_or > +10`: Best ROI (underrated horses)

---

## 🚀 Next Steps

### Immediate (Once Training Completes)
1. **Review Training Logs**:
   - Verify feature list includes GPR features
   - Check AUC is in expected range (0.65-0.72)
   - Inspect feature importances (GPR should rank high)

2. **Register Model in MLflow**:
   ```python
   mlflow ui --backend-store-uri sqlite:///mlflow.db
   # Navigate to model → register → promote to "Production"
   ```

3. **Run Backtest**:
   ```bash
   python tools/backtest_value_gpr.py
   ```
   - Check overall ROI > +2%
   - Validate GPR-OR pattern
   - Ensure no major monthly swings

4. **Test Price Race Tool**:
   ```bash
   # Find a recent race
   python tools/price_race.py --date 2024-10-01 --course "Ascot" --time "14:30"
   ```

### Refinements (After Initial Validation)
1. **Dynamic Thresholds by Odds**:
   - 2-3 odds: require edge ≥ 5pp
   - 3-6 odds: require edge ≥ 3pp
   - 6+ odds: require edge ≥ 2pp

2. **Confidence-Weighted Staking**:
   - Scale Kelly by `1 / gpr_sigma` (higher confidence → larger bets)

3. **Segmented Calibration**:
   - Fit separate isotonic calibrators per odds band
   - Or per GPR bucket

4. **Per-Race Cap**:
   - Max 1-2 selections per race
   - Or dutch top 2 under a race-level stake cap

5. **Close Forecaster** (Advanced):
   - Train lightweight model to predict closing odds from T-60 features
   - Filter to horses likely to shorten (beat the close)

### Production Deployment
1. **Daily Scoring Schedule** (Prefect/Airflow):
   - Run at 08:00 Europe/Madrid
   - Score tomorrow's races
   - Publish signals to DB

2. **Risk Controls**:
   - Daily stake cap: max 10-20 units/day
   - Auto-stop if daily P&L < -5 units
   - Liquidity checks: require min £X available at best back

3. **Monitoring Dashboard**:
   - Daily: bet count, avg odds, avg edge, P&L
   - Weekly: ROI by odds band, by GPR bucket, calibration curves
   - Monthly: Sharpe, max DD, CLV

4. **Data Quality Checks** (Great Expectations):
   - GPR not null for >95% of runners
   - T-60 snapshot within 30-90 min of off
   - Overround per race in [1.0, 1.4]

---

## 🛠️ File Structure

```
giddyup/
├── src/giddyup/
│   ├── ratings/
│   │   ├── __init__.py
│   │   └── gpr.py                 # GPR computation
│   ├── data/
│   │   ├── build.py               # Feature engineering (with GPR)
│   │   └── feature_lists.py       # ABILITY_FEATURES (with GPR)
│   ├── models/
│   │   └── trainer.py             # Training pipeline
│   ├── price/
│   │   └── value.py               # EV, Kelly, fair odds
│   └── publish/
│       └── signals.py             # DB upsert
├── tools/
│   ├── train_model.py             # End-to-end training
│   ├── score_publish.py           # Daily scoring pipeline
│   ├── backtest_value_gpr.py      # Enhanced backtest with GPR analysis
│   ├── price_race.py              # Single race pricing tool
│   ├── test_gpr.py                # GPR unit tests
│   └── migrate.py                 # DB schema setup
└── migrations/
    └── 001_modeling_schema.sql    # modeling.models, signals, bets
```

---

## 📝 Configuration (.env)

```bash
PG_DSN=postgresql+psycopg://postgres:password@localhost:5432/horse_db
TZ=Europe/Madrid

# Thresholds (optional, defaults shown)
EDGE_MIN=0.03          # 3pp minimum edge
ODDS_MIN=2.0           # Avoid heavy favorites
EV_MIN=0.02            # 2% minimum EV after commission
COMMISSION=0.02        # 2% exchange fee (Betfair: 5%, so 0.05)
KELLY_FRACTION=0.25    # Quarter Kelly
MAX_STAKE=0.5          # Max 0.5 units per bet
```

---

## ✅ Validation Checklist

### Training
- [ ] Feature list printed (should include gpr, gpr_minus_or, gpr_minus_rpr, gpr_sigma)
- [ ] No market features in training (guard passed)
- [ ] AUC in range 0.65-0.72
- [ ] Log Loss < 0.55
- [ ] GPR features in top 10 importances

### Backtest (2024-2025)
- [ ] Overall ROI > +2% after commission
- [ ] GPR-OR pattern: higher delta → higher ROI
- [ ] Avg odds 6-10 (not all short favorites)
- [ ] Bet volume reasonable (~500-2000)
- [ ] No catastrophic monthly losses
- [ ] Positive Sharpe ratio

### Tools
- [ ] `price_race.py` runs without error
- [ ] Shows fair vs market odds
- [ ] Highlights value bets correctly
- [ ] `score_publish.py` writes to modeling.signals
- [ ] Signals have all required fields

### Model Registry
- [ ] Model registered in MLflow
- [ ] Model promoted to Production
- [ ] Artifacts include isotonic calibrator
- [ ] Metrics logged (AUC, Log Loss, etc.)

---

## 🎉 Success Criteria

**The GPR implementation is successful if:**

1. **Model trains** with GPR features and achieves reasonable calibration (Log Loss < 0.55)
2. **Backtest shows positive ROI** (>+2%) on 2024-2025 holdout data
3. **GPR-OR delta predicts value**: Higher `gpr_minus_or` → higher ROI
4. **Tools work end-to-end**: Can score races, show value, publish signals
5. **No data leakage**: All guards pass, no market features in training

If all 5 criteria are met, the system is ready for **paper trading** (tracking signals without real money) for 1-2 months before considering real deployment.

---

## 📚 Key References

- **Betfair Commission**: Typically 2-5% on winning bets (market-dependent)
- **Kelly Criterion**: Optimal stake sizing for +EV bets
- **Isotonic Calibration**: Ensures probabilities match actual win rates
- **Vig-Free Probability**: Removes bookmaker margin: `q_vigfree = q / sum(q)`
- **Expected Value**: `EV = p*(O-1)*(1-commission) - (1-p)`

---

*Generated: October 17, 2025*
*Branch: `feat/gpr-rating`*

