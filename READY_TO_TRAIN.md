# 🚀 Ready to Train!

## ✅ Pre-Flight Checklist

### Database ✅
- [x] PostgreSQL running (horse_racing container)
- [x] `racing.*` schema populated (226K races)
- [x] `modeling.*` schema created (3 tables)

### Python Environment ✅
- [x] `uv` installed (v0.9.3)
- [x] All dependencies installed (174 packages)
- [x] Feature engineering pipeline built
- [x] Training pipeline built

### Data Strategy ✅
- [x] Train: 2008-2023 (16 years, ~180K races)
- [x] Test: 2024-2025 (22 months, ~46K races) **HELD OUT**
- [x] No data leakage (GroupKFold + time-series split)

### Features ✅
- [x] 28 form features (speed, recency, connections, course/distance)
- [x] 9 market features (prices, movements, volume - all pre-race)
- [x] **35 total features**

---

## 🏃 Run Training

### Command

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/train_model.py
```

### What Will Happen

**Step 1: Feature Engineering** (2-5 minutes)
- Queries ~226K races from database
- Engineers 35 features per runner
- Saves to `data/training_dataset.parquet`

**Step 2: Model Training** (10-20 minutes)
- Splits train (2008-2023) vs test (2024-2025)
- 5-fold GroupKFold cross-validation
- Trains LightGBM (2000 rounds with early stopping)
- Calibrates probabilities (Isotonic)
- Evaluates on OOT test set

**Step 3: MLflow Logging** (< 1 minute)
- Logs all metrics, params, models
- Registers calibrated model
- Saves feature importance

**Total Time**: ~15-30 minutes

---

## 📊 Expected Output

```
🏇 GiddyUp Model Training Pipeline
================================================================================

📅 Data Split Strategy:
   Training:   2008-01-01 to 2023-12-31
   Testing:    2024-01-01 to 2025-10-16
   (Test set is NEVER seen during training - pure backtest!)

================================================================================
STEP 1: FEATURE ENGINEERING
================================================================================
📊 Building training data from 2008-01-01 to 2025-10-16...
   [1/6] Fetching base runner data...
      Loaded 2,235,311 runners from 226,397 races
   [2/6] Engineering horse historical features...
   [3/6] Engineering trainer form features...
   [4/6] Engineering jockey form features...
   [5/6] Engineering course/distance form...
   [6/6] Adding race-level features...
   [Extra] Adding pre-race market features...

✅ Feature engineering complete!
   Final shape: 2,235,311 rows × 67 columns
   Win rate: 8.45%
   Saved to: data/training_dataset.parquet

================================================================================
STEP 2: MODEL TRAINING
================================================================================
🚂 TRAINING HORSE RACING WIN PROBABILITY MODEL
================================================================================

📅 Splitting data:
   Train: 2008-01-01 to 2023-12-31
   Test:  2024-01-01 to 2025-10-16

   Train: 1,800,000 runners from 180,000 races
   Test:  435,311 runners from 46,397 races
   Train win rate: 8.43%
   Test win rate:  8.51%

🔧 Preparing arrays...
   Features: 35
   Train shape: (1800000, 35)
   Test shape: (435311, 35)

📊 MLflow Run ID: abc123def456...

🔀 Running 5-fold GroupKFold cross-validation...

   Fold 1/5:
      Train: 1,440,000 runners
      Val:   360,000 runners
      Best iteration: 856
      Log Loss: 0.4234
      AUC-ROC: 0.6891

   ... (Folds 2-5)

📈 Out-of-Fold (OOF) Metrics:
   Log Loss: 0.4178
   AUC-ROC: 0.6923

🎯 Calibrating probabilities (Isotonic Regression)...
   Calibrated Log Loss: 0.4145
   Improvement: 0.0033

🧪 Evaluating on Out-of-Time (OOT) test set...
   Period: 2024-01-01 to 2025-10-16
   This data was NEVER seen during training!

   Uncalibrated:
      Log Loss: 0.4201
      AUC-ROC: 0.6867

   Calibrated:
      Log Loss: 0.4168
      AUC-ROC: 0.6867

🔍 Top 10 Features:
    1. decimal_odds                      125834
    2. racing_post_rating                 98765
    3. official_rating                    87654
    4. is_fav                             76543
    5. price_drift_ratio                  65432
    6. trainer_sr_14d                     54321
    7. best_rpr_last_3                    43210
    8. jockey_sr_14d                      32109
    9. career_strike_rate                 21098
   10. market_rank                        10987

💾 Logging model to MLflow...
   ✅ Model logged to MLflow
   Model name: hrd_win_prob
   Run ID: abc123def456...

================================================================================
✅ TRAINING COMPLETE
================================================================================

📊 Final Metrics:
   OOF Log Loss (calibrated): 0.4145
   Test Log Loss (calibrated): 0.4168
   Test AUC-ROC: 0.6867

🎯 Model Performance:
   ✅ GOOD: Test performance within 5% of training

📁 MLflow:
   Experiment: horse_racing_win_prob
   Run ID: abc123def456...
   Model: hrd_win_prob

================================================================================
🎉 PIPELINE COMPLETE!
================================================================================

✅ Model trained successfully!

📊 Performance Summary:
   OOF Log Loss:  0.4145
   Test Log Loss: 0.4168
   Test AUC-ROC:  0.6867

📁 Next Steps:
   1. Review MLflow UI: mlflow ui --backend-store-uri sqlite:///mlflow.db
   2. Promote model to Production if metrics look good
   3. Run backtest on 2024-2025 data to validate edge
   4. Set up scoring pipeline for live predictions
```

---

## 🎯 Success Criteria

### ✅ Good Performance

| Metric | Target | Why |
|--------|--------|-----|
| OOF Log Loss | < 0.50 | Well-calibrated probabilities |
| Test Log Loss | < 0.50 | No overfitting |
| Test AUC-ROC | 0.65-0.72 | Good discrimination |
| Test vs OOF | Within 5% | Stable performance |

### ⚠️ Warning Signs

| Issue | Threshold | Action |
|-------|-----------|--------|
| Test Log Loss | > OOF × 1.10 | Model overfit, add regularization |
| Test AUC-ROC | < 0.60 | Features not predictive enough |
| Test AUC-ROC | > 0.80 | Probably data leakage! |
| Top feature | `win_bsp` | DATA LEAKAGE - remove it! |

---

## 📁 After Training

### 1. Review MLflow UI

```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# Start MLflow UI
mlflow ui --backend-store-uri sqlite:///mlflow.db

# Open browser
http://localhost:5000
```

**Check:**
- Experiment: `horse_racing_win_prob`
- Metrics: `test_logloss_calibrated`, `test_auc`
- Feature importance: Top 10 features
- Compare runs if you train multiple times

### 2. Promote to Production

```bash
# If metrics look good, promote to Production stage
# (You can do this in MLflow UI or via Python)
```

### 3. Generate Backtest Report

```python
# Next task: Build backtest script
# Score all 2024-2025 races
# Calculate ROI, CLV, Sharpe ratio
```

### 4. Build Scoring Pipeline

```python
# Score today's upcoming races
# Publish to modeling.signals
# Set up Prefect schedule (08:00 Europe/Madrid)
```

---

## 🔍 Troubleshooting

### Issue: "Out of Memory"

**Solution 1**: Sample the data
```python
# In tools/train_model.py, add sampling
df = df.sample(fraction=0.5, seed=42)  # Use 50% of data
```

**Solution 2**: Reduce features
```python
# Remove some less important features
# Keep top 20-25 features only
```

### Issue: "Training too slow"

**Solution**: Reduce hyperparameters
```python
TrainConfig(
    num_boost_round=500,  # Instead of 2000
    n_folds=3,            # Instead of 5
)
```

### Issue: "Test AUC < 0.60"

**Diagnosis**: Features not predictive
- Check if market features populated (nulls?)
- Verify data quality in database
- Consider adding more features

### Issue: "Test AUC > 0.80"

**Diagnosis**: DATA LEAKAGE!
- Check feature list for BSP, in-play prices
- Verify no future information in features
- Re-read `MARKET_FEATURES.md`

---

## 📦 Output Files

After training, you'll have:

```
giddyup/
├── data/
│   └── training_dataset.parquet    # ~500MB feature dataset
├── mlflow.db                        # MLflow tracking database
├── mlruns/                          # MLflow artifacts
│   └── 0/
│       └── <run_id>/
│           ├── artifacts/
│           │   ├── calibrated_model/      # Production model
│           │   ├── fold_1_booster/
│           │   ├── fold_2_booster/
│           │   └── ...
│           └── metrics/
└── .mlflow/
```

---

## 🚀 Ready to Go!

**Everything is set up. Run this command:**

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/train_model.py
```

**Estimated time**: 15-30 minutes  
**Expected test AUC**: 0.65-0.72  
**Expected test log loss**: 0.40-0.50

---

**Your 2024-2025 hold-out data is safe and will show you TRUE out-of-sample performance!** 🎯

Good luck! 🍀

