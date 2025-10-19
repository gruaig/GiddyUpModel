# 📂 File Locations Guide

**Repository Root**: `/home/smonaghan/GiddyUpModel/giddyup/`

---

## 🎯 **MOST IMPORTANT: Daily Scripts**

### **Location**: `profitable_models/hybrid_v3/`

**Full path**: `/home/smonaghan/GiddyUpModel/giddyup/profitable_models/hybrid_v3/`

```
profitable_models/hybrid_v3/
├── get_tomorrows_bets.sh              ⭐ Original (compact output)
├── get_tomorrows_bets_v2.sh           ⭐⭐ With bankroll input + CSV export
├── get_tomorrows_bets_with_reasoning.sh ⭐⭐⭐ Detailed reasoning (NEW!)
├── score_tomorrow_hybrid.py           Python version (advanced)
├── config.py                          Model configuration
├── README.md                          Model performance details
└── ENHANCED_SCRIPT_GUIDE.md          Bankroll & tracking guide
```

**To run daily**:
```bash
cd /home/smonaghan/GiddyUpModel/giddyup/profitable_models/hybrid_v3
./get_tomorrows_bets_with_reasoning.sh 2025-10-18 5000
```

---

## 📚 **Documentation**

### **Location**: `docs/`

**Full path**: `/home/smonaghan/GiddyUpModel/giddyup/docs/`

### **Start Here** (Essential Reading)
```
docs/
├── START_HERE_OCT17.md                🎯 Quick start guide
├── YOUR_COMPLETE_ANSWER.md            All questions answered
├── README.md                          Docs folder overview
└── READY_TO_DEPLOY.md                 1-page deployment guide
```

### **Daily Operations**
```
docs/
├── DAILY_WORKFLOW.md                  Daily routine & SQL checks
├── RACE_BY_RACE_WORKFLOW.md           All-day racing schedule (NEW!)
├── BETTING_TIMING_AND_ODDS_STRATEGY.md Exchange vs bookmaker, timing (NEW!)
├── UNDERSTANDING_YOUR_BETS.md         Why bet explanations (NEW!)
└── EXAMPLE_OUTPUT.md                  What script shows you
```

### **For Developer**
```
docs/
├── FOR_DEVELOPER.md                   Simple 1-page reference
├── DEVELOPER_DATABASE_REQUIREMENTS.md Complete technical spec
└── HOW_THE_SCRIPT_WORKS.md           Code walkthrough
```

### **Technical Deep-Dive**
```
docs/
├── METHOD.md                          Complete methodology (1,395 lines!)
├── HYBRID_MODEL_PLAN.md              Architecture & design
├── DEPLOYMENT_GUIDE_HYBRID.md         Full deployment plan
├── PATH_A_PURE_ABILITY.md            Pure ability model details
└── FIX_LOOK_AHEAD_BIAS.md            What we learned
```

### **Results & Analysis**
```
docs/
├── HYBRID_REAL_BETTING_EXAMPLES.md   Real 2024-2025 bets
├── PATH_A_RESULTS.md                 Model iteration results
├── EXECUTIVE_SUMMARY_PATH_A.md       Path A summary
└── FINAL_PATH_A_ASSESSMENT.md        Final assessment
```

### **Reference**
```
docs/
├── ANSWER_EXCHANGE_VS_BOOK.md        Exchange vs bookmaker pros/cons
├── MARKET_FEATURES.md                 Market features explained
├── HIGH_AUC_EXPLAINED.md             Why high AUC with market features
├── GPR_IMPLEMENTATION_SUMMARY.md      GPR rating system
├── TRAIN_TEST_SPLIT.md               Training/test split strategy
└── WHAT_YOU_NEED_TOMORROW.md         Info needed for selections
```

**Total**: 31 documentation files (~25,000 words)

---

## 🏗️ **Source Code**

### **Location**: `src/giddyup/`

**Full path**: `/home/smonaghan/GiddyUpModel/giddyup/src/giddyup/`

```
src/giddyup/
├── __init__.py
├── data/                             Feature engineering
│   ├── build.py                      Data pipeline & GPR computation
│   ├── feature_lists.py              23 ability-only features
│   ├── guards.py                     Prevent market leakage
│   └── market.py                     Market feature calculation
│
├── models/                           Training & scoring
│   ├── trainer.py                    LightGBM + calibration
│   └── hybrid.py                     6-gate scoring system
│
├── ratings/                          GPR rating
│   └── gpr.py                        GiddyUp Performance Rating
│
├── price/                            Value betting
│   └── value.py                      Fair odds, EV, Kelly
│
├── risk/                             Risk management
│   └── controls.py                   Stake caps, stop-loss
│
├── publish/                          Database publishing
│   └── signals.py                    Insert to modeling.signals
│
└── monitoring/                       Data quality
    └── checks.py                     Validations
```

---

## 🛠️ **Tools & Scripts**

### **Location**: `tools/`

**Full path**: `/home/smonaghan/GiddyUpModel/giddyup/tools/`

```
tools/
├── train_model.py                    ⭐ Train the model
├── migrate.py                        Database schema setup
├── score_tomorrow_hybrid.py          Daily scoring (Python)
├── score_today_simple.py             Simplified scoring
├── seed_model.py                     Seed demo model
├── smoke_signal.py                   Test signal publishing
├── test_gpr.py                       Test GPR calculation
├── stake_size_simulator.py           Bankroll sizing simulation
├── show_2025_bets.py                 Show actual 2025 bets
├── analyze_bets.py                   Bet analysis
├── price_race.py                     Price a single race
└── demo_betting_examples.py          Demo examples
```

**Most important**: `train_model.py` (retraining annually)

---

## 📊 **Backtests & Historical**

### **Location**: `models_ran/`

**Full path**: `/home/smonaghan/GiddyUpModel/giddyup/models_ran/`

```
models_ran/
├── backtest_hybrid.py                ⭐ Hybrid V3 backtest (final)
├── backtest_pathA_v3.py              Path A pure ability V3
├── backtest_pathA_v4_8to12.py        8-12 odds specialist
├── backtest_pathA_enhanced.py        Enhanced Path A
├── backtest_simple.py                Simple baseline
├── backtest_value.py                 Value betting baseline
├── backtest_value_gpr.py             With GPR
├── backtest_2024.py                  2024 only
└── backtest_with_commission.py       Commission-aware
```

**Historical record**: All model iterations tested

---

## 🗄️ **Database**

### **Location**: `migrations/`

**Full path**: `/home/smonaghan/GiddyUpModel/giddyup/migrations/`

```
migrations/
└── 001_modeling_schema.sql           Creates modeling.* tables
```

**Tables created**:
- `modeling.models` - Model registry
- `modeling.signals` - Bet selections
- `modeling.bets` - Placed bets

**Apply with**:
```bash
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/migrate.py
```

---

## 📈 **Data**

### **Location**: `data/`

**Full path**: `/home/smonaghan/GiddyUpModel/giddyup/data/`

```
data/
└── training_dataset.parquet          Training data cache (2006-2023)
```

**Generated by**: `tools/train_model.py`  
**Size**: ~500MB (18 years of racing data)  
**Recreate**: Delete file and re-run training

---

## 📦 **Configuration**

### **Location**: Root directory

**Full path**: `/home/smonaghan/GiddyUpModel/giddyup/`

```
giddyup/
├── pyproject.toml                    Python dependencies
├── uv.lock                           Locked dependency versions
├── .env                              Environment variables (DATABASE)
├── .env.example                      Environment template
└── .gitignore                        Git ignore rules
```

**Dependencies**:
- Python 3.13
- LightGBM, Polars, scikit-learn, MLflow, etc.

---

## 📝 **Logs**

### **Location**: Root directory

**Full path**: `/home/smonaghan/GiddyUpModel/giddyup/`

```
giddyup/
├── training_pathA_*.log              Training logs
├── backtest_hybrid_*.log             Backtest results
├── backtest_v3*.log                  V3 iteration logs
├── 2025_bets_examples.log            Bet examples
└── stake_sim_results.log             Stake simulation
```

**Created automatically** when running training/backtests

---

## 📂 **Quick Reference: Where Is...**

| **I want to...** | **Go to...** | **File** |
|------------------|--------------|----------|
| **Run daily bets** | `profitable_models/hybrid_v3/` | `get_tomorrows_bets_with_reasoning.sh` |
| **See reasoning** | `profitable_models/hybrid_v3/` | `get_tomorrows_bets_with_reasoning.sh` |
| **Quick check** | `profitable_models/hybrid_v3/` | `get_tomorrows_bets_v2.sh` |
| **Start here** | `docs/` | `START_HERE_OCT17.md` |
| **Daily workflow** | `docs/` | `RACE_BY_RACE_WORKFLOW.md` |
| **Understand bets** | `docs/` | `UNDERSTANDING_YOUR_BETS.md` |
| **When to bet** | `docs/` | `BETTING_TIMING_AND_ODDS_STRATEGY.md` |
| **For developer** | `docs/` | `FOR_DEVELOPER.md` |
| **Full methodology** | `docs/` | `METHOD.md` |
| **Retrain model** | `tools/` | `train_model.py` |
| **Setup database** | `tools/` | `migrate.py` |
| **See all docs** | `docs/` | (31 files) |
| **Feature code** | `src/giddyup/data/` | `build.py`, `feature_lists.py` |
| **Model code** | `src/giddyup/models/` | `trainer.py`, `hybrid.py` |

---

## 🎯 **Most Used Paths**

### **Daily Use**:
```bash
# Your daily script location
cd /home/smonaghan/GiddyUpModel/giddyup/profitable_models/hybrid_v3

# Run it
./get_tomorrows_bets_with_reasoning.sh 2025-10-18 5000
```

### **Reading Docs**:
```bash
# Documentation location
cd /home/smonaghan/GiddyUpModel/giddyup/docs

# Start here
cat START_HERE_OCT17.md

# Daily workflow
cat RACE_BY_RACE_WORKFLOW.md
```

### **Training/Maintenance**:
```bash
# Tools location
cd /home/smonaghan/GiddyUpModel/giddyup/tools

# Retrain model (annually)
uv run python train_model.py
```

---

## 🌐 **GitHub Repository**

**URL**: https://github.com/gruaig/GiddyUpModel

**Clone**:
```bash
git clone https://github.com/gruaig/GiddyUpModel.git
cd GiddyUpModel/giddyup
```

**All files synced to GitHub** ✅

---

## 📋 **Project Structure Overview**

```
/home/smonaghan/GiddyUpModel/
└── giddyup/                          ← Main project folder
    ├── profitable_models/            ← ⭐ RUN SCRIPTS FROM HERE
    │   └── hybrid_v3/                ← ⭐⭐ YOUR DAILY LOCATION
    │       ├── get_tomorrows_bets_with_reasoning.sh
    │       ├── get_tomorrows_bets_v2.sh
    │       └── get_tomorrows_bets.sh
    │
    ├── docs/                         ← 📚 All documentation (31 files)
    │   ├── START_HERE_OCT17.md
    │   ├── RACE_BY_RACE_WORKFLOW.md
    │   ├── BETTING_TIMING_AND_ODDS_STRATEGY.md
    │   ├── UNDERSTANDING_YOUR_BETS.md
    │   └── ...27 more
    │
    ├── src/giddyup/                  ← 🏗️ Source code
    │   ├── data/                     (Feature engineering)
    │   ├── models/                   (Training & scoring)
    │   └── ratings/                  (GPR)
    │
    ├── tools/                        ← 🛠️ Utilities
    │   ├── train_model.py
    │   └── migrate.py
    │
    ├── models_ran/                   ← 📊 Backtest archive
    ├── migrations/                   ← 🗄️ Database setup
    ├── data/                         ← 📈 Training cache
    │
    ├── README.md                     ← 📖 Main project README
    ├── pyproject.toml                ← 📦 Dependencies
    └── .env                          ← ⚙️ Configuration
```

---

## 🎯 **For Tomorrow Morning**

**You'll run**:
```bash
cd /home/smonaghan/GiddyUpModel/giddyup/profitable_models/hybrid_v3
./get_tomorrows_bets_with_reasoning.sh 2025-10-18 5000
```

**Location breakdown**:
- `cd /home/smonaghan/GiddyUpModel/giddyup` = Go to project
- `profitable_models/hybrid_v3` = Go to production model folder
- `./get_tomorrows_bets_with_reasoning.sh` = Run the reasoning script
- `2025-10-18` = Tomorrow's date
- `5000` = Your bankroll (£5,000)

**That's it!** Everything else is documentation and code.

---

## 🗂️ **Directory Size Reference**

| Folder | Files | Purpose |
|--------|-------|---------|
| `profitable_models/hybrid_v3/` | 7 | ⭐ **YOUR MAIN LOCATION** |
| `docs/` | 31 | Complete documentation |
| `src/giddyup/` | ~20 | Source code |
| `tools/` | 12 | Utilities |
| `models_ran/` | 9 | Backtest archive |

**Total**: ~100 files, 25k+ words of documentation

---

**By**: Sean MoonBoots  
**Date**: October 17, 2025

🎯 **Everything is organized and ready to use!**

