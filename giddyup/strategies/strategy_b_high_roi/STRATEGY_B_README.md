# Strategy B: Path B (High ROI, Lower Volume)

**Branch**: Merged to `main`  
**Status**: ⏳ **NEEDS VALIDATION** - Paper trade before deploying  
**By**: Sean MoonBoots

---

## 📊 **Performance** (Backtest)

```
Validated: 634 bets (Jan 2024 - Oct 2025)
ROI: +65.1% (after 2% commission) ✅✅
Win Rate: 18.1%
Avg Odds: 8.62
Avg Edge: 17.6pp

Annual:
  Bets: ~359/year
  Monthly: ~30 bets
  Daily: 0-2 bets (many days 0)

With £5,000 bankroll:
  Monthly profit: +£39
  Annual profit: +£467
```

**21x better ROI than Strategy A!**

---

## 🎯 **What This Strategy Does**

**Path B** uses **odds-band specific logic** to find high-value opportunities:

### **Banded Approach**:

Instead of fixed thresholds, uses **different rules per odds range**:

| Odds Range | Edge Min | Lambda | Strategy |
|------------|----------|--------|----------|
| 5-8 | 15pp | 40% market | Selective |
| 8-12 | 15pp | 15% market | Trust model most ✅ |
| 12-16 | 16pp | 50% market | Hedge longshots |

**Focus**: Odds-based selection (7-16 sweet spot)

**Key Innovation**: Market efficiency varies by odds → different thresholds per band!

---

## 🎓 **How It Works**

### **Step 1**: Get model probability (same training as Strategy A)

### **Step 2**: Calculate vig-free market probability

### **Step 3**: Blend with odds-specific lambda
```
5-8 odds:  p_blend = 60% model + 40% market
8-12 odds: p_blend = 85% model + 15% market ← Trust model here!
12+ odds:  p_blend = 50% model + 50% market (hedge)
```

### **Step 4**: Check banded edge threshold
```
5-8 odds:  Need 15pp edge minimum
8-12 odds: Need 15pp edge minimum  
12+ odds:  Need 16pp edge minimum
```

### **Step 5**: Top-1 per race by edge

---

## 🚀 **Daily Usage**

### **Get Tomorrow's Selections**:
```bash
cd /home/smonaghan/GiddyUpModel/giddyup/strategies/strategy_b_high_roi
./get_bets.sh 2025-10-18 5000
```

**Output**: 0-2 bets (much more selective than Strategy A)

---

## 📁 **Files in This Folder**

```
strategy_b_high_roi/
├── path_b_hybrid.yaml              Configuration (tuned!)
├── backtest_path_b_simple.py       Validation script
├── get_bets.sh                     Daily selection script
└── STRATEGY_B_README.md           This file
```

---

## ⚠️ **Important: Needs Validation!**

**Status**: Backtested, NOT paper-traded yet

**Before deploying with real money**:
1. ⏳ Paper trade Nov-Dec (2 months, no real money)
2. ⏳ Track ~60 bets
3. ⏳ Validate achieves 20%+ ROI (not expecting full 65%, but should be high)
4. ⏳ If validates → Deploy Jan 2026

**Don't skip validation!** Backtest != real-world guarantee.

---

## 💡 **Best For**

✅ **Aggressive** ROI maximization  
✅ **Lower volume** acceptable (1 bet/day average)  
✅ **Higher profit** per bet (17.6pp edge vs 4-8pp)  
✅ **Patient** (can wait for right opportunities)  
✅ **Willing to validate** (2 months paper trading)

---

## 🆚 **vs Strategy A**

| Metric | **Strategy A** | **Strategy B** |
|--------|---------------|---------------|
| ROI | +3.1% | +65.1% |
| Bets/year | 980 | 359 |
| Bets/day | 3-4 | 0-2 |
| Status | Proven ✅ | Needs validation ⏳ |
| Focus | Rank-based | Odds-based |
| Monthly profit (£5k) | +£1.55 | +£39 |

**Strategy B: 25x more profit per month!**

---

## 🔧 **Configuration**

**Optimized through 5 iterations**:

```yaml
odds_caps:
  min: 7.0   # Focus on 7-16 range
  max: 16.0

edge_min_by_odds:
  "5.0-8.0":  0.15  # 15pp minimum
  "8.0-12.0": 0.15  # 15pp minimum
  "12.0-999": 0.16  # 16pp minimum

lambda_by_odds:
  "5.0-8.0":  0.40  # 40% market trust
  "8.0-12.0": 0.15  # 15% market trust (trust model!)
  "12.0-999": 0.50  # 50% market trust (hedge)
```

**All tuned for 200-500 bets/year @ 5-15% ROI** ✅

---

## 📈 **Backtest Results by Band**

| Odds Band | Bets | ROI | Status |
|-----------|------|-----|--------|
| 5-8 | 56 | +46.0% | ✅ |
| 8-12 | 576 | +61.8% | ✅ |
| 12-16 | 2 | +1176% | ✅ (tiny sample) |
| **Total** | **634** | **+65.1%** | **✅** |

**ALL bands profitable!**

---

## 🎯 **When to Use**

**Use Strategy B if**:
- ✅ Want maximum ROI (not max volume)
- ✅ Okay with 0-2 bets/day (some days zero)
- ✅ Can paper trade 2 months to validate
- ✅ Seeking 30-100% annual ROI

**Use BOTH A + B if**: ⭐
- ✅ Want diversified portfolio
- ✅ Maximum total profit (+£486/year vs +£18)
- ✅ Different market segments
- ✅ Smooth variance

---

## 🚨 **Validation Required!**

**This strategy has NOT been proven in real-world yet.**

**Must complete**:
1. 2 months paper trading (Nov-Dec)
2. Achieve 20%+ ROI (realistic expectation)
3. Track ~60 bets
4. Then deploy if working

**Backtest is promising but not guarantee!**

---

## 🔄 **Run Backtest Yourself**

```bash
cd /home/smonaghan/GiddyUpModel/giddyup/strategies/strategy_b_high_roi

# Validate the configuration
python backtest_path_b_simple.py
```

**Should show**: 634 bets @ +65% ROI

---

**Developed by**: Sean MoonBoots  
**Strategy**: B - Path B (High ROI)  
**Status**: Needs validation before live deployment  
🎯 **Potential +65% ROI - Validate first!** 🎯

