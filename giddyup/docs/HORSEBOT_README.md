# 🤖 GiddyUp HorseBot - Automated Betting System

**Status**: Ready for Paper Trading  
**Strategies**: A (Hybrid V3) + B (Path B)  
**Platform**: Betfair Exchange

---

## 🎯 What It Does

HorseBot automates your daily horse racing betting workflow:

1. **Morning**: You run the bot with today's date and bankroll
2. **Throughout the day**: Bot monitors Betfair markets
3. **At T-60** (60 min before each race): Checks if odds are favorable
4. **Places bet** if conditions are met, or skips if not
5. **Logs everything** to CSV for analysis
6. **Runs until** all races are finished

---

## 📋 Prerequisites

### 1. Betfair Account

- Create account at [Betfair](https://www.betfair.com/)
- Verify your identity
- Fund account (recommended £500+ for testing)

### 2. Betfair API Access

- Go to [Betfair Developer](https://developer.betfair.com/get-started/)
- Create an App Key (free)
- Note down your username, password, and App Key

### 3. Python Dependencies

```bash
pip install betfairlightweight pytz
```

---

## 🔧 Setup

### Step 1: Configure Credentials

```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# Copy the template
cp HorseBot_config.template.py HorseBot_config.py

# Edit with your credentials
nano HorseBot_config.py
```

Fill in:
```python
BETFAIR_USERNAME = "your_betfair_username"
BETFAIR_PASSWORD = "your_betfair_password"
BETFAIR_APP_KEY = "your_app_key_from_developer_portal"
```

### Step 2: Update HorseBot.py to Use Config

Edit the top of `HorseBot.py` to import from config file instead of hardcoded values:

```python
# At the top of HorseBot.py, replace the credentials section with:
try:
    from HorseBot_config import (
        BETFAIR_USERNAME,
        BETFAIR_PASSWORD,
        BETFAIR_APP_KEY,
        T_MINUS_WINDOW,
        RECHECK_INTERVAL,
        MIN_MARKET_LIQUIDITY,
        MAX_PRICE_DRIFT,
    )
except ImportError:
    print("ERROR: HorseBot_config.py not found!")
    print("Copy HorseBot_config.template.py to HorseBot_config.py and add your credentials")
    exit(1)
```

### Step 3: Make Executable

```bash
chmod +x HorseBot.py
```

---

## 🚀 Usage

### Paper Trading (Recommended First!)

Test the bot without placing real bets:

```bash
python HorseBot.py --date 2025-10-18 --bankroll 5000 --paper-trade
```

**Paper trade for 2 weeks** to verify:
- Market finding works
- Odds checking works
- Timing is correct (T-60)
- CSV logging works

### Live Betting

Once confident, remove `--paper-trade` flag:

```bash
python HorseBot.py --date 2025-10-18 --bankroll 5000
```

### Daily Workflow

**Best practice**: Start the bot in the morning and let it run all day.

```bash
# Morning (before first race)
cd /home/smonaghan/GiddyUpModel/giddyup
python HorseBot.py --date $(date +%Y-%m-%d) --bankroll 5000

# Bot will:
# 1. Load today's selections (both strategies)
# 2. Monitor markets throughout the day
# 3. Place bets at T-60 if odds are good
# 4. Keep running until last race finishes
# 5. Print summary at end
```

### Run in Background (tmux)

To let it run while you're away:

```bash
# Start tmux session
tmux new -s horsebot

# Run bot
python HorseBot.py --date $(date +%Y-%m-%d) --bankroll 5000

# Detach: Ctrl+B, then D
# Reattach later: tmux attach -t horsebot
```

---

## 📊 Output

### Console Output

```
[2025-10-18 08:00:00] ℹ️ Fetching selections for 2025-10-18 with £5000 bankroll...
[2025-10-18 08:00:03] ✅ Loaded 53 potential bets
[2025-10-18 08:00:03] ℹ️   1. 09:30 Catterick - Arctic Fox (GB) @ 7.40 (min 7.03) [A-Hybrid_V3] £0.75
[2025-10-18 08:00:03] ℹ️   2. 09:30 Catterick - Wasthatok (GB) @ 9.00 (min 8.10) [B-Path_B] £2.00
...
[2025-10-18 08:30:15] ℹ️ Processing: Arctic Fox (GB) at Catterick
[2025-10-18 08:30:16] ✅ Found market: 1.234567 | Selection: 12345678 | Arctic Fox (GB)
[2025-10-18 08:30:17] 💰 BET PLACED: £0.75 @ 7.40 | Bet ID: 123456789
...
```

### CSV Log

Saved to: `strategies/logs/automated_bets/bot_log_2025-10-18.csv`

```csv
timestamp,race_time,course,horse,strategy,expected_odds,min_odds_needed,actual_odds,stake_gbp,bet_placed,bet_id,reason,matched,result,pnl_gbp
2025-10-18 08:30:17,09:30,Catterick,Arctic Fox (GB),A-Hybrid_V3,7.40,7.03,7.40,0.75,YES,123456789,Conditions met: odds 7.40 >= 7.03,YES,,
2025-10-18 08:30:45,09:30,Catterick,Wasthatok (GB),B-Path_B,9.00,8.10,7.85,2.00,NO,,Odds too low: 7.85 < 8.10,NO,,
```

---

## ⚙️ Configuration Options

Edit `HorseBot_config.py` to customize:

### Timing
```python
T_MINUS_WINDOW = 60    # When to start checking (60 min before)
RECHECK_INTERVAL = 300  # How often to check (5 minutes)
```

### Safety Limits
```python
MIN_MARKET_LIQUIDITY = 1000  # Minimum £ matched
MAX_PRICE_DRIFT = 0.15       # Max 15% odds drift from expected
```

### Strategy Selection
```python
ENABLE_STRATEGY_A = True  # Hybrid V3 (3-4 bets/day)
ENABLE_STRATEGY_B = True  # Path B (0-2 bets/day)
```

---

## 🛡️ Safety Features

### Built-in Protections

1. **Paper Trade Mode**: Test without real money
2. **Odds Validation**: Won't bet if odds moved too much
3. **Liquidity Check**: Ensures market is active (£1000+ matched)
4. **Time Windows**: Only bets T-60 to T-5 (won't bet in-play)
5. **CSV Logging**: Every action tracked
6. **Market Verification**: Matches horse name + course before betting

### Manual Override

**STOP THE BOT ANYTIME**: Just Ctrl+C

The bot will:
- Logout from Betfair gracefully
- Save all logs
- Show summary of actions taken so far

---

## 📈 Expected Performance

Based on backtests (2024-2025):

### Strategy A (Hybrid V3)
- **Bets/day**: 3-4
- **ROI**: +3.1%
- **Win Rate**: 11-12%
- **Monthly profit** (£5k bankroll): +£1.55

### Strategy B (Path B)
- **Bets/day**: 0-2
- **ROI**: +65.1% (needs validation!)
- **Win Rate**: 18.1%
- **Monthly profit** (£5k bankroll): +£39

### Combined (Both Strategies)
- **Bets/day**: 3-6
- **Estimated monthly**: +£40
- **Estimated annual**: +£486

⚠️ **Past performance doesn't guarantee future results!**

---

## 🐛 Troubleshooting

### "No selections found"
- Check database has tomorrow's odds: `./strategies/CHECK_DATA_READY.sh`
- Ensure Docker container is running: `docker ps | grep horse_racing`
- Verify date format: YYYY-MM-DD

### "Could not find market on Betfair"
- UK/Irish racing only
- Check course name matches Betfair's (e.g., "Catterick" not "Catterick Bridge")
- Market must be live (published by Betfair ~24h before)

### "Bet placement failed"
- Check account balance
- Verify API key is correct
- Ensure account has betting permissions
- Check Betfair status: [status.betfair.com](https://status.betfair.com/)

### "Odds too low"
- Normal! Odds often drift down for favorites
- Bot correctly skipping bets that don't meet min odds
- Check CSV for details

---

## 📝 Manual Bet Entry (If Bot Fails)

If bot fails but you still want to bet manually, check the CSV:

```bash
cat strategies/logs/daily_bets/betting_log_2025.csv | grep 2025-10-18
```

Then manually place bets on Betfair using the displayed:
- Horse name
- Course
- Minimum odds needed
- Stake amount

---

## 🔐 Security Notes

1. **NEVER commit `HorseBot_config.py`** (contains credentials)
2. **Use app-specific passwords** for email (if enabled)
3. **Store backups securely** (encrypted drives)
4. **Limit API key permissions** (betting only, not account changes)
5. **Monitor logs** for suspicious activity

---

## 🚦 Development Roadmap

### ✅ Phase 1: Core Bot (Complete)
- [x] Load selections from strategies
- [x] Find Betfair markets
- [x] Check odds at T-60
- [x] Place bets automatically
- [x] CSV logging

### 🔄 Phase 2: Enhanced Monitoring (In Progress)
- [ ] Real-time notifications (Slack/Discord)
- [ ] Bet matched verification
- [ ] Live P&L tracking
- [ ] Multi-day scheduling

### 🔮 Phase 3: Advanced Features (Future)
- [ ] Adaptive stake sizing (Kelly Criterion)
- [ ] Market sentiment analysis
- [ ] Hedge bet recommendations
- [ ] Mobile app interface

---

## 📞 Support

**Issues**:
1. Check logs: `strategies/logs/automated_bets/bot_log_*.csv`
2. Review console output
3. Test in `--paper-trade` mode first

**Questions about strategies**:
- Strategy A: See `strategies/strategy_a_hybrid_v3/STRATEGY_A_README.md`
- Strategy B: See `strategies/strategy_b_high_roi/STRATEGY_B_README.md`

---

## ⚖️ Legal Disclaimer

This software is for **personal use only**.

- You are responsible for compliance with local gambling laws
- Betting involves risk of loss
- Past performance does not guarantee future results
- The developers assume no liability for losses incurred
- Always bet responsibly

---

**Happy Betting! 🏇💰**

*GiddyUp HorseBot v1.0 - October 2025*


