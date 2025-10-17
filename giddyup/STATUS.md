# GPR Implementation Status

**Branch**: `feat/gpr-rating`  
**Date**: October 17, 2025  
**Status**: ✅ **TRAINING IN PROGRESS**

---

## ✅ Completed Components

### 1. **GPR Rating System** 
- [x] `src/giddyup/ratings/gpr.py` - Full GPR computation
- [x] Distance bands and lbs-per-length logic
- [x] Context de-biasing (course/going/distance)
- [x] Recency weighting (120-day half-life)
- [x] Empirical Bayes shrinkage
- [x] Calibration to Official Rating scale

### 2. **Feature Engineering**
- [x] GPR integrated into `build.py`
- [x] GPR features added to `ABILITY_FEATURES`:
  - `gpr` - The rating
  - `gpr_minus_or` - GPR vs Official Rating delta
  - `gpr_minus_rpr` - GPR vs Racing Post Rating delta
  - `gpr_sigma` - Uncertainty/confidence

### 3. **Training Pipeline**
- [x] Feature list printing and verification
- [x] Market leakage guards
- [x] 2006-2023 training window
- [x] 2024-2025 test window (pure OOT)
- [x] Currently training (Fold 1/5, Log Loss 0.157)

### 4. **Scoring & Publishing**
- [x] `tools/score_publish.py` - Daily scoring pipeline
  - Loads ability-only model
  - Joins T-60 market snapshot
  - Computes vig-free probabilities
  - Calculates edge and EV
  - Filters by thresholds
  - Publishes to `modeling.signals`

### 5. **Backtesting**
- [x] `tools/backtest_value_gpr.py` - Enhanced backtest
  - Performance by `gpr_minus_or` buckets
  - Performance by odds bands
  - Monthly stability analysis
  - ROI, Max DD, Sharpe metrics

### 6. **Race Pricing Tool**
- [x] `tools/price_race.py` - Single race analysis
  - Score any race by date/course/time or race_id
  - Show fair odds vs market odds
  - Display GPR and GPR-OR deltas
  - Highlight value bets

### 7. **Risk Controls**
- [x] `src/giddyup/risk/controls.py` - Risk management
  - Per-race betting caps
  - Daily stake limits
  - Auto-stop on losses
  - Liquidity checks

### 8. **Monitoring**
- [x] `src/giddyup/monitoring/quality.py` - Data quality
  - GPR coverage checks
  - Market snapshot timing validation
  - Overround range checks
  - Feature completeness validation

---

## 🏃 Current Training Progress

**Log**: `training_gpr_20251017_103026.log`

```
Feature Engineering: ✅ COMPLETE
   - 2,078,106 rows × 71 columns
   - GPR computed for 187,548 horses
   - 28 ability features selected

Training: 🏃 IN PROGRESS
   - Fold 1/5: Round 1200+
   - Log Loss: 0.157 (decreasing)
   - Train: 1,888,760 runners (2006-2023)
   - Test: 189,346 runners (2024-2025)
   - ETA: ~30-60 minutes for full training
```

---

## 📊 Feature List (28 Total)

**Ability Features** (NO MARKET DATA):
1. official_rating
2. racing_post_rating
3. best_rpr_last_3
4. **gpr** ⭐
5. **gpr_minus_or** ⭐
6. **gpr_minus_rpr** ⭐
7. **gpr_sigma** ⭐
8. days_since_run
9. last_pos
10. avg_btn_last_3
11. career_runs
12. career_strike_rate
13. trainer_sr_total
14. trainer_wins_total
15. trainer_runs_total
16. jockey_sr_total
17. jockey_wins_total
18. jockey_runs_total
19. runs_at_course
20. wins_at_course
21. field_size
22. class_numeric
23. is_flat
24. is_aw
25. dist_f
26. draw
27. age
28. lbs

---

## 🎯 Next Steps (After Training Completes)

### 1. **Review Training Results**
```bash
# Wait for training to complete (~30-60 min)
tail -f training_gpr_20251017_103026.log

# Expected:
# - AUC: 0.65-0.72 (ability-only, this is good!)
# - Log Loss: 0.45-0.55
# - GPR features in top importances
```

### 2. **Register Model in MLflow**
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
# Navigate to experiment → select run → register model
# Promote to "Production" stage
```

### 3. **Run Backtest on 2024-2025**
```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/backtest_value_gpr.py
```

**Expected Results**:
- Overall ROI: +3% to +10% (after 2% commission)
- GPR-OR pattern: higher delta → higher ROI
- Avg odds: 6-10 (not all favorites)
- Bet volume: 500-2000 bets

### 4. **Test Race Pricing Tool**
```bash
# Example: Price a recent race
uv run python tools/price_race.py --date 2024-10-01 --course "Ascot" --time "14:30"
```

### 5. **Run Scoring Pipeline** (When Model is Production)
```bash
# Score tomorrow's races
uv run python tools/score_publish.py --date 2025-10-18

# Or score today
uv run python tools/score_publish.py
```

---

## 📁 New Files Created

```
giddyup/
├── src/giddyup/
│   ├── ratings/
│   │   ├── __init__.py
│   │   └── gpr.py                 # ⭐ GPR rating system
│   ├── risk/
│   │   ├── __init__.py
│   │   └── controls.py            # ⭐ Risk management
│   └── monitoring/
│       ├── __init__.py
│       └── quality.py             # ⭐ Data quality checks
├── tools/
│   ├── score_publish.py           # ⭐ Daily scoring pipeline
│   ├── backtest_value_gpr.py      # ⭐ Enhanced backtest
│   ├── price_race.py              # ⭐ Race pricing tool
│   └── test_gpr.py                # ⭐ GPR unit tests
├── GPR_IMPLEMENTATION_SUMMARY.md  # ⭐ Full documentation
└── STATUS.md                       # ⭐ This file
```

---

## ✅ Validation Checklist

### Pre-Production
- [x] GPR module tested (unit tests pass)
- [x] Feature engineering includes GPR
- [ ] Training completes successfully
- [ ] No market leakage (guards passed ✅)
- [ ] AUC in range 0.65-0.72
- [ ] Log Loss < 0.55
- [ ] GPR features in top importances
- [ ] Backtest shows +ROI
- [ ] GPR-OR pattern validates
- [ ] Tools run without errors

### Production Ready
- [ ] Model registered in MLflow as "Production"
- [ ] Backtest ROI > +3% after commission
- [ ] Monthly stability confirmed
- [ ] Risk controls tested
- [ ] Data quality checks pass
- [ ] Monitoring dashboard set up

---

## 🚨 Important Notes

1. **Expected AUC**: 0.65-0.72 is **NORMAL** for ability-only features
   - We're NOT trying to beat the market at winner-picking
   - We're finding MISPRICED horses (edge vs market)
   
2. **Data Leakage**: Training uses ZERO market features ✅
   - Market data only joined at T-60 during scoring
   - GPR computed from PAST runs only
   
3. **Calibration**: Log Loss is the critical metric
   - Probabilities must be accurate for value betting
   - Isotonic calibration applied
   
4. **GPR Hypothesis**: Horses with `gpr_minus_or > 0` are underrated
   - Backtest will validate this
   - Expect: high GPR-OR delta → high ROI

---

## 📞 Support

**Documentation**:
- `GPR_IMPLEMENTATION_SUMMARY.md` - Full technical docs
- `00_START_HERE.md` - Project overview
- `01_DEVELOPER_GUIDE.md` - Developer setup

**Logs**:
- Training: `training_gpr_20251017_103026.log`
- MLflow: `mlflow ui --backend-store-uri sqlite:///mlflow.db`

---

*Last Updated: October 17, 2025 10:40 UTC*  
*Status: Training in progress (Fold 1/5)*

