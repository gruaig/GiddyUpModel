# 🏇 Horse Back-Lay Trading Bot

## 💰 What Is This?

A **trading bot** that exploits price movements in horse racing markets. Instead of traditional betting, it:

1. **Records morning expected prices** (your model selections)
2. **Monitors live price movements** throughout the day
3. **Lays (cashes out) when profitable** - typically when odds shorten

This is **market trading**, not gambling - you're taking advantage of price fluctuations!

---

## 🎯 Strategy

### Morning (9-11 AM):
- Bot records all your model selections with expected odds
- Example: Horse A expected at 10.0, stake £10

### Throughout Day:
- Monitors live Betfair odds every 5 seconds
- Looks for price shortening (odds dropping)

### Lay Triggers:
Bot will lay (cash out) when ANY of these conditions are met:

1. **Price Drops 10%+ Below Morning Price**
   - Morning: 10.0 → Current: 9.0 or less
   - Reason: "Price shortened 10.0%"

2. **T-15 Before Race (if any profit available)**
   - Close to race time with profitable position
   - Reason: "T-15 cash out"

3. **Large Profit Available (20%+)**
   - Significant price movement
   - Reason: "Large profit available 20%+"

---

## 📊 Example Trade

```
Morning Selection:
  Horse: Tommie Beau (IRE)
  Expected: 10.00
  Stake: £20.00

🔍 Monitoring begins...

T-46 Current price: 8.50
  → Price shortened 15%!
  → LAY NOW!

Trade Executed:
  Back: £20.00 @ 10.00
  Lay: £23.53 @ 8.50
  
  Profit: £3.53 (17.6% ROI)
  
Result: £3.53 profit regardless of race outcome! ✅
```

---

## 🚀 How To Run

### Basic (Paper Trading - Recommended First):
```bash
cd /home/smonaghan/GiddyUpModel/giddyup
python3 HorseBackLayBot.py start 2025-10-19 5000
```

### Live Trading (Real Money):
```bash
python3 HorseBackLayBot.py start 2025-10-19 5000 --live
```

### Stop:
Press `Ctrl+C`

---

## 📁 Output Files

### Daily Trade Log:
`strategies/logs/backlay_trades/2025-10-19_backlay.csv`

Columns:
- timestamp: When trade closed
- race_time: Race time
- course: Course name
- horse: Horse name
- strategy: Model strategy
- back_odds: Odds backed at (morning)
- back_stake: Stake used
- lay_odds: Odds laid at
- lay_stake: Lay stake calculated
- profit_gbp: Profit in £
- profit_pct: Profit %
- reason: Why we laid
- status: COMPLETED

---

## 💡 Key Differences vs HorseBot

| Feature | HorseBot | BackLayBot |
|---------|----------|------------|
| **Strategy** | Place bet at T-60 | Trade price movements |
| **Timing** | Single bet per race | Continuous monitoring |
| **Outcome** | Win or lose based on result | Profit locked before race |
| **Risk** | Full stake at risk | Reduced risk (hedged) |
| **Profit Source** | Horse winning | Price shortening |

---

## 🎓 Understanding Back-Lay Trading

### Back (Morning):
```
Back £10 @ 10.0
If wins: Return £100 (profit £90)
If loses: Lose £10
```

### Lay (When Price Drops to 8.0):
```
Lay £12.50 @ 8.0
(Lay stake calculated to match back return)

If wins: Win back bet (£100), lose lay (£87.50) = +£12.50
If loses: Lose back bet (-£10), win lay (+£12.50) = +£2.50

Average profit: ~£7.50 regardless of outcome!
```

This is a **green book** - profit locked in either way!

---

## ⚙️ Configuration

### Adjust Trading Parameters:

Edit `HorseBackLayBot.py`:

```python
# Line ~40-42
MIN_PROFIT_PERCENTAGE = 5.0  # Min 5% profit to close
PRICE_DROP_THRESHOLD = 10.0  # Lay when 10%+ drop
T_MINUS_CASHOUT = 15  # Cash out at T-15
```

**More aggressive:**
```python
PRICE_DROP_THRESHOLD = 5.0  # Lay at 5% drop (more trades)
T_MINUS_CASHOUT = 30  # Cash out earlier
```

**More conservative:**
```python
PRICE_DROP_THRESHOLD = 15.0  # Wait for bigger moves
MIN_PROFIT_PERCENTAGE = 10.0  # Higher profit threshold
```

---

## 📱 Telegram Integration

Bot automatically sends notifications when trades are closed:

```
💰 BACK-LAY PROFIT

🏇 Tommie Beau (IRE) @ Kempton
⏰ Race: 16:05 (T-46)

📊 Trade Details:
Back: £20.00 @ 10.00
Lay: £23.53 @ 8.50

💵 Profit: £3.53 (17.6%)

Reason: Price shortened 15.0%
```

---

## 🎯 Best Practices

### ✅ DO:
- Run in paper trading mode first
- Monitor a few races before going live
- Check morning prices are reasonable
- Review daily logs regularly
- Combine with HorseBot for diversification

### ❌ DON'T:
- Don't expect every trade to trigger
- Don't lay at a loss (bot won't do this anyway)
- Don't trade with money you can't afford
- Don't ignore commission (built into calculations)

---

## 📊 Expected Results

### Typical Day:
- 10 morning selections
- 3-5 trades executed (30-50% hit rate)
- Average profit per trade: £2-10
- Daily P&L: £10-40

### Why Not All Trades?
- Some odds drift (price goes up) - no lay opportunity
- Some odds stay flat - no significant movement
- Some reach T-60 before criteria met (HorseBot takes over)

This is normal! You're only trading when conditions are favorable.

---

## 🔄 Running Both Bots

You can run both HorseBot and BackLayBot simultaneously!

**Terminal 1:**
```bash
python3 HorseBot_Simple.py start 2025-10-19 5000
```

**Terminal 2:**
```bash
python3 HorseBackLayBot.py start 2025-10-19 5000
```

**Result:**
- BackLayBot trades early price movements (T-120 to T-60)
- HorseBot places traditional bets at T-60
- Two different strategies, one selection pool!

---

## 🐛 Troubleshooting

**Q: Bot not finding any trades?**
A: Normal! Market needs to move in your favor. Try lowering PRICE_DROP_THRESHOLD.

**Q: "Market not found" errors?**
A: Betfair may not have market yet. Bot will retry.

**Q: Telegram not working?**
A: Check telegram_config.py is set up correctly.

**Q: Want to see more detail?**
A: Bot logs every check. Watch the console output.

---

## 🎉 Ready To Trade!

This bot can be run independently or alongside HorseBot for a complete trading setup!

Good luck and happy trading! 🏇💰
