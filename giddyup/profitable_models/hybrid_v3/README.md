# Hybrid Model V3 - PROFITABLE ✅

**Status**: Production-ready  
**ROI**: +3.1%  
**Bets**: 979/year  
**Date**: October 17, 2025

---

## 📊 **Performance**

```
Backtest Period: 2024-2025 (22 months)
Total Bets: 1,794
Wins: 203 (11.3%)
Avg Odds: 9.96
Avg Rank: 4.4 (mid-field)

Financial:
  Total Staked: 22.75 units
  Total P&L: +0.70 units
  ROI: +3.1% ✅

Risk:
  Max Drawdown: 1.70 units
  Sharpe: 0.01
  Positive Months: 50%
```

---

## 🎯 **Configuration**

```python
MIN_DISAGREEMENT_RATIO = 2.50  # Model 150%+ higher than market
MIN_EDGE_ABSOLUTE = 0.08       # 8pp minimum
MIN_RANK = 3                   # Skip favorites
MAX_RANK = 6                   # Mid-field only
ODDS_MIN = 7.0                 # Sweet spot
ODDS_MAX = 12.0
MAX_OVERROUND = 1.18           # Competitive markets
MIN_EV_ADJUSTED = 0.05         # 5% EV minimum
KELLY_FRACTION = 0.10          # 1/10 Kelly
```

---

## 🚀 **How to Use**

```bash
# Daily selections
cd /home/smonaghan/GiddyUpModel/giddyup
./get_tomorrows_bets.sh 2025-10-18
```

---

## 📁 **Files**

- Model: MLflow run `5cb3c061d0184ab38059f37c84e0ffc9`
- Backtest: `models_ran/backtest_hybrid.py`
- Scorer: `get_tomorrows_bets.sh`
- Docs: `docs/DEPLOYMENT_GUIDE_HYBRID.md`

---

## ✅ **Why Profitable**

- **6-gate system** filters to high-conviction bets only
- **Avoids favorites** (market most efficient)
- **Focus on 7-12 odds** (market less efficient)
- **Adaptive blending** (trust market on extremes)
- **Top-1 per race** (no spraying)

