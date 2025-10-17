# GiddyUp Horse Racing Model

**Python-first modeling stack for value betting in horse racing**

**Status**: ✅ Production-ready (Hybrid V3)  
**ROI**: +3.1% (validated on 1,794 bets)  
**Volume**: ~980 bets/year

---

## 🎯 **Quick Start**

```bash
# Get tomorrow's bet selections
./get_tomorrows_bets.sh 2025-10-18

# Expected output: 0-5 bets with odds, stakes, reasoning
```

**See**: `docs/START_HERE_OCT17.md` for complete guide

---

## 📊 **What This Does**

**Finds value bets** by:
1. Training independent model on **ability features only** (no market data)
2. Comparing model probability to market probability
3. Betting when we **strongly disagree** with market (2.5x+ higher)
4. Targeting **mid-field horses** (rank 3-6, odds 7-12)
5. Avoiding favorites (market too efficient)

**Result**: +3.1% ROI over 1,794 bets

---

## ✅ **Profitable Model**

**Hybrid V3** (Path A training + market-aware scoring):

```
Performance (2024-2025 backtest):
  Bets: 1,794 (979/year, ~80/month, ~3-4/day)
  ROI: +3.1%
  Win Rate: 11.3%
  Avg Odds: 9.96
  P&L: +0.70 units

Best Odds Band:
  5-8 odds: 187 bets, +18.7% ROI ✅
  8-12 odds: 1,200 bets, +3.8% ROI ✅
```

**See**: `profitable_models/hybrid_v3/` for details

---

## 📁 **Repository Structure**

```
giddyup/
├── docs/                          # All documentation
│   ├── START_HERE_OCT17.md       # Quick start guide
│   ├── DEPLOYMENT_GUIDE_HYBRID.md # Full deployment plan
│   ├── FOR_DEVELOPER.md           # Database requirements
│   └── METHOD.md                  # Complete methodology
│
├── profitable_models/             # Production-ready models
│   └── hybrid_v3/                 # Current: +3.1% ROI
│       └── README.md
│
├── models_ran/                    # Historical backtests
│   ├── backtest_hybrid.py         # Hybrid V3 backtest
│   ├── backtest_pathA_v3.py       # Path A pure ability
│   └── backtest_simple.py         # Quick validation
│
├── src/giddyup/                   # Core modules
│   ├── data/                      # Feature engineering
│   ├── models/                    # Training & scoring
│   ├── ratings/                   # GPR rating system
│   ├── price/                     # EV, Kelly, fair odds
│   └── risk/                      # Risk controls
│
├── tools/                         # Utilities
│   ├── train_model.py             # Model training
│   ├── score_tomorrow_hybrid.py   # Daily scoring (Python)
│   └── migrate.py                 # DB migration
│
├── get_tomorrows_bets.sh          # Daily selections (SQL)
└── pyproject.toml                 # Dependencies
```

---

## 🚀 **Usage**

### **Daily Workflow** (Paper Trading Nov-Dec 2025)

```bash
# Morning (8 AM)
./get_tomorrows_bets.sh

# Review output (0-5 bets)
# Log to spreadsheet (no real money yet)

# Evening
# Check results
# Update P&L tracking
```

### **Retraining** (Annual - Jan 1)

```bash
# Update config
# train_date_to = "2024-12-31"

# Retrain
rm data/training_dataset.parquet
uv run python tools/train_model.py

# Backtest
uv run python models_ran/backtest_hybrid.py
```

---

## 📊 **Key Features**

### **1. Independent Model**
- Trains on ability features only (NO market data)
- No Official Rating, No Racing Post Rating
- Truly independent of market consensus
- **AUC**: 0.71 (realistic, not inflated)

### **2. GPR Rating System**
- GiddyUp Performance Rating (pounds-scale)
- Distance-aware beaten lengths
- Context de-biased (course/going/distance)
- Recency weighted (120-day half-life)
- Point-in-time (no look-ahead)

### **3. Market-Aware Scoring**
- 6-gate system for selection
- Adaptive blending (trust market on extremes)
- Favorite penalty (market most efficient)
- Top-1 per race (no spraying)

### **4. Risk Controls**
- Fractional Kelly staking (1/10)
- Per-race caps
- Daily limits
- Liquidity checks

---

## 💰 **Expected Returns**

**With £5,000 bankroll** (1 unit = £50):

```
Daily:
  Bets: 3-4 (some days zero)
  Stake: £1-2
  
Monthly (80 bets):
  Stake: ~£50
  Expected P&L: £1.50-2.50 (at +3% ROI)
  
Annually (980 bets):
  Stake: ~£600
  Expected P&L: £18-30
```

**Not get-rich-quick, but systematic edge.**

---

## 🔄 **Retraining Schedule**

```
Current Model: Trained on 2006-2023
Deployment: Nov-Dec 2025 (paper trade)

Next Retrain: Jan 1, 2026
  - Training: 2006-2024
  - Validation: 2025
  - Deploy: 2026

Annual: Every Jan 1
```

---

## 📚 **Documentation**

- **`docs/START_HERE_OCT17.md`** - Quick start
- **`docs/YOUR_COMPLETE_ANSWER.md`** - All questions answered
- **`docs/FOR_DEVELOPER.md`** - Database requirements
- **`docs/METHOD.md`** - Complete methodology (1,395 lines)
- **`docs/DEPLOYMENT_GUIDE_HYBRID.md`** - Deployment plan

---

## 🛠️ **Tech Stack**

```
Language: Python 3.13
Package Manager: uv
ML: LightGBM, scikit-learn
Data: Polars
Database: PostgreSQL
Experiment Tracking: MLflow
```

---

## ⚠️ **Important Notes**

1. **Paper trade first** (Nov-Dec 2025, no real money)
2. **Use Betfair Exchange** prices (`win_ppwap`)
3. **Expect variance** (50% of months negative)
4. **Long-term edge** (+3% ROI over time)
5. **Not for favorites** (rank 3-6 only)

---

## 📞 **Support**

- Questions? See `docs/` folder
- Issues? Check `docs/DEVELOPER_DATABASE_REQUIREMENTS.md`
- Deployment? See `docs/DEPLOYMENT_GUIDE_HYBRID.md`

---

## 📜 **License**

Private - Not for distribution

---

**Built**: October 2025  
**Branch**: `hybrid_model`  
**Ready for**: Paper trading deployment

