# Market Features & Data Leakage Prevention

## 🎯 Summary

**YES** - We incorporate Betfair market data into the model  
**BUT** - Only **PRE-RACE** data to avoid data leakage

---

## ⚠️ **The Data Leakage Problem**

### What is Data Leakage?

Using information that **wouldn't be available at prediction time** to train your model.

**Example of LEAKAGE:**
```python
# ❌ BAD - Using BSP to predict race outcomes
features = ["win_bsp", "official_rating", "trainer_form"]

# Problem: BSP is set at race START
# When predicting tomorrow's races, BSP doesn't exist yet!
# Model learns "low BSP = likely to win" (obvious!)
# But can't use this in production
```

**Result:** Model performs great in backtests but fails in production because the critical feature (BSP) doesn't exist yet.

---

## ✅ **Safe Pre-Race Features** (Available Before Race)

We use these Betfair fields that are available **BEFORE** the race starts:

### 1. Morning Prices
```python
"win_morningwap"       # Morning weighted average price
"win_morning_vol"      # Morning traded volume
"place_morningwap"     # Morning place prices
"place_morning_vol"
```

**Available:** ~4-12 hours before race  
**Use:** Market's early assessment

### 2. Pre-Play Prices
```python
"win_ppwap"            # Pre-play weighted average price
"win_ppmax"            # Pre-play maximum price  
"win_ppmin"            # Pre-play minimum price
"win_pre_vol"          # Pre-play volume
"place_ppwap"          # Place pre-play prices
"place_ppmax"
"place_ppmin"
"place_pre_vol"
```

**Available:** Up to race start  
**Use:** Market's final assessment (most informed)

---

## 🚫 **Unsafe Post-Race Features** (NOT Available at Prediction Time)

### DO NOT USE These for Training

```python
"win_bsp"              # ❌ Betfair Starting Price (set at race start)
"win_ipmax"            # ❌ In-play maximum (during race)
"win_ipmin"            # ❌ In-play minimum (during race)
"win_ip_vol"           # ❌ In-play volume (during race)
"win_lose"             # ❌ Win/loss outcome (after race!)
"place_bsp"            # ❌ Place BSP
"place_ipmax"          # ❌ In-play place prices
"place_ipmin"
"place_ip_vol"
"place_win_lose"       # ❌ Outcome
```

**Why forbidden?**
- These values are determined **during or after** the race
- They don't exist when we need to make predictions
- Using them = overfitting to unavailable information

---

## 💡 **Engineered Market Features**

### 1. Price Movement (Steamer/Drifter)

```python
price_drift_ratio = win_ppwap / win_morningwap

# Ratio < 1.0 = "Steamer" (price shortened)
#   Example: 10.0 → 6.0 (money came for this horse)
# Ratio > 1.0 = "Drifter" (price lengthened)
#   Example: 5.0 → 8.0 (money against this horse)
```

**Why useful?**
- Market movement reflects new information (stable form, track condition, etc.)
- Steamers often win more than their pre-play odds suggest
- Drifters can signal confidence issues

### 2. Volume

```python
volume_traded = win_pre_vol

volume_per_runner = win_pre_vol / field_size
```

**Why useful?**
- High volume = more liquidity = more efficient pricing
- Low volume = might be mispriced
- Can use volume as confidence weight

### 3. Price Volatility

```python
price_spread = win_ppmax - win_ppmin

price_volatility = price_spread / win_ppwap
```

**Why useful?**
- High spread = uncertain, conflicting opinions
- Low spread = market consensus
- Can indicate weak form reading

### 4. Favorite Status

```python
is_morning_fav = (morning_price_rank == 1)
is_fav = (preplay_price_rank == 1)
```

**Why useful?**
- Favorites win ~30-35% of races
- Strong baseline feature
- Can check if favorite status changed (steamer!)

---

## 📊 **Feature Importance: Market vs Form**

### Expected Feature Ranking

**Strong Features (High Importance):**
1. `win_ppwap` or `decimal_odds` - Market's best guess
2. `is_fav` - Favorite indicator
3. `racing_post_rating` - Speed rating
4. `official_rating` - Official handicap mark
5. `price_drift_ratio` - Market movement

**Medium Features:**
6. `trainer_sr_14d` - Recent trainer form
7. `jockey_sr_14d` - Recent jockey form
8. `volume_traded` - Liquidity indicator
9. `days_since_run` - Recency
10. `career_strike_rate` - Long-term form

**Weaker Features:**
- `draw` - Only important at certain courses
- `price_spread` - Noisy signal
- `wins_at_course` - Small sample sizes

---

## 🧪 **Testing for Leakage**

### How to Detect Data Leakage

**Test 1: Feature Availability Check**
```python
# For inference dataset (future races)
df_future = build_inference_data("2025-10-17")

# Check if any features are NULL
null_counts = df_future.null_count()

# If win_bsp, win_ipmax, etc. have values → LEAKAGE!
# They shouldn't exist for future races
```

**Test 2: Too-Good-To-Be-True Performance**
```python
# If your test AUC-ROC > 0.90 → Probably leakage
# Racing is noisy; AUC > 0.70 is excellent

# Check feature importance
# If win_bsp is #1 feature → LEAKAGE (it's just the outcome!)
```

**Test 3: Production Failure**
```python
# Model works great in backtest but fails in production
# → You're using features that don't exist at prediction time
```

---

## 📈 **Expected Model Performance**

### With Pre-Race Market Features

**Realistic Metrics:**
- Train AUC-ROC: 0.68-0.72
- Test AUC-ROC: 0.65-0.70
- Log Loss: 0.45-0.50

**Why not higher?**
- Racing has inherent randomness (luck, accidents, etc.)
- Market is efficient (hard to beat)
- If AUC > 0.75, check for leakage!

### Market vs Non-Market Models

**Without market features:**
- AUC: ~0.62-0.65 (pure form/ratings)

**With market features:**
- AUC: ~0.68-0.72 (market + form)

**With BSP (LEAKAGE):**
- AUC: ~0.90-0.95 (but useless in production!)

---

## 🎯 **Best Practices**

### DO ✅

1. **Use pre-play prices** - Market's informed opinion
2. **Engineer price movements** - Captures information flow
3. **Use volume as confidence** - Weight predictions by liquidity
4. **Combine market + form** - Complementary signals
5. **Validate on OOT test set** - Proves no leakage

### DON'T ❌

1. **Don't use BSP** - Only available at race start
2. **Don't use in-play prices** - Only available during race
3. **Don't use outcomes** - That's what we're predicting!
4. **Don't trust AUC > 0.80** - Probably leakage
5. **Don't skip OOT testing** - Only way to catch leakage

---

## 🔍 **Current Implementation**

### Features Added (All Safe!)

```python
# Market position
"market_rank"          # Rank by odds (1 = favorite)
"decimal_odds"         # Pre-play odds
"is_fav"              # Is favorite?
"is_morning_fav"      # Was morning favorite?

# Market dynamics
"price_drift_ratio"   # Morning → pre-play movement
"price_movement"      # Absolute price change
"price_spread"        # Price volatility

# Liquidity
"volume_traded"       # Total volume
"volume_per_runner"   # Normalized volume
```

**Total Market Features**: 9  
**Total Features**: 35 (28 form + 9 market - 2 duplicates)

---

## 📝 **Summary**

**Q: Should we use Betfair data?**  
**A:** YES - but only PRE-RACE data

**Q: What about BSP?**  
**A:** NO - it's only available at race start (leakage!)

**Q: What about in-play prices?**  
**A:** NO - they're only available during the race (leakage!)

**Q: What's safe to use?**  
**A:** Morning prices, pre-play prices, volumes, price movements

**Q: How do I know if I have leakage?**  
**A:** Test AUC > 0.80, or model fails in production

---

**Bottom Line:** Market data is powerful, but use it carefully. Only pre-race data is safe!

🎯 **Your model now includes 9 market features that are all leakage-free and available at prediction time.**

