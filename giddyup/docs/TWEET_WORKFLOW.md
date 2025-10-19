# Tweet Workflow - Complete Guide

## 📅 Daily Tweet Workflow

### Morning - Pre-Race Tweets

**Option 1: Morning Summary (All Bets)**
```bash
cd /home/smonaghan/GiddyUpModel/giddyup

# Generate daily summary tweet
./generate_tweet_files.sh 2025-10-18 summary
```

Generates: `2025-10-18_summary.tweet`
- Shows all bets for the day
- Total stake
- Number of bets placed

---

### During Day - Bet Placed Tweets

**Automatic:** Bot generates these when placing bets!

When bot places a bet, it automatically creates:
```
1827_Kempton_WoodhayWhisper.tweet
```

**Manual:** If you need to create one manually:
```bash
./generate_tweet_files.sh 2025-10-18 bet_placed 18:27 Kempton "Woodhay Whisper (IRE)" 13.50 20.00 B-Path_B
```

---

### Evening - Result Tweets

**After races finish and results are updated:**

```bash
# 1. Update results in Excel report
python3 generate_betting_report.py 2025-10-18
# Open Excel, fill in WIN/LOSS in Result column

# 2. Generate result tweets
python3 generate_result_tweets.py 2025-10-18
```

This generates result tweets for all bets with results filled in!

---

## 🎯 Tweet Types

### 1. Bet Placed Tweet
**Filename:** `<time>_<course>_<horse>.tweet`

```
🎯 New Bet Placed

🏇 Woodhay Whisper (IRE) @ Kempton
⏰ Race: 18:27
💰 £20.00 @ 13.50
📈 Strategy: B-Path_B

#HorseRacing #Betting #Kempton #WoodhayWhisper
```

### 2. Result Tweet (Win)
**Filename:** `<time>_<course>_<horse>_result.tweet`

```
🎉 Bet Result

🏇 Woodhay Whisper (IRE) @ Kempton
⏰ Race: 18:27
📊 Result: WON
💰 P&L: +£244.60

#HorseRacing #Betting #Kempton #WoodhayWhisper
```

### 3. Result Tweet (Loss)
```
😔 Bet Result

🏇 Looks Fantastic (GB) @ Wolverhampton
⏰ Race: 18:56
📊 Result: Lost
💰 P&L: £-7.50

#HorseRacing #Betting #Wolverhampton #LooksFantastic
```

### 4. Daily Summary Tweet
**Filename:** `<date>_summary.tweet`

```
📊 2025-10-18 Summary

🎯 Total Selections: 56
💰 Total Staked: £450.00
✅ Bets Placed: 8
⏭️ Skipped: 48

#HorseRacing #Betting #Automation #Kempton #Wolverhampton
```

---

## 📋 Complete Daily Example

### 8:00 AM - Morning Prep
```bash
./morning_prep.sh
# Generates: betting_log_2025.csv, betting_card_2025-10-18.png

# Optional: Post summary tweet
./generate_tweet_files.sh 2025-10-18 summary
./tweet_manager.sh post 2025-10-18_summary.tweet
```

### 8:30 AM - Start Bot
```bash
sudo systemctl start giddyup-bot
```

### Throughout Day - Bets Placed
Bot automatically creates:
- `1827_Kempton_WoodhayWhisper.tweet` ✅
- `1856_Wolverhampton_LooksFantastic.tweet` ✅
- `2000_Wolverhampton_Maldevious.tweet` ✅

**Post these as they're created!**

### Evening (20:00) - Races Finish
```bash
# 1. Generate Excel report
python3 generate_betting_report.py 2025-10-18

# 2. Open Excel, fill in results:
#    - Row 1: Woodhay Whisper → WIN
#    - Row 2: Looks Fantastic → LOSS
#    - Row 3: Maldevious → WIN

# 3. Generate result tweets
python3 generate_result_tweets.py 2025-10-18
```

Output:
```
🎉 Woodhay Whisper (IRE) @ 18:27
   Result: WIN | P&L: +£244.60
   Tweet: 1827_Kempton_WoodhayWhisper_result.tweet

😔 Looks Fantastic (GB) @ 18:56
   Result: LOSS | P&L: £-7.50
   Tweet: 1856_Wolverhampton_LooksFantastic_result.tweet

🎉 Maldevious (IRE) @ 20:00
   Result: WIN | P&L: +£176.40
   Tweet: 2000_Wolverhampton_Maldevious_result.tweet
```

**Post the result tweets!**

---

## 🔧 Tweet Manager Commands

### View All Tweets
```bash
./tweet_manager.sh list
```

### Post a Tweet
```bash
./tweet_manager.sh post 1827_Kempton_WoodhayWhisper.tweet
# Copy the output and paste into Twitter
```

### Archive Posted Tweet
```bash
./tweet_manager.sh archive 1827_Kempton_WoodhayWhisper.tweet
```

### Clean Up Old Tweets
```bash
./tweet_manager.sh clean  # Removes tweets older than 7 days
```

---

## 💡 Tips

1. **Post bet placed tweets immediately** - Builds transparency
2. **Wait until all races finish** for result tweets - Post them together
3. **Archive tweets after posting** - Keeps directory clean
4. **Use hashtags** - Help people find your tweets
5. **Include race time** - Helps followers tune in

---

## 🎭 Social Media Strategy

### Build Trust
- Post bet placed tweets BEFORE races
- Post result tweets AFTER races
- Shows you're not cherry-picking wins

### Engagement
- Post morning summary → Gets people interested
- Post individual bets → Builds anticipation
- Post results → Celebrates wins, honest about losses

### Frequency
- Morning: 1 summary tweet
- During day: 1 tweet per bet placed (0-10 tweets)
- Evening: 1 tweet per result (same 0-10 tweets)

Total: ~20 tweets max per day

---

## 📊 Example Thread

**Morning (8:00 AM):**
```
📊 Today's betting card is ready! 
8 selections with positive edge.
Total stake: £150

Let's see how we do! 🏇

#HorseRacing #Betting
```

**Bet Placed (18:27):**
```
🎯 New Bet Placed

🏇 Woodhay Whisper (IRE) @ Kempton
⏰ Race: 18:27
💰 £20.00 @ 13.50
📈 Strategy: B-Path_B

#HorseRacing #Betting #Kempton #WoodhayWhisper
```

**Result (20:30):**
```
🎉 Bet Result

🏇 Woodhay Whisper (IRE) @ Kempton
⏰ Race: 18:27
📊 Result: WON
💰 P&L: +£244.60

Great result! 🎉

#HorseRacing #Betting #Kempton #WoodhayWhisper
```

---

## 🆘 Troubleshooting

**No tweets being generated?**
- Check bot is running: `sudo systemctl status giddyup-bot`
- Check logs: `tail -f logs/bot_service.log`
- Clear Python cache: `find . -name "*.pyc" -delete`

**Result tweets not generating?**
- Make sure you've filled in WIN/LOSS in Excel
- Check CSV has results: `cat strategies/logs/automated_bets/bot_actions_2025-10-18.csv`
- Run manually to see errors: `python3 generate_result_tweets.py 2025-10-18`

**Tweets have wrong info?**
- Check CSV data is correct
- Regenerate: delete tweet file and run script again

---

## ✅ Quick Reference

| Action | Command |
|--------|---------|
| Morning summary | `./generate_tweet_files.sh <date> summary` |
| Manual bet tweet | `./generate_tweet_files.sh <date> bet_placed <time> <course> <horse> <odds> <stake> <strategy>` |
| Result tweets | `python3 generate_result_tweets.py <date>` |
| List tweets | `./tweet_manager.sh list` |
| View tweet | `./tweet_manager.sh show <filename>` |
| Post tweet | `./tweet_manager.sh post <filename>` |
| Archive tweet | `./tweet_manager.sh archive <filename>` |

---

Enjoy sharing your betting journey! 🏇💰

