# ✅ Tasks 2 & 3 Complete: Feature Engineering + Model Training

**Date**: October 16, 2025  
**Status**: ✅ **READY TO TRAIN**

---

## 🎉 What Was Built

### Task 2: Feature Engineering Pipeline ✅

**File**: `giddyup/src/giddyup/data/build.py`

**Features Engineered:**

1. **Horse Historical**
   - Days since last run (DSR)
   - Last 3 positions
   - Career runs & wins
   - Career strike rate
   - Best RPR in last 3 runs
   - Average beaten lengths

2. **Trainer Form**
   - Wins in last 14 days
   - Runs in last 14 days
   - Strike rate (14-day rolling)

3. **Jockey Form**
   - Wins in last 14 days
   - Runs in last 14 days
   - Strike rate (14-day rolling)

4. **Course/Distance**
   - Runs at this course
   - Wins at this course

5. **Race Characteristics**
   - Field size
   - Class (numeric)
   - Race type (Flat/Jumps)
   - Surface (Turf/AW)
   - Distance
   - Going (grouped)
   - Draw position

6. **Market**
   - Market rank (by odds)
   - Decimal odds

**Total**: 28 features

---

### Task 3: Model Training Pipeline ✅

**File**: `giddyup/src/giddyup/models/trainer.py`

**Training Strategy:**

```
📅 Data Split (Configured for Backtesting):

Train:  2008-01-01 to 2023-12-31   ← 16 years of historical data
Test:   2024-01-01 to 2025-10-16   ← 22 months HELD OUT for backtesting
Live:   2025-10-17 onwards          ← Future production
```

**Key Features:**

1. **GroupKFold Cross-Validation**
   - 5 folds
   - Groups by `race_id` to prevent leakage
   - All horses in same race stay in same fold

2. **LightGBM Training**
   - 2000 boosting rounds
   - Early stopping (100 rounds)
   - Tuned hyperparameters

3. **Isotonic Calibration**
   - Fits on out-of-fold (OOF) predictions
   - Ensures probabilities are well-calibrated
   - Critical for betting/staking decisions

4. **MLflow Integration**
   - Logs all metrics, params, models
   - Registers calibrated model
   - Enables easy deployment

5. **Feature Importance**
   - Tracks top features
   - Helps with model interpretation

---

## 🔒 Why Hold Out 2024-2025?

### You Asked For "Unpolluted Data" - Here's Why This Works:

**✅ True Out-of-Time (OOT) Testing**
- Model **NEVER** sees 2024-2025 during training
- Simulates real-world deployment
- Tests if model has genuine predictive power

**✅ Realistic Backtest**
- 22 months of hold-out data (~46K races)
- Can calculate actual ROI, CLV, Sharpe ratio
- Proves edge vs. the market

**✅ No Data Leakage**
- GroupKFold prevents within-race leakage
- Time-series split prevents future leakage
- Clean separation between train/test

---

## 🚀 How to Run

### 1. Train the Model

```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# Create data directory
mkdir -p data

# Run full training pipeline
uv run python tools/train_model.py
```

**What This Does:**
1. Extracts features from `racing.*` tables (2008-2025)
2. Splits into train (2008-2023) and test (2024-2025)
3. Trains LightGBM with 5-fold GroupKFold CV
4. Calibrates probabilities
5. Evaluates on OOT test set
6. Logs everything to MLflow

**Expected Runtime**: 10-30 minutes (depending on hardware)

### 2. Review Results in MLflow

```bash
# Start MLflow UI
cd /home/smonaghan/GiddyUpModel/giddyup
mlflow ui --backend-store-uri sqlite:///mlflow.db

# Open browser
http://localhost:5000
```

**Check:**
- Experiment: `horse_racing_win_prob`
- Metrics: `test_logloss_calibrated`, `test_auc`
- Parameters: All hyperparameters logged
- Artifacts: Calibrated model + boosters

---

## 📊 Expected Metrics

### Good Performance

| Metric | Target |
|--------|--------|
| OOF Log Loss | < 0.50 |
| Test Log Loss | < 0.50 |
| Test AUC-ROC | > 0.65 |
| Test vs OOF | Within 5% |

### Warning Signs

⚠️ **If test much worse than OOF:**
- Model overfit to 2008-2023 patterns
- May need more regularization
- Consider using only 2015-2023 for training

⚠️ **If AUC < 0.60:**
- Features may not be predictive enough
- Need more feature engineering
- Check for data quality issues

---

## 📁 Files Created

```
giddyup/
├── src/giddyup/
│   ├── data/
│   │   ├── __init__.py
│   │   └── build.py                # Feature engineering
│   └── models/
│       ├── __init__.py
│       └── trainer.py              # LightGBM training + calibration
├── tools/
│   └── train_model.py              # End-to-end training script
└── TRAIN_TEST_SPLIT.md             # Documentation
```

---

## 🔬 Backtest Period

**You now have 22 months of "unpolluted" data:**

```
2024-01-01 to 2025-10-16
```

**What You Can Do:**

1. **Calculate ROI**
   - For each race, model predicts win probabilities
   - Compare vs actual market odds
   - Simulate bets where model has edge
   - Calculate profit/loss

2. **Validate CLV (Closing Line Value)**
   - Compare model's fair odds vs closing prices
   - Positive CLV = beating the market
   - This is the gold standard for edge validation

3. **Risk Metrics**
   - Sharpe ratio
   - Maximum drawdown
   - Win rate vs expected win rate

4. **Feature Analysis**
   - Which features are most predictive?
   - Are there patterns in when model performs well/poorly?

---

## 📝 Next Steps

### Option A: Run the Training Now

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/train_model.py
```

**Then:**
- Review MLflow metrics
- Check if test performance looks good
- If good, promote model to Production

### Option B: Build Backtest Script First (Task 4)

Create `tools/backtest.py`:
- Load trained model
- Score 2024-2025 races
- Simulate betting strategy
- Calculate ROI, CLV, Sharpe
- Generate performance report

### Option C: Build Scoring Pipeline (Task 4)

Create `giddyup/flows/score.py`:
- Load production model from MLflow
- Score today's upcoming races
- Calculate Kelly stakes
- Publish to `modeling.signals`
- Set up Prefect scheduling

---

## 🎯 Data Split Configuration

**Current (Recommended):**
```python
TrainConfig(
    train_date_from="2008-01-01",
    train_date_to="2023-12-31",    # 16 years
    test_date_from="2024-01-01",    # OOT hold-out
    test_date_to="2025-10-16",      # 22 months
)
```

**Alternative Options:**

**More Recent Training:**
```python
train_date_from="2015-01-01"  # Only use last 9 years
```

**Larger Test Set:**
```python
train_date_to="2024-06-30"     # Hold out 15 months instead
test_date_from="2024-07-01"
```

**Smaller Test Set:**
```python
train_date_to="2024-12-31"     # Only hold out 2025
test_date_from="2025-01-01"
```

To change: Edit `tools/train_model.py` and adjust `TrainConfig`

---

## 🔍 Feature Engineering Details

See: `TRAIN_TEST_SPLIT.md` for full documentation

**Key Features:**
- **Speed ratings**: `official_rating`, `racing_post_rating`, `best_rpr_last_3`
- **Recency**: `days_since_run`
- **Form**: `last_pos`, `avg_btn_last_3`, `career_strike_rate`
- **Connections**: `trainer_sr_14d`, `jockey_sr_14d`
- **Course**: `runs_at_course`, `wins_at_course`
- **Market**: `market_rank`, `decimal_odds`

**Total**: 28 features

---

## ✅ Validation Checklist

Before deploying to production:

- [ ] Train model on 2008-2023
- [ ] Verify test metrics (2024-2025) are reasonable
- [ ] Run backtest to calculate ROI
- [ ] Check CLV is positive
- [ ] Review feature importance
- [ ] Promote model to Production in MLflow
- [ ] Set up scoring pipeline
- [ ] Deploy Prefect schedule

---

## 📚 Documentation

- **Feature Engineering**: `src/giddyup/data/build.py`
- **Training**: `src/giddyup/models/trainer.py`
- **Train/Test Split**: `TRAIN_TEST_SPLIT.md`
- **Run Script**: `tools/train_model.py`

---

**Status**: ✅ Tasks 2 & 3 COMPLETE  
**Next**: Train the model OR build backtest script  
**Your 2024-2025 data is SAFE**: Never used in training, ready for validation!

🎊 **You now have a proper ML pipeline with clean train/test split for backtesting!**

