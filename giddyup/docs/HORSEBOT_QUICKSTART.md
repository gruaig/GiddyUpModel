# 🚀 HorseBot Quick Start Guide

Get up and running in 5 minutes!

---

## 📦 Installation

### 1. Install Python Dependencies

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
pip install -r horsebot_requirements.txt
```

### 2. Create Config File

```bash
# Copy template
cp HorseBot_config.template.py HorseBot_config.py

# Edit with your Betfair credentials
nano HorseBot_config.py
```

Add your credentials:
```python
BETFAIR_USERNAME = "your_betfair_username"
BETFAIR_PASSWORD = "your_betfair_password"
BETFAIR_APP_KEY = "your_app_key"  # From developer.betfair.com
```

Save and exit (Ctrl+X, Y, Enter)

---

## 🧪 Test (Paper Trade)

**ALWAYS test first** without real money:

```bash
./run_bot_today.sh 5000 --paper
```

This will:
- ✅ Load today's selections
- ✅ Simulate finding markets
- ✅ Simulate placing bets
- ✅ Show what would happen
- ❌ **NOT place real bets**

Run paper trade for **1-2 weeks** to build confidence.

---

## 💰 Live Betting

Once you're confident:

```bash
./run_bot_today.sh 5000
```

⚠️ **This places REAL bets with REAL money!**

---

## 📊 Monitor Progress

### While Running

The bot prints status updates:
```
[2025-10-18 08:30:17] 💰 BET PLACED: £0.75 @ 7.40 | Bet ID: 123456789
[2025-10-18 08:35:22] ℹ️ Processing: Wasthatok (GB) at Catterick
[2025-10-18 08:35:24] ⚠️ Odds too low: 7.85 < 8.10
```

### Check Logs

```bash
# View today's log
cat strategies/logs/automated_bets/bot_log_$(date +%Y-%m-%d).csv

# View last 10 actions
tail -n 10 strategies/logs/automated_bets/bot_log_$(date +%Y-%m-%d).csv
```

---

## 🔄 Daily Workflow

### Morning (Before First Race)

```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# Check data is ready
./strategies/CHECK_DATA_READY.sh

# Start bot
./run_bot_today.sh 5000
```

### Leave It Running

The bot will:
1. Monitor all markets
2. Place bets at T-60 (if conditions met)
3. Log everything
4. Stop after last race

### Optional: Run in Background

```bash
# Start tmux
tmux new -s horsebot

# Run bot
./run_bot_today.sh 5000

# Detach (keep running): Ctrl+B, then D

# Later, reattach to check:
tmux attach -t horsebot
```

---

## 🛑 Stop the Bot

**Anytime**: Press `Ctrl+C`

The bot will:
- Logout from Betfair
- Save all logs
- Show summary

---

## 📈 Check Results

### View Betting Log

```bash
# Today's bets
cat strategies/logs/automated_bets/bot_log_$(date +%Y-%m-%d).csv

# Summary
cat strategies/logs/automated_bets/bot_log_$(date +%Y-%m-%d).csv | grep "YES" | wc -l
# Shows number of bets placed
```

### Compare with Original Selections

```bash
# What the strategies recommended
cat strategies/logs/daily_bets/betting_log_2025.csv | grep $(date +%Y-%m-%d)

# What the bot actually did
cat strategies/logs/automated_bets/bot_log_$(date +%Y-%m-%d).csv
```

---

## 🐛 Common Issues

### "No selections found"

**Cause**: Database doesn't have tomorrow's odds yet

**Fix**:
```bash
# Check data readiness
cd strategies
./CHECK_DATA_READY.sh
```

Wait for data to load (usually available by 6pm day before)

### "Could not find market on Betfair"

**Cause**: Market not published yet or course name mismatch

**Fix**: 
- Markets usually published 24h before race
- Check Betfair website manually
- Verify UK/Irish racing only

### "Bet placement failed"

**Causes**:
- Insufficient funds
- API key permissions
- Betfair account restrictions

**Fix**:
1. Check account balance on Betfair
2. Verify API key has betting permissions
3. Check account isn't restricted

### "ImportError: No module named 'betfairlightweight'"

**Fix**:
```bash
pip install -r horsebot_requirements.txt
```

---

## 🎯 Expected Behavior

### Normal Day

```
Selections loaded: 53 bets
Markets found: 48/53 (5 not published yet)
Odds checked at T-60: 48
Bets placed: 12/48 (36 odds too low)
```

**It's NORMAL for many bets to be skipped** - that's the odds filter working!

### What Success Looks Like

- ✅ Bot runs all day without crashing
- ✅ Bets placed at correct times (T-60 to T-5)
- ✅ Only bets when odds >= minimum
- ✅ All actions logged to CSV
- ✅ Can see bets on Betfair website

---

## 📚 Full Documentation

- **Setup**: `HORSEBOT_README.md`
- **Strategy A**: `strategies/strategy_a_hybrid_v3/STRATEGY_A_README.md`
- **Strategy B**: `strategies/strategy_b_high_roi/STRATEGY_B_README.md`
- **Both Strategies**: `strategies/DAILY_WORKFLOW_BOTH_STRATEGIES.md`

---

## 🎓 Understanding the Output

### EV +226.9% Explained

From your earlier question - this is **Expected Value**:

```
EV +226.9% means:
- For every £1 bet, you expect £2.27 profit on average
- Your £2 stake = £4.54 expected profit
- Over many identical bets, this is the average
```

**Higher EV = Better bet** (in theory)

### Strategy Codes

- **A-Hybrid_V3**: Rank-based, 3-4 bets/day, +3% ROI, proven ✅
- **B-Path_B**: Odds-based, 0-2 bets/day, +65% ROI, needs validation ⏳

---

## ⚡ Quick Commands Reference

```bash
# Install
pip install -r horsebot_requirements.txt

# Setup
cp HorseBot_config.template.py HorseBot_config.py
nano HorseBot_config.py

# Test
./run_bot_today.sh 5000 --paper

# Run Live
./run_bot_today.sh 5000

# View Log
cat strategies/logs/automated_bets/bot_log_$(date +%Y-%m-%d).csv

# Check Data
./strategies/CHECK_DATA_READY.sh
```

---

## 🎯 Next Steps

1. ✅ Install dependencies
2. ✅ Create config file
3. ✅ Paper trade for 1-2 weeks
4. ✅ Review logs and results
5. ✅ Once confident, switch to live
6. ✅ Monitor daily for first month

---

**Questions? Check `HORSEBOT_README.md` for full documentation.**

**Happy betting! 🏇💰**


