# 🚂 Training Status

**Started**: October 17, 2025 at 00:25:47

## Process Information

**Status**: ✅ RUNNING  
**Process ID**: 2277673  
**Command**: `uv run python tools/train_model.py`

---

## Expected Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Feature Engineering | 2-5 min | 🔄 In Progress |
| Model Training | 10-20 min | ⏳ Pending |
| MLflow Logging | < 1 min | ⏳ Pending |
| **Total** | **15-30 min** | **🔄 Running** |

---

## Check Progress

### Option 1: Watch Live Progress
```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# Watch the training process
watch -n 2 'ps aux | grep train_model | grep -v grep'

# Check if Python process is using CPU (should be 100-200%)
top -p 2277673
```

### Option 2: Monitor Logs (When Available)
```bash
# If nohup.out gets created:
tail -f nohup.out

# Or check training log:
ls -lh training_*.log
tail -f training_20251017_002547.log
```

### Option 3: Check if Complete
```bash
# Process no longer running = complete or failed
ps aux | grep 2277673 | grep -v grep

# Check for MLflow database (created when training finishes)
ls -lh mlflow.db mlruns/

# Check for output dataset
ls -lh data/training_dataset.parquet
```

---

## What's Happening Now

1. **Loading Data from Database** (2-3 min)
   - Querying ~2M runners from `racing.*` tables
   - Loading into Polars DataFrame

2. **Feature Engineering** (2-3 min)
   - 35 features being calculated
   - Horse form, trainer form, jockey form
   - Market features (prices, movements)

3. **Training** (10-15 min)
   - 5-fold GroupKFold cross-validation
   - LightGBM boosting (2000 rounds)
   - Isotonic calibration
   - OOT test set evaluation

4. **Saving** (< 1 min)
   - Logging to MLflow
   - Saving calibrated model
   - Feature importance

---

## When Complete

Look for these files:

```
giddyup/
├── data/
│   └── training_dataset.parquet    ← Feature dataset (~500MB)
├── mlflow.db                        ← MLflow tracking database
├── mlruns/                          ← MLflow artifacts
│   └── 0/
│       └── <run_id>/
│           ├── artifacts/
│           │   └── calibrated_model/    ← Your trained model!
│           └── metrics/
└── training_*.log                   ← Training log
```

---

## Expected Results

**Good Performance:**
- Test Log Loss: 0.40-0.50
- Test AUC-ROC: 0.65-0.72
- Test performance within 5% of OOF

**Top Features Should Be:**
1. `decimal_odds` or `win_ppwap`
2. `racing_post_rating`
3. `official_rating`
4. `is_fav`
5. `price_drift_ratio`

---

## If It Fails

Check for error messages:
```bash
# Kill the process
kill 2277673

# Check what went wrong
cat nohup.out
cat training_*.log

# Check system resources
free -h
df -h
```

Common issues:
- Out of memory → Reduce data or use sampling
- Database connection → Check PostgreSQL is running
- Dependency error → Missing package

---

## Next Steps After Training

1. **Review Results**
   ```bash
   mlflow ui --backend-store-uri sqlite:///mlflow.db
   # Open http://localhost:5000
   ```

2. **Check Metrics**
   - Is test AUC 0.65-0.72? ✅ Good
   - Is test AUC > 0.80? ⚠️ Check for leakage
   - Is test worse than OOF? ⚠️ Overfit

3. **Promote to Production** (if good)
   - In MLflow UI, promote model to "Production" stage

4. **Run Backtest**
   - Score all 2024-2025 races
   - Calculate ROI, CLV, Sharpe
   - Validate edge vs market

5. **Build Scoring Pipeline**
   - Score today's races
   - Publish to `modeling.signals`
   - Set up Prefect schedule

---

**Status**: 🔄 Training in progress...  
**Check back in**: ~15-30 minutes  
**Current time**: 00:25 (started)  
**Expected completion**: ~00:40-00:55

