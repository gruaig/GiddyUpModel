# Betting Media Generation Guide

## Overview

The GiddyUp bot now automatically generates visual content for betting activities:

1. **PNG Betting Card** - Visual summary of all day's bets (generated when strategies run)
2. **Tweet Files** - Individual tweet files for each bet placed (generated when bot places bets)

## 📊 PNG Betting Card

### When It's Generated
Automatically created when you run `RUN_BOTH_STRATEGIES.sh`

### Location
```
strategies/logs/daily_bets/betting_card_YYYY-MM-DD.png
```

### Manual Generation
```bash
cd /home/smonaghan/GiddyUpModel/giddyup
python3 generate_betting_card.py 2025-10-18
```

### Features
- Dark, modern design
- Shows all bets for the day
- Color-coded by strategy (Green=A, Blue=B)
- Displays: time, course, horse, odds, stake, min odds, reasoning
- Total stake summary
- Ready for social media sharing or printing

### Requirements
```bash
pip3 install pillow
```

## 🐦 Tweet Files

### When They're Generated
Automatically created when `HorseBot.py` places a bet (both dry-run and live mode)

### Location
```
strategies/logs/tweets/<time>_<course>_<horse>.tweet
```

### Example
```
strategies/logs/tweets/1827_Kempton_WoodhayWhisper.tweet
```

### Console Output
When a bet is placed, you'll see:
```
[2025-10-18 18:27:24] 💰 PLACING BET: Woodhay Whisper (IRE) @ 13.50 for £20.00
[2025-10-18 18:27:24] ℹ️    Return: £270.00 | Profit: £250.00
[2025-10-18 18:27:24] ⚠️    DRY RUN - Not actually placed (ID: DRY_1760808444)
[2025-10-18 18:27:24] ℹ️ 📝 Tweet saved → 1827_Kempton_WoodhayWhisper.tweet
[2025-10-18 18:27:24] ℹ️    #HorseRacing #Betting #Kempton #WoodhayWhisper
```

### Tweet Content Format
```
🎯 New Bet Placed

🏇 Woodhay Whisper (IRE) @ Kempton
⏰ Race: 18:27
💰 £20.00 @ 13.50
📈 Strategy: B-Path_B

#HorseRacing #Betting #Kempton #WoodhayWhisper
```

## 🎉 Result Tweets

After races finish and you've updated results, generate result tweets to share wins/losses.

### Generate Result Tweets

```bash
# After updating results in Excel or CSV, run:
python3 generate_result_tweets.py 2025-10-18
```

**This will:**
1. Read bot actions CSV
2. Find bets with results filled in (WIN/LOSS)
3. Calculate P&L automatically
4. Generate result tweet files

### Result Tweet Format

**Win Example:**
```
🎉 Bet Result

🏇 Woodhay Whisper (IRE) @ Kempton
⏰ Race: 18:27
📊 Result: WON
💰 P&L: +£244.60

#HorseRacing #Betting #Kempton #WoodhayWhisper
```

**Loss Example:**
```
😔 Bet Result

🏇 Looks Fantastic (GB) @ Wolverhampton
⏰ Race: 18:56
📊 Result: Lost
💰 P&L: £-7.50

#HorseRacing #Betting #Wolverhampton #LooksFantastic
```

### P&L Calculation

- **Win:** (Odds × Stake) - Stake - (2% Commission) = Net Profit
- **Loss:** -Stake

Example win:
- Stake: £20.00 @ 13.50
- Gross return: £270.00
- Commission (2%): £5.40
- Net profit: +£244.60

### Workflow

1. **Races finish** - Wait for results
2. **Update Excel report** - Fill in WIN/LOSS in Result column
3. **Generate result tweets** - Run `generate_result_tweets.py`
4. **Post to social media** - Share the results!

## 📁 Managing Tweet Files

### List All Tweets
```bash
./tweet_manager.sh list
```

### View a Tweet
```bash
./tweet_manager.sh show 1827_Kempton_WoodhayWhisper.tweet
```

### Post a Tweet (copy to clipboard)
```bash
./tweet_manager.sh post 1827_Kempton_WoodhayWhisper.tweet
```

### Archive Posted Tweets
```bash
./tweet_manager.sh archive 1827_Kempton_WoodhayWhisper.tweet
```

### Clean Up Old Tweets
```bash
./tweet_manager.sh clean  # Removes tweets older than 7 days
```

## 🔄 Complete Workflow

### Morning - Get Day's Bets
```bash
cd strategies
./RUN_BOTH_STRATEGIES.sh 2025-10-18 5000
```
**Output:**
- ✅ CSV: `logs/daily_bets/betting_log_2025.csv`
- ✅ PNG: `logs/daily_bets/betting_card_2025-10-18.png`

### During the Day - Run Bot
```bash
python3 HorseBot.py --date 2025-10-18 --bankroll 5000 --dry-run
```
**Output:**
- ✅ Tweet files created for each bet placed in `strategies/logs/tweets/`
- ✅ Bot log: `strategies/logs/automated_bets/bot_log_2025-10-18.csv`

### Evening - Generate Report
```bash
python3 generate_betting_report.py 2025-10-18
```
**Output:**
- ✅ Excel: `strategies/logs/automated_bets/betting_report_2025-10-18.xlsx`

## 🐛 Troubleshooting

### Tweet files not being created?

1. **Clear Python cache:**
   ```bash
   cd /home/smonaghan/GiddyUpModel/giddyup
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} +
   ```

2. **Check directory exists:**
   ```bash
   ls -la strategies/logs/tweets/
   ```

3. **Run bot with verbose output** - look for:
   - `📝 Tweet saved → <filename>`
   - `⚠️  Could not generate tweet file: <error>` (if there's an error)

### PNG not being generated?

1. **Check Pillow is installed:**
   ```bash
   pip3 list | grep -i pillow
   ```

2. **Install if missing:**
   ```bash
   pip3 install pillow
   ```

3. **Test manually:**
   ```bash
   python3 generate_betting_card.py 2025-10-18
   ```

## 📸 Viewing PNG Files

### Linux
```bash
xdg-open strategies/logs/daily_bets/betting_card_2025-10-18.png
```

### Or copy to your local machine
```bash
# On your local machine:
scp user@server:/home/smonaghan/GiddyUpModel/giddyup/strategies/logs/daily_bets/betting_card_2025-10-18.png ~/Downloads/
```

## 📝 File Naming Conventions

### Betting Card PNG
- Format: `betting_card_YYYY-MM-DD.png`
- Example: `betting_card_2025-10-18.png`

### Tweet Files
- Format: `HHMM_CourseName_HorseName.tweet`
- Example: `1827_Kempton_WoodhayWhisper.tweet`
- Note: Country codes (IRE, GB, FR, USA) are removed from horse names

### Summary Tweets
- Format: `YYYY-MM-DD_summary.tweet`
- Example: `2025-10-18_summary.tweet`

## ✅ Dependencies

All dependencies are in `horsebot_requirements.txt`:
```
betfairlightweight>=2.18.0
pytz>=2023.3
requests>=2.31.0
openpyxl>=3.1.0   # For Excel reports
pillow>=10.0.0    # For PNG generation
```

Install all:
```bash
pip3 install -r horsebot_requirements.txt
```

