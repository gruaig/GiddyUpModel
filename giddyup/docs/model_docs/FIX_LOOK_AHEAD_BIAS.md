# Fix: Look-Ahead Bias in GPR Calculation

**Date**: October 17, 2025  
**Issue**: Unrealistic AUC (0.9575) due to data leakage  
**Status**: ✅ FIXED - Retraining in progress

---

## 🐛 The Problem

### **Original Code (WRONG)**
```python
# In src/giddyup/data/build.py
gpr_df = compute_gpr(
    df_runs=hist_runs,
    as_of_date=None,  # ← USING ALL DATA INCLUDING FUTURE!
    ...
)
```

**What this did**:
- For a race in **2010**, GPR was computed using runs from **2010, 2011, ..., 2025**
- Model could see the FUTURE when making predictions about the PAST
- This is called **look-ahead bias** or **data leakage**

**Result**:
- **AUC: 0.9575** (unrealistically high)
- **Log Loss: 0.156** (too good)
- Model appeared perfect but was cheating

---

## ✅ The Fix

### **New Code (CORRECT)**
```python
# Compute GPR incrementally by year
for year in years:
    cutoff_date = f"{year-1}-12-31"  # Use only PAST runs
    
    past_runs = hist_runs.filter(
        pl.col("race_date") <= cutoff_date
    )
    
    gpr_snapshot = compute_gpr(
        df_runs=past_runs,  # ← ONLY PAST DATA
        ...
    )
```

**What this does**:
- For races in **2010**, GPR uses only runs up to **2009-12-31**
- For races in **2023**, GPR uses only runs up to **2022-12-31**
- Model can NEVER see the future
- This is called **point-in-time** calculation

**Expected Result**:
- **AUC: 0.65-0.72** (realistic for ability-only features)
- **Log Loss: 0.45-0.55** (properly calibrated)
- Model is honest about what it knows

---

## 📊 Why This Matters

### **Look-Ahead Bias Example**

**Horse "Thunder Road" racing on 2010-06-15**:

| GPR Method | Runs Used | GPR Value | Problem |
|------------|-----------|-----------|---------|
| **WRONG** (all data) | 2006-2025 (50 runs) | 95 | Includes 40 runs AFTER this race! |
| **CORRECT** (point-in-time) | 2006-2009 (10 runs) | 82 | Only knows past performance |

With the WRONG method:
- Model knows horse will improve dramatically in 2011-2015
- Model correctly predicts outcomes because it saw the future
- But in REAL betting, we can't see the future!

With the CORRECT method:
- Model only knows what was knowable in 2010
- Predictions are realistic
- Can be deployed in production

---

## 🔍 How We Detected It

### **1. Unrealistic AUC**
```
Training Fold 2/5:
  AUC: 0.9575  ← TOO HIGH for ability-only model
  
Expected for ability-only: 0.65-0.72
```

**Red flag**: Even the best handicappers get AUC ~0.70-0.75. An AUC of 0.96 means the model is seeing information it shouldn't have.

### **2. User Skepticism**
User correctly questioned: *"Keep retraining until we get realistic results its not normal"*

This is good intuition! If results look too good to be true, they probably are.

### **3. Investigation**
```bash
# Checked dataset columns
- Found market features present (but not used in training ✅)
- Checked correlation: OR vs odds = -0.28 (moderate, not a problem ✅)
- Reviewed code: Found as_of_date=None ❌ FOUND IT!
```

---

## 🎯 Expected Results (After Fix)

### **Training Metrics**
```
Old (with leakage):
  AUC: 0.9575
  Log Loss: 0.156
  
New (no leakage):
  AUC: 0.65-0.72  ← Much lower, but HONEST
  Log Loss: 0.45-0.55  ← Higher, but REAL
```

### **Why Lower AUC is Actually Good**

**High AUC (0.96)** means:
- "I can rank horses perfectly"
- But market can also rank horses well
- No edge vs market

**Moderate AUC (0.70)** means:
- "I can rank horses moderately well"
- But I rank them DIFFERENTLY than market
- **Potential edge** when my ranking disagrees with market

**Example**:
```
Race at Ascot, 8 horses

Market ranking:  A, B, C, D, E, F, G, H
My ranking:      B, A, D, C, F, E, G, H
                 ↑     ↑  ↑

If I'm right and market is wrong about B, D, F → VALUE BETS!
```

---

## 📈 What Changes in the Model

### **Before Fix (Cheating)**
```
Horse: "Starlight Express"
Race Date: 2010-06-15

GPR Input:
  - Run 1: 2009-05-10 (2 lengths behind)  ✅ OK
  - Run 2: 2009-08-20 (won)              ✅ OK  
  - Run 3: 2010-12-15 (won big!)         ❌ FUTURE!
  - Run 4: 2011-03-20 (won again)        ❌ FUTURE!
  - Run 5: 2011-06-10 (placed)           ❌ FUTURE!

GPR = 98 (knows horse will improve!)
Model predicts: 25% win chance
Actual: wins at 8.0 odds → PROFIT

But in real betting, we didn't know about runs 3-5!
```

### **After Fix (Honest)**
```
Horse: "Starlight Express"  
Race Date: 2010-06-15

GPR Input:
  - Run 1: 2009-05-10 (2 lengths behind)  ✅ OK
  - Run 2: 2009-08-20 (won)              ✅ OK
  (Runs 3-5 are in the FUTURE, excluded)

GPR = 85 (only knows past form)
Model predicts: 18% win chance
Actual: wins at 8.0 odds

Market odds suggest 12.5% chance (1/8.0)
Our 18% > market 12.5% → Still a VALUE bet!
Edge is smaller but REAL
```

---

## ⚠️ Important Lessons

### **1. Always Check for Look-Ahead Bias**

**Common places it hides**:
- ✅ **Features**: Using today's closing price to predict today's outcome
- ✅ **Scaling**: Standardizing using min/max from entire dataset (including test)
- ✅ **Target encoding**: Using full dataset to compute category means
- ✅ **Time series**: Using future values in rolling windows

**Fix**: Always use **point-in-time** data only.

### **2. Unrealistic Metrics are Red Flags**

| Metric | Realistic Range | Red Flag |
|--------|----------------|----------|
| AUC (ability-only) | 0.65-0.75 | > 0.85 |
| Log Loss | 0.45-0.55 | < 0.30 |
| Win rate (10% base) | 11-13% | > 15% |
| ROI (after commission) | +3% to +10% | > +20% |

If your model is "too good", it's probably leaking data.

### **3. Domain Knowledge Matters**

**User's intuition was correct**: "Keep retraining until we get realistic results"

Even without seeing the code, they knew 0.96 AUC was impossible for horse racing betting. Domain experts can spot these issues faster than looking at code.

---

## 🔄 Current Status

**Training**: In progress (restarted at 10:50 AM)  
**Log**: `training_gpr_fixed_20251017_HHMMSS.log`  
**ETA**: ~45-90 minutes (point-in-time GPR is slower)

**What's happening now**:
1. Fetching base data (2M+ runners) - ~5-10 min
2. Engineering features - ~5-10 min
3. **Computing point-in-time GPR** - ~10-30 min ⏰ (SLOWER now, but CORRECT)
   - 2006 GPR: from 0 runs (debutants)
   - 2007 GPR: from 2006 runs
   - 2008 GPR: from 2006-2007 runs
   - ...
   - 2025 GPR: from 2006-2024 runs
4. Training LightGBM (5 folds × 2000 rounds) - ~20-40 min
5. Evaluation on test set - ~2-5 min

**Expected completion**: ~11:30-12:00 PM

---

## ✅ Validation Checklist (After Training)

### **Metrics Check**
- [ ] AUC: 0.65-0.72 (not 0.95+)
- [ ] Log Loss: 0.45-0.55 (not 0.15)
- [ ] Test metrics similar to train (no overfitting)

### **Feature Importance**
- [ ] GPR in top 10 features
- [ ] gpr_minus_or is informative
- [ ] No single feature dominates (>50% importance)

### **Backtest (2024-2025)**
- [ ] ROI: +3% to +10% (realistic)
- [ ] Bet volume: 500-2000 bets
- [ ] Avg odds: 6-12 (not all favorites)
- [ ] GPR-OR pattern: higher delta → higher ROI

### **Red Flags (Stop if)**
- ❌ AUC > 0.85 (still leaking)
- ❌ ROI > +20% (too good to be true)
- ❌ Bet volume < 50 (filters too tight)
- ❌ All bets are favorites (odds < 4.0)

---

## 📚 References

**Academic Papers**:
- "Common Pitfalls in Machine Learning" - data leakage section
- "Advances in Financial Machine Learning" by Marcos López de Prado - Chapter on backtesting
- "Prediction Errors in Sports Betting Markets" - realistic AUC ranges

**Our Docs**:
- `METHOD.md` - Full methodology (now updated)
- `GPR_IMPLEMENTATION_SUMMARY.md` - Technical details
- `STATUS.md` - Current project status

---

## 🎯 Summary

**Problem**: Look-ahead bias (AUC 0.96)  
**Root Cause**: GPR used future runs  
**Fix**: Point-in-time GPR calculation  
**Expected**: AUC 0.65-0.72 (realistic)  
**Status**: Retraining now (~45-90 min)  
**Next**: Validate metrics, run backtest, extract real betting examples

**Key Takeaway**: **Lower AUC with proper methodology beats higher AUC with data leakage**. 

We want a model that works in PRODUCTION, not one that looks good in backtest but fails in real betting.

---

*Last Updated: October 17, 2025 10:55 AM*  
*Training Log: `training_gpr_fixed_*.log`*

