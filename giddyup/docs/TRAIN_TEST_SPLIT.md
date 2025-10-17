# Train/Test Split Strategy for Backtesting

## 🎯 Objective

Hold out **2024-2025 data** as a pure out-of-time (OOT) test set for validating model performance and calculating realistic backtest returns.

---

## 📅 Data Split

### Current Configuration

```python
Train:  2008-01-01 to 2023-12-31  # 16 years, ~180K races
Test:   2024-01-01 to 2025-10-16  # 22 months, ~46K races
Live:   2025-10-17 onwards         # Production deployment
```

### Why This Split?

1. **No Data Leakage**: Model never sees 2024-2025 during training
2. **Realistic Performance**: Test set reflects recent market conditions
3. **Large Sample**: 22 months gives statistically significant results
4. **CLV Validation**: Can compare our odds vs closing prices on unseen data

---

## 🔒 What This Prevents

### ❌ **BAD: Training on All Data**

```python
# DON'T DO THIS!
df = build_training_data("2008-01-01", "2025-10-16")
train_test_split(df, test_size=0.2)  # Random split
```

**Problems:**
- Test races might be from 2010, 2015, 2020, etc. (not realistic)
- Model sees future information (race outcomes leak into features)
- Backtest is **overly optimistic** and doesn't reflect real performance

### ✅ **GOOD: Time-Series Split**

```python
# Training: historical data only
train_df = df.filter(race_date <= "2023-12-31")

# Testing: future data (unseen during training)
test_df = df.filter(race_date >= "2024-01-01")
```

**Benefits:**
- Simulates real-world deployment (predict future races)
- Test set is chronologically **after** training set
- Backtest shows true expected performance going forward

---

## 📊 Cross-Validation Strategy

### GroupKFold by race_id

```python
from sklearn.model_selection import GroupKFold

gkf = GroupKFold(n_splits=5)
for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=race_ids)):
    # All runners in same race stay together in same fold
    # Prevents leakage: can't use race outcomes to predict same race
```

**Why GroupKFold?**
- All horses in **Race 123** are in the same fold
- Prevents using "Horse A won Race 123" to predict "Horse B in Race 123"
- This is critical for racing: outcome of one horse correlates with others in same race

### Combined with Time-Series Split

```
                  Training Set (2008-2023)                   Test Set (2024-2025)
├─────────────────────────────────────────────────────────┼──────────────────────┤
│                                                           │                      │
│  Fold 1   Fold 2   Fold 3   Fold 4   Fold 5             │    Never Seen!       │
│  (Val)    (Train)  (Train)  (Train)  (Train)             │                      │
│                                                           │                      │
│  Fold 2   Fold 2   Fold 3   Fold 4   Fold 5             │    Pure Backtest     │
│  (Train)  (Val)    (Train)  (Train)  (Train)             │                      │
│                                                           │                      │
│  ...                                                      │                      │
│                                                           │                      │
└─────────────────────────────────────────────────────────┴──────────────────────┘
         Out-of-Fold (OOF) Predictions                    Out-of-Time (OOT) Test
         (used for calibration)                           (used for backtest)
```

---

## 🧪 Validation Workflow

### 1. During Training

```python
# Train on 2008-2023
# 5-fold GroupKFold CV gives OOF predictions
# OOF metrics: Log Loss, AUC-ROC
```

### 2. Calibration

```python
# Use OOF predictions to fit isotonic calibration
# This ensures probabilities are well-calibrated
```

### 3. Test Set Evaluation

```python
# Predict on 2024-2025 (OOT)
# Calculate:
#   - Log Loss (how well calibrated?)
#   - AUC-ROC (discrimination)
#   - Brier Score (accuracy of probabilities)
```

### 4. Backtest

```python
# For each race in 2024-2025:
#   1. Get model prediction (p_win)
#   2. Calculate fair odds (1 / p_win)
#   3. Compare vs actual market odds
#   4. Simulate bets where we have edge
#   5. Calculate ROI, Sharpe, CLV
```

---

## 💰 Backtest Metrics to Track

### 1. **Closing Line Value (CLV)**

```python
# For each bet:
CLV = (closing_odds - taken_odds) / taken_odds

# Positive CLV = we beat the closing line (good!)
# Negative CLV = market moved against us (bad)
```

### 2. **ROI (Return on Investment)**

```python
total_profit = sum(payouts) - sum(stakes)
ROI = total_profit / sum(stakes)

# Target: ROI > 5% (after commissions)
```

### 3. **Edge Realization**

```python
# Compare model edge vs actual results
model_edge = fair_odds / market_odds - 1
actual_edge = (wins / bets) * avg_odds - 1

# If actual_edge ≈ model_edge → model is well-calibrated!
```

### 4. **Sharpe Ratio**

```python
# Risk-adjusted returns
sharpe = mean(returns) / std(returns) * sqrt(252)

# Target: Sharpe > 1.0 (decent), > 2.0 (excellent)
```

---

## 🚀 How to Use

### Train Model with Hold-Out

```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# This will automatically use 2024-2025 as OOT test set
uv run python tools/train_model.py
```

### Check Results

```bash
# View MLflow UI
mlflow ui --backend-store-uri sqlite:///mlflow.db

# Navigate to:
# http://localhost:5000
# → Experiment: horse_racing_win_prob
# → Check test_logloss_calibrated and test_auc metrics
```

### Run Backtest (Next Task!)

```bash
# After training, run backtest on hold-out period
uv run python tools/backtest.py \
  --date-from 2024-01-01 \
  --date-to 2025-10-16 \
  --model-name hrd_win_prob \
  --model-stage Production
```

---

## 📈 Expected Performance

### Realistic Metrics for Racing

| Metric | Good | Excellent |
|--------|------|-----------|
| Test Log Loss | < 0.50 | < 0.45 |
| Test AUC-ROC | > 0.65 | > 0.70 |
| Positive CLV | > 2% | > 5% |
| ROI (2% comm) | > 5% | > 10% |
| Sharpe Ratio | > 1.0 | > 2.0 |

### Warning Signs

⚠️ **If test performance is much worse than OOF:**
- Model may be overfitting to 2008-2023 patterns
- Racing markets may have changed
- Need to retrain on more recent data

⚠️ **If backtest ROI is negative:**
- Model may not have real edge
- Commissions/market impact not properly accounted for
- Need better features or different approach

---

## 🔄 Alternative Splits (If Needed)

### Option B: More Recent Training

```python
Train:  2015-01-01 to 2023-12-31  # 9 years
Test:   2024-01-01 to 2025-10-16  # 22 months
```

**Use if:** Older racing data (2008-2014) is less relevant

### Option C: Larger Test Set

```python
Train:  2008-01-01 to 2024-06-30  # 16.5 years
Test:   2024-07-01 to 2025-10-16  # 15 months
```

**Use if:** You want more recent training data

---

## 📝 Key Takeaways

1. ✅ **Never train on your backtest period**
2. ✅ **Use GroupKFold to prevent within-race leakage**
3. ✅ **Calibrate probabilities on OOF predictions**
4. ✅ **Test set must be chronologically after training**
5. ✅ **Track CLV to validate real edge vs market**

---

**Your 2024-2025 hold-out is your "unpolluted" data for proving your model works!**

