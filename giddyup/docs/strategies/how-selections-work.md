# 🎯 How Morning Selections Work

**Complete explanation of how HorseBot finds value bets**

---

## 📊 The Complete Flow

### 1. Morning: You Run HorseBot

```bash
python3 HorseBot_Simple.py start 2025-10-21 A50000 B5000
```

### 2. HorseBot Calls `RUN_BOTH_STRATEGIES.sh`

The bot executes:
```bash
./strategies/RUN_BOTH_STRATEGIES.sh 2025-10-21 55000
```

(Uses total bankroll: £50,000 + £5,000 = £55,000)

### 3. Script Queries PostgreSQL Database

The script runs **two SQL queries** (one for each strategy) against your `horse_db` database:

---

## 🔍 Strategy A: Hybrid V3

### SQL Query Breakdown

**Step 1: Get Race Data**
```sql
WITH race_data AS (
    SELECT 
        r.race_id, r.race_date, r.off_time,
        c.course_name, h.horse_name, t.trainer_name,
        COALESCE(ru.win_ppwap, ru.dec) as decimal_odds,
        ROW_NUMBER() OVER (PARTITION BY r.race_id ORDER BY odds) as market_rank,
        1.0 / odds as q_market,
        SUM(1.0 / odds) OVER (PARTITION BY r.race_id) as overround
    FROM racing.runners ru
    JOIN racing.races r ON r.race_id = ru.race_id
    WHERE r.race_date = '2025-10-21'
    AND odds >= 1.01
)
```

**What this does:**
- Gets all horses running today
- Calculates their market position (favorite, 2nd favorite, etc.)
- Calculates market probability (`q_market = 1 / odds`)
- Calculates bookmaker overround (total probability > 1.0)

**Step 2: Calculate Model Probability**
```sql
with_calcs AS (
    SELECT *, 
        q_market / overround as q_vigfree,  -- Remove vig
        CASE 
            WHEN market_rank = 3 THEN (q_market / overround) * 2.4
            WHEN market_rank = 4 THEN (q_market / overround) * 2.3
            WHEN market_rank = 5 THEN (q_market / overround) * 2.0
            WHEN market_rank = 6 THEN (q_market / overround) * 1.8
            ELSE (q_market / overround) * 1.1
        END as p_model
    FROM race_data
)
```

**What this does:**
- Removes bookmaker margin (`q_vigfree`)
- Applies **position-based multipliers** to estimate true probability
- **Key insight:** 3rd-6th favorites often underestimated by market!
  - 3rd favorite: 2.4x multiplier (market undervalues significantly)
  - 4th favorite: 2.3x multiplier
  - 5th favorite: 2.0x multiplier
  - 6th favorite: 1.8x multiplier

**Step 3: Find Value Bets**
```sql
with_metrics AS (
    SELECT *,
        p_model / q_vigfree as disagreement,  -- How much we disagree with market
        p_model - q_vigfree as edge_pp,       -- Edge in percentage points
        -- Calculate expected value with 2% commission
        CASE WHEN market_rank <= 2 
             THEN (p_model * (odds - 1) * 0.98 - (1 - p_model)) * 0.3
             ELSE p_model * (odds - 1) * 0.98 - (1 - p_model) 
        END as ev_adjusted
    FROM with_calcs
)
```

**What this calculates:**
- **Disagreement:** How much model disagrees with market (want 2.2x+)
- **Edge:** Percentage point advantage (want 6pp+)
- **EV:** Expected value after 2% Betfair commission

**Step 4: Filter for Quality Bets**
```sql
filtered AS (
    SELECT * FROM with_metrics
    WHERE decimal_odds BETWEEN 7.0 AND 12.0    -- Sweet spot odds range
    AND market_rank BETWEEN 3 AND 6             -- 3rd to 6th favorite
    AND overround <= 2.20                       -- Not too much vig
    AND disagreement >= 2.20                    -- Strong disagreement
    AND edge_pp >= 0.06                         -- Minimum 6% edge
    AND ev_adjusted >= 0.03                     -- Positive EV
)
```

**Filters:**
- ✅ Odds between 7.0 and 12.0 (value zone)
- ✅ 3rd-6th favorites only (market inefficiency)
- ✅ Low bookmaker margin (competitive markets)
- ✅ Model disagrees 2.2x+ with market
- ✅ At least 6pp edge
- ✅ Positive expected value

**Step 5: Best Bet Per Race**
```sql
best_per_race AS (
    SELECT *, 
        ROW_NUMBER() OVER (PARTITION BY race_id ORDER BY edge_pp DESC) as rank
    FROM filtered
)
SELECT * FROM best_per_race WHERE rank = 1
```

**What this does:**
- Picks the **best value bet** from each race (highest edge)
- One bet per race maximum

---

## 🔵 Strategy B: Path B

### Differences from Strategy A

**1. Odds Range:**
```sql
WHERE odds BETWEEN 7.0 AND 16.0  -- Wider range, accepts longer odds
```

**2. Blended Probability:**
```sql
-- Uses LAMBDA to blend model with market
p_blend = (1 - lambda) * p_model + lambda * q_vigfree

Where lambda varies by odds:
  - Odds < 8.0:  lambda = 0.40 (40% market, 60% model)
  - Odds < 12.0: lambda = 0.15 (15% market, 85% model)
  - Odds >= 12.0: lambda = 0.50 (50% market, 50% model)
```

**Why blend?**
- At lower odds: Market is more accurate, trust it more
- At mid odds: Model is strong, trust it mostly
- At higher odds: Market is volatile, blend 50/50

**3. Different Edge Requirements:**
```sql
edge_min_required = 
  - Odds < 8.0:  15% edge required
  - Odds < 12.0: 15% edge required
  - Odds >= 12.0: 16% edge required (stricter for longshots)

WHERE edge_pp >= edge_min_required * 0.85  -- Allow 85% of minimum
AND ev >= 0.015  -- Lower EV threshold than Strategy A
```

**4. Different Stake Calculation:**
```sql
-- Strategy A
stake_gbp = 0.015 * UNIT_GBP  -- 1.5% of unit

-- Strategy B  
stake_gbp = 0.04 * UNIT_GBP   -- 4% of unit
```

With your setup (A50000 B5000):
- Unit = Bankroll / 100
- Strategy A Unit = £500 → Stake = £7.50 (0.015 * 500)
- Strategy B Unit = £50 → Stake = £2.00 (0.04 * 50)

---

## 🎯 What Makes a Selection

### Strategy A Requirements:
1. ✅ **Odds:** 7.0 to 12.0
2. ✅ **Market Rank:** 3rd to 6th favorite
3. ✅ **Overround:** ≤ 2.20 (competitive market)
4. ✅ **Disagreement:** ≥ 2.2x (model thinks much better chance)
5. ✅ **Edge:** ≥ 6pp (6% advantage)
6. ✅ **EV:** ≥ 0.03 (3% expected value)

### Strategy B Requirements:
1. ✅ **Odds:** 7.0 to 16.0 (wider)
2. ✅ **Market Rank:** 3rd to 6th favorite
3. ✅ **Overround:** ≤ 2.20
4. ✅ **Edge:** ≥ 13-16% (stricter)
5. ✅ **EV:** ≥ 1.5% (lower than A)

---

## 💡 The Value Betting Philosophy

### Why 3rd-6th Favorites?

**Market Psychology:**
- 1st-2nd favorites: Heavily backed, often overbet
- 3rd-6th favorites: **Overlooked** by public
- 7th+ favorites: Too unpredictable

**Your Model Exploits:**
- Identifies when 3rd-6th favorites are **undervalued**
- Market focuses on top 2, ignoring good value further down
- Position-based multipliers (2.0x - 2.4x) account for this

### Why Odds Range 7.0 - 12.0 (Strategy A)?

- **Too low (<7.0):** Overbet, poor value
- **Sweet spot (7.0-12.0):** Market inefficient, value available
- **Too high (>12.0):** Too random, need more data

### The "Disagreement" Metric

```
disagreement = p_model / q_vigfree

Example:
  Market says 10% chance (q_vigfree = 0.10)
  Model says 22% chance (p_model = 0.22)
  Disagreement = 0.22 / 0.10 = 2.2x
  
This means: Model thinks horse is 2.2x more likely to win than market!
```

---

## 📈 Example Selection

### Real Example from Today:

**Horse:** Village Master (IRE)  
**Course:** Kempton  
**Time:** 16:25  

**Market Data:**
- Odds: 8.30 (Market probability: 12.0%)
- Market rank: 4th favorite
- Overround: 1.15 (competitive)

**Model Calculation:**
```
q_vigfree = 0.120 / 1.15 = 0.104 (10.4% fair probability)
p_model = 0.104 * 2.3 = 0.239 (23.9% model probability)
disagreement = 0.239 / 0.104 = 2.30x
edge = 23.9% - 10.4% = 13.5pp
ev = 0.239 * (8.30 - 1) * 0.98 - (1 - 0.239) = 0.095 (9.5% EV!)
```

**Filters:**
- ✅ Odds 8.30 (in range 7.0-12.0)
- ✅ Market rank 4 (in range 3-6)
- ✅ Overround 1.15 (< 2.20)
- ✅ Disagreement 2.30x (>= 2.20)
- ✅ Edge 13.5pp (>= 6pp)
- ✅ EV 9.5% (>= 3%)

**Result:** ✅ **SELECTED!**

**Actual Result:** 🏆 **WON** at 8.00 → +£51.45!

---

## 🎲 The Math Behind It

### Expected Value (EV) Formula

```
EV = (p_model × (odds - 1) × 0.98) - (1 - p_model)

Where:
  p_model = Estimated win probability
  odds = Decimal odds
  0.98 = After 2% Betfair commission
  
Positive EV = Profitable bet long-term
```

### Kelly Criterion (Stake Sizing)

```
Kelly % = (p_model × odds × 0.98 - 1) / (odds - 1)

But we use fractional Kelly (safer):
  Strategy A: 1.5% of unit (very conservative)
  Strategy B: 4% of unit (more aggressive)
```

---

## 📊 Why This Works

### Edge Sources:

1. **Position Bias**
   - Market overvalues favorites
   - Undervalues 3rd-6th horses
   - Your model corrects this

2. **Statistical Modeling**
   - Position-based probability adjustments
   - Vig-free probability calculations
   - Edge and disagreement filters

3. **Quality Gates**
   - Only competitive markets (low overround)
   - Minimum edge requirements
   - Positive EV mandate

4. **Risk Management**
   - Fractional Kelly staking
   - Maximum drift protection (15%)
   - Time-based entry (T-60)

---

## 🔧 How Bankroll Affects Selections

### With A50000 B5000:

**Strategy A:**
- Bankroll: £50,000
- Unit: £500 (1% of bankroll)
- Stake: £7.50 (1.5% of unit)

**Strategy B:**
- Bankroll: £5,000
- Unit: £50 (1% of bankroll)
- Stake: £2.00 (4% of unit)

**The query doesn't change based on bankroll!**
- Same selections found
- Only **stake sizes** change
- Bankroll just determines position sizing

---

## 🎯 What Gets Written to CSV

After the SQL query runs, results saved to:
`strategies/logs/daily_bets/betting_log_2025.csv`

**Columns:**
- `date` - 2025-10-21
- `time` - 16:25 (race time)
- `course` - Kempton
- `horse` - Village Master (IRE)
- `odds` - 8.30 (expected odds)
- `strategy` - A-Hybrid_V3
- `reasoning` - "Rank 4/9 | Disagree 2.30x | Edge +13.5pp"
- `min_odds_needed` - 7.89 (95% of expected for Strategy A)
- `stake_gbp` - 7.50
- `result` - (empty, filled later)
- `pnl_gbp` - (empty, filled later)

---

## 🤖 What HorseBot Does With This

### Morning (8:00 AM):

1. **Runs SQL queries** → Gets 48 selections
2. **Loads from CSV** → Parses into memory
3. **Corrects times** → Adds 1 hour (UK time offset)
4. **Posts to Telegram** → Morning picks card

### During Day:

For each selection, at T-60:
1. **Check Betfair odds** → Get current price
2. **Compare to min_odds_needed:**
   - If `current >= min` → **PLACE BET** ✅
   - If `current < min` → **SKIP** (drift too much) ❌
3. **Post to Telegram** → Bet placed or skipped

### After Race (+10 minutes):

1. **Fetch result from Sporting Life API**
2. **Check if won/lost**
3. **Calculate P&L** (with 2% commission)
4. **Post to Telegram** → Result & P&L
5. **Save to database**

---

## 📚 Key Concepts Explained

### Overround

```
Overround = Sum of all implied probabilities

Fair market: 1.00 (100%)
Typical market: 1.10 - 1.20 (10-20% bookmaker margin)

Your filter: <= 2.20 (only competitive markets)
```

### Disagreement Ratio

```
disagreement = p_model / q_vigfree

1.0 = Perfect agreement
2.2 = Model thinks 2.2x more likely than market
3.0 = Model thinks 3x more likely!

Your filter: >= 2.20 (strong disagreement required)
```

### Edge (Percentage Points)

```
edge_pp = p_model - q_vigfree

Example:
  Model: 23.9% chance
  Market: 10.4% chance
  Edge: 13.5pp

Your filter: >= 6pp (6% advantage minimum)
```

### Expected Value (EV)

```
EV = (p_win × profit) - (p_lose × loss)

After commission:
EV = p_model × (odds - 1) × 0.98 - (1 - p_model)

Positive EV = Long-term profit expected
Your filter: >= 0.03 (3% EV minimum)
```

---

## 🎲 The Model's Logic

**Hypothesis:**
> "3rd-6th favorites in competitive markets are systematically undervalued by the betting public, who focus attention on the top 2 horses."

**How it exploits this:**
1. Identifies these overlooked horses
2. Estimates their TRUE probability (with multipliers)
3. Compares to market price
4. Bets when edge is significant
5. Uses fractional Kelly for safety

**Why it works:**
- Market psychology creates predictable bias
- Statistical advantage in position-based pricing
- Quality filters ensure only best opportunities
- Risk management protects bankroll

---

## 🔍 Where Data Comes From

### Your PostgreSQL Database (`horse_db`)

**Tables Used:**
- `racing.races` - Race schedule & details
- `racing.runners` - Horses in each race
- `racing.horses` - Horse information
- `racing.trainers` - Trainer data
- `racing.courses` - Course information

**Key Data:**
- `win_ppwap` - Weighted average pre-race odds
- `dec` - Decimal odds
- `race_date` - Tomorrow's date
- `off_time` - Race start time

**This data must be loaded BEFORE running the bot!**

---

## ⏰ Data Availability

Your selections depend on having **tomorrow's odds data** in the database.

**Typical workflow:**
1. **Evening (6-8 PM)** - Odds data loaded into database
2. **Morning (8 AM)** - Run bot to get selections
3. **Throughout day** - Monitor & place bets

If no selections found:
- Check if odds data loaded (`racing.runners` table)
- Check if data for correct date
- Check if odds in expected range

---

## 🎯 Summary

**Morning query finds value bets by:**

1. ✅ Getting all horses running tomorrow
2. ✅ Calculating market probabilities (removing vig)
3. ✅ Estimating TRUE probabilities (with position multipliers)
4. ✅ Finding disagreement (model vs market)
5. ✅ Calculating edge & expected value
6. ✅ Filtering for quality (odds range, rank, overround, edge, EV)
7. ✅ Selecting best bet per race
8. ✅ Writing to CSV with stake sizes
9. ✅ HorseBot loads and executes throughout the day

**Result:** Systematic value betting based on statistical edge! 📊🏇💰

