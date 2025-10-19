# Hybrid Model: Deployment Guide & Retraining Schedule

**Model**: Hybrid V3 (Path A training + market-aware scoring)  
**Performance**: +3.1% ROI over 1,794 bets (979/year)  
**Status**: Ready for paper trading

---

## 📊 **Real Betting Performance (2024-2025 Backtest)**

### **Annual Summary**

```
Period: Jan 2024 - Oct 2025 (22 months)
Total Bets: 1,794 (979/year, ~80/month, ~3-4/day)
Wins: 203 (11.3% win rate)
Avg Odds: 9.96
Avg Market Rank: 4.4 (mid-field, not favorites)

Financial:
  Total Staked: 22.75 units
  Total P&L: +0.70 units
  ROI: +3.1%

Risk:
  Max Drawdown: 1.70 units
  Sharpe: 0.01 (low but positive)
  Positive months: 11/22 (50%)
```

---

### **Real Examples (Jan 1-2, 2024)**

#### **Example 1: Zealandia (FR) - Newcastle ✅**
```
Date: 2024-01-01 14:00
Course: Newcastle (AW)
Horse: Zealandia (FR)
Odds: 9.45
Market Rank: 4 ✅
RPR: 99

Hybrid Assessment:
  Model: ~16% win probability
  Market: ~10.6% (vig-free)
  Disagreement: ~1.5x
  Edge: ~5pp
  
Bet: 0.012 units @ 9.45
Result: ✅ WON
Profit: +0.10u
```

#### **Example 2: Follow Charlie (IRE) - Ayr ✅**
```
Date: 2024-01-02 13:15
Course: Ayr
Horse: Follow Charlie (IRE)
Odds: 11.00
Market Rank: 4 ✅
RPR: 102

Bet: 0.010 units @ 11.00
Result: ✅ WON
Profit: +0.10u
```

**Favorites that WON but we DIDN'T bet** (rank filter protected us):
- Boldog (FR) @ 9.18 - rank 1 ❌ (would have won)
- Mick Charlie (IRE) @ 8.26 - rank 1 ❌ (would have won)
- Jungle Boogie (IRE) @ 10.84 - rank 1 ❌ (would have won)

**Trade-off**: We miss some winners to avoid favorite trap overall.

---

## 📅 **Your 2-Month Plan (Nov-Dec 2025)**

### **Current Situation**

- **Model**: Trained on 2006-2023 (18 years)
- **Validated on**: 2024-2025 (22 months) - backtest shows +3.1% ROI
- **Status**: Never deployed, completely fresh
- **Time remaining in 2025**: 2.5 months (mid-Oct to Dec)

---

### **Recommended Approach: Paper Trade Until Year End** ⭐

#### **Phase 1: Setup (Week 1 - Late October)**

1. **Test Scoring Script**
```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# Test on a recent date (verify it works)
uv run python tools/score_tomorrow_hybrid.py --date 2024-10-01

# Should show 0-3 bets with details
```

2. **Set Up Daily Automation**
```bash
# Add to crontab (run at 8:00 AM daily)
0 8 * * * cd /home/smonaghan/GiddyUpModel/giddyup && uv run python tools/score_tomorrow_hybrid.py >> logs/daily_scoring.log 2>&1
```

3. **Create Tracking Spreadsheet**
- Date, Horse, Course, Odds, Stake, Result, P&L
- Track every signal
- Compare to predictions

---

#### **Phase 2: Paper Trading (Nov-Dec 2025)**

**What to do**:
```
Daily (8:00 AM):
  1. Script runs automatically
  2. Emails you 0-3 bet recommendations
  3. You LOG the bets (don't place real money yet)
  4. Next day, check results
  5. Update tracking spreadsheet
```

**Expected (Nov-Dec, 2 months)**:
- Total bets: ~160
- Wins: ~18 (11-12%)
- Total stake: ~2.0 units
- Expected P&L: +0.05 to +0.15 units
- Expected ROI: +2.5% to +7.5%

**Success Criteria** (by Dec 31):
- ✅ ROI > +2% (validates backtest)
- ✅ Bets/month: 60-100 (on track)
- ✅ Avg odds: 8-11 (in range)
- ✅ No major errors (script works)

---

#### **Phase 3: Decision Point (Jan 1, 2026)**

**If paper trading successful** (ROI > +2%):
```
✅ Deploy with SMALL real stakes:
   - £10-20/bet (very conservative)
   - Max £100/week
   - Continue for Q1 2026
   - Monitor weekly

✅ Retrain model:
   - Training: 2006-2024 (add 2024 data)
   - Validation: 2025 (your paper trading period!)
   - This validates if 2025 matched backtest
```

**If paper trading failed** (ROI < 0%):
```
❌ Don't deploy real money
🔍 Analyze why:
   - Calibration drift?
   - Market changed?
   - Threshold issues?
   
🔄 Options:
   - Retune thresholds
   - Try different approach
   - More research needed
```

---

## 🔄 **Retraining Schedule**

### **Annual Retraining (Recommended)** ⭐

```
Current Model (Oct 2025):
  Training: 2006-2023
  Validation: 2024-2025 (backtest)
  Deployment: Nov-Dec 2025 (paper trade)

Model v2 (Jan 1, 2026):
  Training: 2006-2024 ← Add 2024
  Validation: 2025 ← Your paper trading results!
  Deployment: 2026
  
Model v3 (Jan 1, 2027):
  Training: 2006-2025
  Validation: 2026
  Deployment: 2027
```

**Retraining Process**:
```bash
# Jan 1, 2026
cd /home/smonaghan/GiddyUpModel/giddyup

# Update training config
# Edit: train_date_to = "2024-12-31"

# Retrain
rm -f data/training_dataset.parquet
uv run python tools/train_model.py > training_2026_model.log 2>&1 &

# Wait ~60 min for training

# Backtest on 2025
uv run python tools/backtest_hybrid.py

# Compare to paper trading results
# If aligned → deploy new model for 2026
```

---

### **Why Annual Retraining**

✅ **Pros**:
- Simple schedule (once per year)
- Always have fresh holdout year
- Enough training data (15+ years)
- Captures slow market evolution
- Not overfitting to recent noise

❌ **Cons**:
- Model ages over year
- Misses mid-year trends
- Less adaptive

**Verdict**: Annual is sufficient for horse racing (market evolves slowly).

---

### **Alternative: Quarterly Retraining**

```
Q4 2025: Train on 2006-2024 Q1-Q2, validate on Q3-Q4
Q1 2026: Train on 2006-2024, validate on 2025
Q2 2026: Train on 2006-2025 Q1, validate on Q1
```

**More adaptive** but more complex. Only needed if market changes rapidly.

---

## 🎯 **Daily Workflow (Starting Nov 1, 2025)**

### **Morning (8:00 AM)**

```bash
# Script runs automatically (cron job)
cd /home/smonaghan/GiddyUpModel/giddyup
uv run python tools/score_tomorrow_hybrid.py

# Output (example):
# ================================================================================
# 🎯 BET RECOMMENDATIONS FOR 2025-11-02
# ================================================================================
# 
# Total Bets: 3
# Total Stake: 0.042 units
#
# 🏇 Race 1
#    Time: 14:30
#    Course: Ascot
#    Horse: Thunder Road (GB) (#5)
#    Odds: 9.50 (Market Rank: 4)
#    
#    Model: 17.2% | Market: 10.5% | Disagreement: 1.64x
#    Edge: 6.7pp | EV: +12.3%
#    
#    💰 BET: 0.015 units @ 9.50
#
# [Race 2, Race 3...]
```

---

### **Evening (After Racing)**

```
1. Check results on racing websites
2. Update tracking spreadsheet:
   - Did horse win/lose?
   - Actual odds obtained?
   - P&L calculation
3. Weekly: Compare to backtest expectations
```

---

### **Weekly Review (Every Sunday)**

```
Check:
  ✅ Bets this week: 15-25 (on track?)
  ✅ ROI this week: Close to +3%?
  ✅ Avg odds: 8-11?
  ✅ Win rate: 10-13%?
  
Red flags:
  ❌ Win rate < 8% (calibration issue)
  ❌ ROI < -10% (strategy not working)
  ❌ Avg odds < 6 (betting too many favorites)
  ❌ Bets < 10/week (filters too tight)
```

---

### **Monthly Review**

```
Expected Monthly:
  Bets: 60-100
  Stake: ~0.8-1.2 units
  P&L: -0.5u to +0.9u (variance)
  ROI: -20% to +80% (wide swing per month)
  
Over 2 months (Nov-Dec):
  Bets: 120-200
  P&L: Should trend positive (+0.1 to +0.3u)
  ROI: Should approach +3%
```

---

## 💰 **Staking Guide**

### **Unit Size Selection**

Choose based on your bankroll:

| Bankroll | Conservative | Moderate | Aggressive |
|----------|--------------|----------|------------|
| £1,000 | 1u = £5 | 1u = £10 | 1u = £20 |
| £5,000 | 1u = £25 | 1u = £50 | 1u = £100 |
| £10,000 | 1u = £50 | 1u = £100 | 1u = £200 |

**Typical bet**: 0.01-0.03 units  
**Max bet**: 0.30 units (cap)

**Examples with £5,000 bankroll (1u = £50)**:
- Typical bet: 0.015u = £0.75
- Larger bet: 0.030u = £1.50
- Max bet: 0.300u = £15.00

**Monthly turnover**: ~£40-60  
**Expected monthly profit**: £1-3 (at +3% ROI)

---

## 🚨 **Stop/Retune Triggers**

### **Stop Immediately If:**

- ❌ ROI < -15% after 100+ bets (no edge)
- ❌ Win rate < 7% persistently (severe calibration issue)
- ❌ 3 consecutive months with ROI < -20%
- ❌ Technical errors in scoring script

---

### **Retune Thresholds If:**

**ROI consistently -5% to 0%**:
```
Tighten:
  - Disagreement: 2.5x → 3.0x
  - Edge: 8pp → 10pp
  - Rank: 3-6 → 4-5 only
```

**Bets < 30/month**:
```
Relax:
  - Disagreement: 2.5x → 2.0x
  - Edge: 8pp → 6pp
  - Odds: 7-12 → 6-13
```

---

## 📋 **Deployment Checklist**

### **Before Nov 1, 2025**

- [ ] Test scoring script on recent date
- [ ] Verify outputs match expectations
- [ ] Set up cron job for daily automation
- [ ] Create tracking spreadsheet/database
- [ ] Document unit size decision (e.g., 1u = £50)
- [ ] Set up email alerts (optional)

### **Nov-Dec 2025 (Paper Trading)**

- [ ] Run daily scoring (no real money)
- [ ] Log every signal
- [ ] Track results vs predictions
- [ ] Weekly review (bets, ROI, odds)
- [ ] Monthly summary
- [ ] Target: 120-200 bets total

### **Jan 1, 2026 (Evaluation)**

- [ ] Calculate 2-month ROI
- [ ] Compare to backtest (+3.1% target)
- [ ] If successful (ROI > +2%): Deploy small stakes
- [ ] Retrain on 2006-2024
- [ ] Validate 2025 matches paper trading

### **Q1 2026 (Live Trading)**

- [ ] Deploy with £10-20/bet
- [ ] Max £100/week
- [ ] Weekly monitoring
- [ ] Monthly review
- [ ] Scale up if working

---

## 🎯 **Decision Framework**

### **After 2 Months Paper Trading (Dec 31, 2025)**

**Scenario A: ROI > +5%** (Better than backtest)
```
Action: Deploy immediately with small stakes
Confidence: High
Stake size: Start at 50% of target (£5-10/bet)
```

**Scenario B: ROI +2% to +5%** (Matches backtest)
```
Action: Deploy cautiously
Confidence: Moderate
Stake size: Start at 25% of target (£2.50-5/bet)
Monitor: Very closely for 3 months
```

**Scenario C: ROI 0% to +2%** (Below backtest)
```
Action: Extended paper trading (3 more months)
Confidence: Low
Decision: Wait for more data
```

**Scenario D: ROI < 0%** (Losing)
```
Action: DO NOT DEPLOY
Analysis: Why did backtest not hold?
  - Calibration drift?
  - Market changed?
  - Overfitting to 2024-2025?
Options:
  - Retune thresholds
  - Different approach
  - More research
```

---

## 🔄 **Retraining Schedule: Your Question Answered**

### **Your Question**:
> "Should I continue using this until end of year then retrain based on the bets we make?"

### **Answer: YES** ⭐

**Recommended timeline**:

```
NOW (Oct 2025):
  ✅ Use current model (trained on 2006-2023)
  ✅ Paper trade Nov-Dec 2025
  ✅ DON'T retrain yet
  ✅ Track all signals
  
Jan 1, 2026:
  ✅ Retrain on 2006-2024
  ✅ Validate on 2025 (your paper trading results!)
  ✅ This validates if backtest was realistic
  ✅ Deploy new model for 2026
  
Ongoing:
  ✅ Retrain annually (every Jan 1)
  ✅ Always hold out most recent year
  ✅ Always validate on fresh data
```

**Why wait until Jan 1**:
1. **Clean time boundary** (full year of data)
2. **Validates backtest** (2025 paper trading vs 2024-2025 backtest)
3. **Enough data** (adding full 2024 year)
4. **Operationally simple** (annual schedule)

---

### **DON'T Retrain On Your Own Bets**

**Bad approach** ❌:
```
Train on 2006-2023
Bet in Nov-Dec 2025
Retrain on 2006-2023 + your Nov-Dec bets
```

**Why this is bad**:
- Only ~160 new bets (tiny sample)
- Introduces selection bias (you only bet where model was confident)
- Overfits to your own results
- Loses generalization

**Good approach** ✅:
```
Train on 2006-2023
Bet in Nov-Dec 2025
Jan 1, 2026: Retrain on 2006-2024 (ALL races, not just your bets)
```

**Why this is good**:
- Adds ~95,000 new races from 2024
- No selection bias
- Keeps model general
- Fresh validation (2025)

---

## 🛠️ **How to Use Scoring Script Daily**

### **Manual Run (For Testing)**

```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# Score tomorrow
uv run python tools/score_tomorrow_hybrid.py

# Score specific date
uv run python tools/score_tomorrow_hybrid.py --date 2025-11-15

# Output shows:
# - Number of bets
# - Horse names, courses, times
# - Odds, stakes, edge, disagreement
# - Total stake for the day
```

---

### **Automated Daily Run (Production)**

```bash
# Create cron job
crontab -e

# Add this line (runs at 8:00 AM daily):
0 8 * * * cd /home/smonaghan/GiddyUpModel/giddyup && /home/smonaghan/.local/bin/uv run python tools/score_tomorrow_hybrid.py >> /home/smonaghan/GiddyUpModel/giddyup/logs/daily_scoring.log 2>&1

# Create logs directory
mkdir -p /home/smonaghan/GiddyUpModel/giddyup/logs
```

---

### **Optional: Email Alerts**

Add to script:
```python
# At end of score_tomorrow_hybrid.py

if len(bets) > 0:
    import smtplib
    from email.mime.text import MIMEText
    
    body = f"""
    Daily Bets for {target_date}:
    
    Total: {len(bets)} bets
    Total Stake: {total_stake:.3f} units
    
    {bet_details}
    """
    
    msg = MIMEText(body)
    msg['Subject'] = f'GiddyUp Bets: {len(bets)} for {target_date}'
    msg['From'] = 'giddyup@yourdomain.com'
    msg['To'] = 'you@email.com'
    
    # Send email
```

---

## 📊 **Typical Week Example (Nov 2025)**

**Monday Nov 4**:
- Script runs 8:00 AM
- Finds 4 bets for Tuesday
- Total stake: 0.052u (£2.60 with £50 units)
- You log the bets
- Tuesday evening: 1 won, 3 lost
- Day P&L: -0.025u

**Tuesday Nov 5**:
- 3 bets for Wednesday
- 1 wins
- Day P&L: +0.08u

**Wednesday Nov 6**:
- 2 bets
- 0 wins  
- Day P&L: -0.02u

**Thursday Nov 7**:
- 5 bets
- 2 wins
- Day P&L: +0.12u

**Friday Nov 8**:
- 4 bets
- 0 wins
- Day P&L: -0.04u

**Weekend Nov 9-10**:
- 8 bets total
- 2 wins
- Weekend P&L: +0.05u

**Week Total**:
- 26 bets
- 6 wins (23%)
- Stake: 0.34u
- P&L: +0.16u
- ROI: +47%

**Good week!** Some weeks will be negative, but over time should trend +3%.

---

## 📈 **Expected Monthly Pattern**

```
Month 1 (Nov 2025):
  Bets: 70-90
  P&L: -0.3u to +0.5u (could be negative!)
  ROI: -30% to +50% (high variance)
  
Month 2 (Dec 2025):
  Bets: 60-80 (fewer racing days)
  P&L: -0.2u to +0.4u
  ROI: -20% to +40%
  
Combined 2 months:
  Bets: 130-170
  P&L: Should be positive (+0.1 to +0.4u)
  ROI: Should approach +3%
```

**Don't panic if one month is negative** - variance is high with small sample sizes.

---

## ✅ **Summary: Your Complete Plan**

### **Timeline**

```
Oct 25-31:
  - Test scoring script
  - Set up automation
  - Create tracking system
  
Nov 1 - Dec 31:
  - Paper trade (no real money)
  - Log ~160 bets
  - Track results daily
  - Target: +3% ROI
  
Jan 1, 2026:
  - Evaluate paper trading
  - If successful: Deploy small stakes
  - Retrain on 2006-2024
  - Validate on 2025
  - Deploy new model
  
Q1 2026:
  - Live trading (small stakes)
  - Weekly monitoring
  - Scale up if working
  
Jan 1, 2027:
  - Annual retrain (2006-2025)
  - Continue cycle
```

---

### **Expected Results (If Backtest Holds)**

**2 months paper trading** (Nov-Dec 2025):
- Bets: ~160
- P&L: +0.1 to +0.3 units
- ROI: +2% to +5%
- Validates model works live

**Full year 2026** (if deployed):
- Bets: ~980
- P&L: +0.5 to +1.5 units
- ROI: +3% to +5%
- With £50 units: +£25 to £75 profit

**This is realistic and achievable!** Not get-rich-quick, but systematic edge.

---

## 🎓 **Key Principles**

1. **Paper trade first** (validate before risking money)
2. **Start small** (£10-20/bet max initially)
3. **Track everything** (compare to backtest)
4. **Retrain annually** (Jan 1 schedule)
5. **Be patient** (3% ROI requires volume)
6. **Stop if broken** (ROI < -10% persistent)

---

**Ready to test the scoring script?** Let me know and I'll walk you through first run!

