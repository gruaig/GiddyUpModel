# 🎯 Betting Timing & Odds Strategy Guide

**Key Questions Answered**:
1. Should I take bookmaker prices to avoid commission?
2. When is the best time to place bets - morning or closer to off?

---

## 🏪 Bookmaker vs Exchange: The Commission Question

### **Your Question**: "What if bookmaker price matches our model - should we take it to avoid commission?"

**Short Answer**: **No, stick with exchange prices** even with 2% commission.

---

### **Why Exchange > Bookmaker (Even With Commission)**

| Factor | Bookmaker | Exchange | Winner |
|--------|-----------|----------|--------|
| **Commission** | 0% | 2% on winnings | 🟡 Bookmaker |
| **Typical Odds** | 10% lower | Baseline | ✅ Exchange |
| **Account Limits** | Restrict winners | No limits | ✅ Exchange |
| **Sustainability** | 6-12 months max | Unlimited | ✅ Exchange |
| **Liquidity** | £5-50/bet | £100-10,000+ | ✅ Exchange |
| **Model Calibration** | Not trained on | Trained on | ✅ Exchange |
| **Gubbing Risk** | 100% if winning | 0% | ✅ Exchange |

**Overall**: ✅ **Exchange wins 6-1**

---

### **The Math: "Matching" Odds Aren't Really Matching**

**Scenario**: Your model says bet at 10.0 odds

```
Bookmaker shows: 10.0 (looks like a match!)
Exchange shows:  10.5 (best back price)

After 2% commission:
  Exchange effective: 10.5 × 0.98 = 10.29

Real comparison:
  Bookmaker: 10.0 (no commission)
  Exchange:  10.29 (after 2% commission)
  
Exchange is STILL 2.9% better! ✅
```

**Rule of thumb**: Exchange needs to be only **2%** better to break even with bookmaker after commission.

---

### **Example: Real Race**

**Race**: Ascot 14:30, Horse: Thunder Road

```
Your Model:
  Fair odds: 8.0 (12.5% probability)
  Minimum acceptable: 9.0 (need edge)

Bookmaker Paddy Power:
  Odds: 9.0 ✓ (meets minimum)
  
Exchange Betfair:
  Odds: 10.0 ✓ (even better)
  After 2% commission: 9.8 effective

Decision:
  ❌ Don't take bookmaker 9.0
  ✅ Take exchange 10.0 (9.8 after commission)
  
Extra profit: 10.9% better value
```

**Even if bookmaker "matches", exchange is usually still better.**

---

### **The Gubbing Problem** 🚫

**Bookmakers restrict winning accounts:**

```
Month 1-3:   Full stake accepted (£20 bets)
Month 4-6:   Limits appear (max £5 bets)
Month 7-9:   Severe restrictions (max £1 bets)
Month 10-12: Account "gubbed" (max £0.50 bets)
Month 13+:   Effectively banned

Result: You can't scale up, wasted effort
```

**Exchange**: No restrictions ever. Win £10M, they're happy (they get commission).

---

### **When Bookmaker MIGHT Make Sense**

**Only these specific situations:**

✅ **1. Account Preservation Phase** (Months 1-3)
```
Goal: Keep bookmaker accounts alive for promotions/arbs
Strategy: Place LOSING bets with bookies to look like mug punter
Reality: Not compatible with value betting model
Verdict: Don't mix strategies
```

❌ **2. Massive Odds Difference** (Rare)
```
Scenario: Bookmaker 12.0 vs Exchange 9.0 (33% better!)
Reality: This almost never happens (arb bots fix it in seconds)
Verdict: Take it if you see it, but you won't
```

❌ **3. No Exchange Account Yet**
```
Scenario: You don't have Betfair account set up
Solution: Set up Betfair account before starting
Verdict: Don't bet until exchange ready
```

---

### **The Commission Illusion**

**People think**: "2% commission is expensive!"

**Reality**: Exchange odds are 5-15% better, so you save 3-13% overall.

```
Example bet: £100 stake

BOOKMAKER (9.0 odds, 0% commission):
  If win: £100 × 9.0 = £900 return
  Profit: £800
  
EXCHANGE (10.0 odds, 2% commission):
  If win: £100 × 10.0 = £1,000 gross
  Commission: £900 × 0.02 = £18
  Net: £1,000 - £18 = £982 return
  Profit: £882
  
Extra profit with exchange: +£82 (10.25% better) ✅
```

**Commission is tiny compared to odds improvement.**

---

### **Model Calibration Issue**

**Critical**: Your model was **trained on exchange prices** (`win_ppwap`).

```
Model sees:
  - Exchange odds distribution
  - Exchange market efficiency
  - Exchange vig-free probabilities
  
If you bet bookmaker odds:
  - Odds are systematically lower
  - Market efficiency different
  - Model calibration is OFF
  
Result: Model's edge calculation is wrong ❌
```

**Using bookmaker odds = Using model outside training domain**

---

### **Final Verdict: Bookmaker vs Exchange**

| Timeframe | Recommended | Why |
|-----------|-------------|-----|
| **Paper Trading (2 months)** | Exchange | Match your backtest exactly |
| **Live Trading (Year 1)** | Exchange | Build track record properly |
| **Scaling (Year 2+)** | Exchange | Only sustainable long-term |

**Never use bookmakers for systematic value betting.**

---

---

## ⏰ Betting Timing: Morning vs Pre-Off

### **Your Question**: "When is best time to bet - morning or closer to off?"

**Short Answer**: **T-60 to T-30 (30-60 min before off) is optimal** ⏰

---

### **Market Efficiency Timeline**

```
T-12 hours (Morning):
  ├─ Prices very wide (inefficient)
  ├─ Low liquidity (£50-200 available)
  ├─ Big swings possible
  └─ "Morning price" in racing.runners.win_morningwap

T-4 hours (Lunch):
  ├─ Prices stabilizing
  ├─ Moderate liquidity (£200-500)
  └─ Professional money entering

T-90 min (90 before off):
  ├─ Prices tightening
  ├─ Good liquidity (£500-2,000)
  └─ Market becoming efficient

T-60 min (60 before off): ⭐ YOUR MODEL'S SWEET SPOT
  ├─ Prices stable but not final
  ├─ High liquidity (£1,000-5,000)
  ├─ Model calibrated to this snapshot
  └─ racing.runners.win_ppwap (Pre-Play WAP)

T-30 min (30 before off):
  ├─ Prices near final
  ├─ Very high liquidity (£2,000-10,000)
  └─ Market very efficient

T-10 min (10 before off):
  ├─ Prices locked in
  ├─ Maximum liquidity
  ├─ Market most efficient
  └─ Hard to beat

T-2 min (In-Play):
  ├─ Prices final
  ├─ Near-perfect efficiency
  └─ No edge left
```

---

### **Model Calibration: T-60 is Key**

**Your model was trained on `win_ppwap`** = T-60 snapshot.

```python
# What win_ppwap means:
Pre-Play WAP = Weighted Average Price
Captured: ~60 minutes before scheduled off time
Purpose: Stable snapshot before in-play volatility

Your backtest:
  ✅ Used win_ppwap (T-60)
  ✅ +3.1% ROI validated
  ✅ 1,794 bets over 22 months
```

**To match backtest results, bet at same time: T-60** ✅

---

### **Why Not Morning Prices?**

**Pros of morning betting:**
```
✅ Sometimes better odds (before smart money)
✅ Less competition
✅ More leisure time (not rushed)
```

**Cons of morning betting:**
```
❌ Model NOT calibrated on morning prices
❌ Lower liquidity (hard to get full stake)
❌ Prices volatile (might move against you)
❌ Non-runners risk (horse scratched = void bet)
❌ Going changes (official going declared later)
❌ Jockey changes (not confirmed until declarations)
❌ Your edge calculation is OFF
```

**Example Problem**:

```
Morning (T-12 hours):
  Thunder Road: 12.0 odds
  Model says: GREAT value! (based on T-60 calibration)
  You bet: £20
  
By T-60:
  Thunder Road: 8.0 odds (smart money came in)
  Model would say: NO BET (edge gone)
  You're stuck: Already bet at 8.0 effective
  
Result: Bet that wouldn't have qualified ❌
```

**Morning prices are not the same market your model learned.**

---

### **Why Not Very Close to Off?**

**Pros of late betting (T-10):**
```
✅ Maximum liquidity
✅ Confirmed non-runners
✅ Final going/jockey info
```

**Cons of late betting:**
```
❌ Market most efficient (hardest to beat)
❌ Your edge is smaller
❌ Time pressure (rushed decisions)
❌ Risk of missing bet (technical issues)
❌ Can't match backtest timing
```

**Research shows**: Market efficiency increases closer to off.

```
T-60:  Your model's AUC ~0.71 vs market
T-10:  Market's AUC ~0.95 (near perfect)

Translation:
  T-60: You find mispricing
  T-10: Market fixed most mispricing
```

**Late betting = Competing against final market wisdom.**

---

### **Optimal Betting Window: T-60 to T-30**

**Recommendation**:

```
Ideal: 60-45 minutes before off
Acceptable: 45-30 minutes before off
Avoid: >90 minutes (too early)
Avoid: <30 minutes (too late)
```

---

### **Practical Daily Workflow**

### **Morning (8:00 AM)** - Research Phase

```bash
# Run selection script
./get_tomorrows_bets_v2.sh 2025-10-18 50000

# Review selections:
#   - 3 bets identified
#   - Horses, courses, times
#   - Provisional odds/stakes
```

**What to do**:
- ✅ Review selections
- ✅ Check non-runners (Racing Post)
- ✅ Note race times
- ✅ Set alerts for T-60

**What NOT to do**:
- ❌ Don't bet yet!
- ❌ Don't use morning prices
- ❌ Don't panic if odds moved

---

### **Pre-Race (T-60)** - Betting Phase

```
For 14:30 race → Bet window: 13:15-13:45

Steps:
1. Check if horse still running (non-runners?) ✓
2. Check current Betfair odds ✓
3. Compare to model's minimum odds
4. If odds >= model minimum → PLACE BET
5. If odds < model minimum → SKIP (edge gone)
6. Log bet in spreadsheet
```

**Decision tree**:

```
Model recommended: Thunder Road @ 9.0+ needed

Current Betfair odds: 10.5
  → ✅ BET (better than needed)

Current Betfair odds: 9.2
  → ✅ BET (slightly better, OK)

Current Betfair odds: 8.5
  → ❌ SKIP (below minimum, edge gone)

Current Betfair odds: 11.0 but only £10 available
  → ⚠️ PARTIAL (bet what's available, or skip if too small)
```

---

### **Real Example: Full Day**

**Date**: 2025-10-18

**Morning (8:00 AM)**:
```bash
$ ./get_tomorrows_bets_v2.sh 2025-10-18 50000

Output:
  🎯 BET #1 | 14:30 | Ascot | Thunder Road | 9.50 odds | £20
  🎯 BET #2 | 15:45 | Newmarket | Silver Storm | 10.00 odds | £15
  🎯 BET #3 | 17:00 | Leopardstown | Celtic Dawn | 11.00 odds | £12

Notes:
  - 3 races today
  - Set alerts: 13:15, 14:30, 15:45
  - These are PROVISIONAL (check at T-60)
```

---

**13:15 (T-75 for first race)** - Check In Early:
```
Thunder Road:
  Current Betfair: 10.0 (drift from 9.5)
  Model minimum: 9.0
  Liquidity: £2,500 available
  Non-runners: None
  
Action: Wait until 13:30 (T-60)
```

---

**13:30 (T-60 for first race)** - BETTING TIME:
```
Thunder Road:
  Current Betfair: 10.2 (drifted more)
  Model minimum: 9.0
  Liquidity: £3,200 available
  
✅ PLACE BET: £20 @ 10.2
Log in spreadsheet: 14:30, Ascot, Thunder Road, 10.2, £20
```

---

**14:15 (T-90 for second race)** - Monitor:
```
Silver Storm:
  Current Betfair: 8.5 (steamed from 10.0!)
  Model minimum: 9.5
  
⚠️ Edge is GONE - may not bet this one
Wait until 14:45 to confirm
```

---

**14:45 (T-60 for second race)** - Decision:
```
Silver Storm:
  Current Betfair: 8.2 (more steam)
  Model minimum: 9.5
  
❌ SKIP - Odds below minimum, no edge left
Update spreadsheet: SKIPPED (steamed off)
```

---

**16:00 (T-60 for third race)** - Final Bet:
```
Celtic Dawn:
  Current Betfair: 11.5 (drifted from 11.0)
  Model minimum: 10.5
  Liquidity: £1,800 available
  
✅ PLACE BET: £12 @ 11.5 (even better!)
Log in spreadsheet: 17:00, Leopardstown, Celtic Dawn, 11.5, £12
```

---

**End of Day**:
```
Planned: 3 bets
Placed: 2 bets (Thunder Road, Celtic Dawn)
Skipped: 1 bet (Silver Storm - steamed off)
Total stake: £32

This is NORMAL! ✓
~33% of morning selections will steam off by T-60
```

---

### **Why Some Bets Steam Off**

**Your model finds value at T-60**. But morning to T-60, market moves:

```
Morning → T-60 movements:

Drift (odds ↑):
  - Less popular than expected
  - Your model's edge INCREASES
  - Even better value! ✅
  
Steam (odds ↓):
  - Smart money came in
  - Your model's edge DECREASES  
  - May lose value ❌
```

**This is the game**: You're competing with the market.

- 60-70% of morning selections still have edge at T-60 ✅
- 30-40% steam off (skip these) ❌

**Don't chase steamed bets!** Discipline = Profit.

---

### **The "Morning Odds Were Better!" Trap**

**Common mistake**:

```
❌ BAD THINKING:
"At 8am, odds were 12.0, now they're 9.0. 
I should have bet this morning!"

✅ CORRECT THINKING:
"At 8am, my model wasn't calibrated for that market.
Smart money made the price 9.0 for a reason.
At T-60, there's no edge, so skip."
```

**Morning odds are not "better"** - they're just less informed.

Your model learned T-60 prices = You bet at T-60 prices.

---

### **Special Cases**

#### **Case 1: Race Off Time Changed**

```
Originally: 14:30 off
Changed to: 14:45 off (15 min delay)

Action: Adjust your T-60 window to new time
Bet window: 13:30 → 13:45
```

---

#### **Case 2: Non-Runner Declared**

```
13:00: Thunder Road declared non-runner

Action: 
  ❌ Skip this bet (horse not running)
  ✓ Update spreadsheet: NON-RUNNER
  ✓ Check if any reserves moved into the race
```

---

#### **Case 3: You're Not Available at T-60**

```
Problem: You're in a meeting 13:30-14:00
Race: 14:30 (T-60 = 13:30)

Options:
  A) Bet at T-90 (13:00) - Slightly suboptimal but OK
  B) Bet at T-30 (14:00) - More risky (market efficient)
  C) Skip this race - Safest
  
Recommendation: Option A or C
Never bet T-10 or later (too efficient)
```

---

#### **Case 4: Liquidity Too Low**

```
T-60: Thunder Road @ 10.5 odds
Need: £20 stake
Available: Only £8 at 10.5

Options:
  A) Take £8 partial stake (40% of plan)
  B) Wait 5-10 min for more liquidity
  C) Skip (if really important, don't compromise)
  
Recommendation: 
  - If £8+ available: Take it
  - If <£5 available: Skip
```

---

## 📋 Summary: Best Practices

### **Odds Source** 🏦

| Option | Verdict | Why |
|--------|---------|-----|
| **Betfair Exchange** | ✅ **USE THIS** | Better odds, no limits, model-trained |
| Bookmaker (Paddy Power, etc.) | ❌ Avoid | Lower odds, get banned, not calibrated |
| Morning Exchange | ❌ Avoid | Not calibrated, volatile |

---

### **Timing** ⏰

| Window | Verdict | Why |
|--------|---------|-----|
| **T-60 to T-45** | ✅ **OPTIMAL** | Model calibration, good liquidity |
| T-45 to T-30 | ✅ Good | Acceptable, slightly late |
| T-90 to T-60 | 🟡 OK | If needed, monitor for moves |
| Morning (T-12h) | ❌ Avoid | Not calibrated, too early |
| T-30 to T-10 | ❌ Avoid | Market too efficient |
| T-10 to T-0 | ❌ Never | No edge left |

---

### **Decision Flow** 🎯

```
1. Morning (8 AM):
   ├─ Run selection script
   ├─ Identify potential bets
   ├─ Set T-60 alerts
   └─ Do NOT bet yet

2. T-60 Before Each Race:
   ├─ Check non-runners ✓
   ├─ Check current Betfair odds ✓
   ├─ Compare to model minimum ✓
   ├─ IF odds >= minimum AND liquidity OK:
   │   └─ PLACE BET ✅
   └─ ELSE:
       └─ SKIP (edge gone) ❌

3. Evening:
   ├─ Check results
   ├─ Update spreadsheet
   └─ Calculate P&L
```

---

### **Key Principles** 🎓

1. **Exchange > Bookmaker** (even with 2% commission)
2. **T-60 is your sweet spot** (model calibrated here)
3. **Morning prices are traps** (not calibrated, volatile)
4. **Some bets will steam off** (30-40% normal)
5. **Discipline beats FOMO** (skip steamed bets)
6. **Match your backtest** (same timing = same results)

---

## 🧮 Worked Example: Commission Math

**Bet**: Thunder Road, £100 stake

### **Scenario A: Bookmaker** ❌

```
Odds: 9.0
Commission: 0%

If WIN:
  Gross return: £100 × 9.0 = £900
  Commission: £0
  Net return: £900
  Profit: £800

If LOSE:
  Loss: -£100
```

---

### **Scenario B: Exchange** ✅

```
Odds: 10.0 (typical 10% better)
Commission: 2% on profit

If WIN:
  Gross return: £100 × 10.0 = £1,000
  Profit: £900
  Commission: £900 × 0.02 = £18
  Net return: £982
  Profit: £882
  
Difference vs Bookmaker: +£82 (+10.25%) ✅

If LOSE:
  Loss: -£100 (same as bookmaker)
  Commission: £0 (only on winning bets)
```

**Result**: Exchange earns you **+£82 MORE** per £100 bet when you win.

---

### **Over 100 Bets**:

```
Strategy: 100 bets, £100 each, 11% win rate (model average)

Bookmaker (9.0 avg odds, 0% commission):
  11 wins: 11 × £800 = £8,800
  89 losses: 89 × -£100 = -£8,900
  Net: -£100 (negative even with edge!)

Exchange (10.0 avg odds, 2% commission):
  11 wins: 11 × £882 = £9,702
  89 losses: 89 × -£100 = -£8,900
  Net: +£802 ✅
  ROI: +8.02%

Difference: £902 more profit with exchange!
```

**Commission is TINY vs odds improvement.**

---

## 🚀 Action Items

**Before First Bet**:
- [ ] Open Betfair Exchange account
- [ ] Deposit bankroll (start small: £1,000-5,000)
- [ ] Test placing a £0.50 bet (practice mechanics)
- [ ] Set up T-60 alerts for race times

**Daily Routine**:
- [ ] 8:00 AM: Run selection script
- [ ] Review selections, note times
- [ ] T-60: Check odds, non-runners, liquidity
- [ ] T-60: Place bets IF odds >= model minimum
- [ ] Evening: Update spreadsheet with results

**Never**:
- [ ] ❌ Use bookmaker odds (get gubbed + lower odds)
- [ ] ❌ Bet morning prices (not calibrated)
- [ ] ❌ Bet T-10 or later (too efficient)
- [ ] ❌ Chase steamed bets (discipline = profit)

---

## 📚 Further Reading

- `docs/ANSWER_EXCHANGE_VS_BOOK.md` - Exchange vs bookmaker detailed comparison
- `docs/DEPLOYMENT_GUIDE_HYBRID.md` - Full deployment workflow
- `docs/DAILY_WORKFLOW.md` - Day-to-day operations
- `profitable_models/hybrid_v3/README.md` - Model specifics

---

**TL;DR**:
- ✅ **Bet on Exchange** (Betfair) even with 2% commission
- ✅ **Bet at T-60** (30-60 minutes before off)
- ❌ **Never use bookmakers** (get banned + lower odds)
- ❌ **Never bet morning** (not calibrated)

**Follow this = Match your +3.1% ROI backtest** 🎯

---

**Developed by**: Sean MoonBoots  
**Date**: October 17, 2025

