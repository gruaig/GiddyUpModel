# Complete Daily Workflow

## 🌅 Morning → 🏇 Racing Day → 🌙 Evening

Complete end-to-end workflow for automated betting with Telegram notifications.

---

## 📅 Morning (08:00 AM)

### 1. Morning Preparation

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
./morning_prep.sh
```

**This will:**
- ✅ Check if odds data is ready
- ✅ Query database for selections
- ✅ Generate CSV with locked-in bets
- ✅ Create PNG betting card
- ✅ Show summary of today's picks

**Output files:**
- `strategies/logs/daily_bets/betting_log_2025.csv`
- `strategies/logs/daily_bets/betting_card_2025-10-18.png`

---

## 🏇 During Day (08:30 AM - 18:00 PM)

### 2. Start the Bot

**Option A: As a Service (Recommended)**
```bash
sudo systemctl start giddyup-bot
```

**Option B: Manual**
```bash
python3 HorseBot_Simple.py start 2025-10-18 5000
```

### What Happens Automatically

#### T-60 Before Each Race:
1. Bot checks Betfair odds
2. Compares to minimum threshold
3. **Decision:**

**If Odds ≥ Minimum:**
```
✅ CONDITIONS MET
💰 Places bet
📱 Telegram: "🎯 BET PLACED - Horse @ 13.50"
🐦 Creates tweet file
```

**If Odds < Minimum:**
```
⏭️ SKIPPED
📱 Telegram: "⏭️ BET SKIPPED - Odds too low: 6.40 < 6.65"
📊 Logs reasoning
```

### Real-Time Notifications

**Telegram messages you'll receive:**

1. **Morning Picks (08:00)**
   ```
   🏇 GiddyUp Betting Card - 2025-10-18
   
   📊 Daily Selections
   ━━━━━━━━━━━━━━━━━━━━━━
   
   🎯 Total Selections: 8
   💰 Total Stake: £150.00
   
   [Full list of horses...]
   ```

2. **Bet Placed (Throughout Day)**
   ```
   🎯 BET PLACED 🟡 DRY RUN
   
   🏇 Woodhay Whisper (IRE) @ Kempton
   ⏰ Race: 18:27
   💰 £20.00 @ 13.50
   💵 Potential Profit: £250.00
   ```

3. **Bet Skipped (Throughout Day)**
   ```
   ⏭️ BET SKIPPED
   
   🏇 Cayman Dancer (GB) @ Wolverhampton
   ⏰ Race: 20:30
   
   ⚠️ Reason: Odds too low: 6.40 < 6.65
   ```

---

## 🌙 Evening (After All Races)

### 3. End of Day Workflow

```bash
./end_of_day.sh
```

**This is an interactive script that will:**

#### Step 1: Generate Excel Report
```
📊 Generating Excel report...
✅ Report generated: betting_report_2025-10-18.xlsx
```

#### Step 2: Wait for You to Fill in Results
```
📝 Please open the Excel file and fill in the 'Result' column:
   File: strategies/logs/automated_bets/betting_report_2025-10-18.xlsx
   
   For each bet:
   - Column L (Result): Enter 'WIN' or 'LOSS'
   - P&L will auto-calculate

Press ENTER when done...
```

**While you wait, open Excel:**
- Open `betting_report_2025-10-18.xlsx`
- Go to "Betting Log" sheet
- Fill in column L (Result) with WIN or LOSS
- P&L auto-calculates with 2% commission
- Save and close

#### Step 3: Generate Result Tweets
```
🐦 Generating tweet files for results...
✅ Generated:
   1827_Kempton_WoodhayWhisper_result.tweet (WIN)
   1856_Wolverhampton_LooksFantastic_result.tweet (LOSS)
```

#### Step 4: Send to Telegram
```
📱 Telegram is configured
   Send results to Telegram? (y/n): y
   
Sending results...
🎉 Woodhay Whisper - WIN - P&L: +£244.60
😔 Looks Fantastic - LOSS - P&L: £-7.50

✅ Sent 2 result(s) to Telegram
```

**Telegram will receive:**
```
🎉 BET WON

🏇 Woodhay Whisper (IRE) @ Kempton
⏰ Race: 18:27
📊 Result: WON
💰 P&L: +£244.60

━━━━━━━━━━━━━━━━━━━━━━

📊 DAILY SUMMARY - 2025-10-18

🎯 Bets: 8
🏆 Wins: 3
😔 Losses: 5
💰 P&L: +£450.00
📈 ROI: +15.2%
```

#### Step 5: Post to Social Media (Optional)
```
📱 Tweet files are ready in: strategies/logs/tweets/
   
View tweet files now? (y/n): y

📋 Available tweet files:
   1827_Kempton_WoodhayWhisper_result.tweet
   1856_Wolverhampton_LooksFantastic_result.tweet
```

#### Final Summary
```
===============================================================================
✅ END OF DAY WORKFLOW COMPLETE
===============================================================================

📊 Summary for 2025-10-18:
   Total Bets: 8
   Wins: 3 | Losses: 5 | Pending: 0
   Total Staked: £150.00
   Total P&L: +£450.00
   ROI: +15.2%
   Win Rate: 37.5%
```

---

## 📊 Complete File Structure

### Morning Output
```
strategies/logs/daily_bets/
├── betting_log_2025.csv          ← All selections (master file)
└── betting_card_2025-10-18.png   ← Visual betting card
```

### During Day Output
```
strategies/logs/automated_bets/
├── bot_actions_2025-10-18.csv    ← Bet execution log
├── bot_prices_2025-10-18.csv     ← Price tracking log
└── bot_log_2025-10-18.csv        ← Bot activity log

strategies/logs/tweets/
├── 1827_Kempton_WoodhayWhisper.tweet      ← Bet placed
├── 1856_Wolverhampton_LooksFantastic.tweet ← Bet placed
└── 2000_Wolverhampton_Maldevious.tweet     ← Bet placed
```

### Evening Output
```
strategies/logs/automated_bets/
└── betting_report_2025-10-18.xlsx   ← Excel report with P&L

strategies/logs/tweets/
├── 1827_Kempton_WoodhayWhisper_result.tweet      ← Result
├── 1856_Wolverhampton_LooksFantastic_result.tweet ← Result
└── 2000_Wolverhampton_Maldevious_result.tweet     ← Result
```

---

## 🎯 Quick Commands Reference

| Time | Command | What It Does |
|------|---------|--------------|
| **Morning** | `./morning_prep.sh` | Generate selections |
| **Start Bot** | `sudo systemctl start giddyup-bot` | Start automated betting |
| **Monitor** | `tail -f logs/bot_service.log` | Watch bot activity |
| **Evening** | `./end_of_day.sh` | Complete end-of-day workflow |
| **View Tweets** | `./tweet_manager.sh list` | List all tweet files |
| **Post Tweet** | `./tweet_manager.sh post <file>` | Copy tweet to post |

---

## 🔄 Alternative: Manual Workflow

If you prefer manual control:

### Morning
```bash
# 1. Generate selections
./morning_prep.sh

# 2. Review PNG betting card
xdg-open strategies/logs/daily_bets/betting_card_2025-10-18.png
```

### During Day
```bash
# 3. Run bot manually (stays in foreground)
python3 HorseBot_Simple.py start 2025-10-18 5000
```

### Evening
```bash
# 4. Generate Excel report
python3 generate_betting_report.py 2025-10-18

# 5. Fill in results in Excel

# 6. Generate result tweets
python3 generate_result_tweets.py 2025-10-18

# 7. View and post tweets manually
./tweet_manager.sh list
./tweet_manager.sh post 1827_Kempton_WoodhayWhisper_result.tweet
```

---

## 📱 Telegram Timeline Example

### Morning (08:00)
```
🏇 GiddyUp Betting Card - 2025-10-18
📊 8 selections, £150 total stake
```

### During Day (09:00-18:00)
```
09:27 ⏭️ BET SKIPPED - Odds too low
10:15 🎯 BET PLACED - Horse @ 9.50
11:30 🎯 BET PLACED - Horse @ 13.50
12:45 ⏭️ BET SKIPPED - Drifted too far
14:00 🎯 BET PLACED - Horse @ 8.80
[... more throughout the day ...]
```

### Evening (20:00)
```
🎉 BET WON - P&L: +£244.60
😔 BET LOST - P&L: £-7.50
🎉 BET WON - P&L: +£176.40
[... all results ...]

📊 DAILY SUMMARY
Wins: 3 | Losses: 5
P&L: +£450.00 | ROI: +15.2%
```

---

## ✅ Daily Checklist

### Morning
- [ ] Run `./morning_prep.sh`
- [ ] Review PNG betting card
- [ ] Check Telegram received morning picks
- [ ] Start bot (service or manual)

### During Day
- [ ] Monitor Telegram for bet notifications
- [ ] Check bot logs occasionally
- [ ] Bot handles everything automatically

### Evening
- [ ] Wait for all races to finish
- [ ] Run `./end_of_day.sh`
- [ ] Fill in WIN/LOSS in Excel
- [ ] Review Telegram results
- [ ] Post tweets if desired

### Maintenance
- [ ] Archive old tweets weekly
- [ ] Review Excel reports
- [ ] Check bot logs for errors

---

## 🐛 Troubleshooting

### Bot not placing bets?
```bash
# Check if running
sudo systemctl status giddyup-bot

# Check logs
tail -f logs/bot_service.log

# Verify selections exist
cat strategies/logs/daily_bets/betting_log_2025.csv | grep $(date +%Y-%m-%d)
```

### Telegram not working?
```bash
# Test connection
python3 telegram_bot.py

# Check config
python3 -c "from telegram_config import *; print(TELEGRAM_CHAT_ID)"
```

### Excel report errors?
```bash
# Check bot actions file exists
ls -lh strategies/logs/automated_bets/bot_actions_*.csv

# Regenerate
python3 generate_betting_report.py 2025-10-18
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `COMPLETE_DAILY_WORKFLOW.md` | This file - complete guide |
| `QUICK_START_SERVICE.md` | Quick daily reference |
| `SERVICE_SETUP_GUIDE.md` | Bot service installation |
| `TELEGRAM_QUICKSTART.md` | Telegram setup |
| `TWEET_WORKFLOW.md` | Tweet generation guide |
| `BETTING_MEDIA_GUIDE.md` | PNG & tweet guide |

---

## 🎉 Summary

**One-line Daily Workflow:**
```bash
# Morning: Generate picks
./morning_prep.sh && sudo systemctl start giddyup-bot

# Evening: Process results
./end_of_day.sh
```

That's it! The bot handles everything else automatically with real-time Telegram notifications! 🏇💰📱

