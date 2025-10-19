# 🤖 GiddyUp HorseBot - Twitter Integration Setup

## 🚀 New Bot Commands

### Start Bot
```bash
python3 HorseBot_Simple.py start 2025-10-18 5000
python3 HorseBot_Simple.py start 2025-10-18 5000 --live  # Real bets
```

### Stop Bot
```bash
python3 HorseBot_Simple.py stop
```

### Check Status
```bash
python3 HorseBot_Simple.py status
```

---

## 🐦 Twitter Integration Setup

### 1. Get Twitter API Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app or use existing one
3. Get these credentials:
   - API Key
   - API Secret Key
   - Access Token
   - Access Token Secret

### 2. Set Environment Variables

```bash
export TWITTER_API_KEY="your_api_key_here"
export TWITTER_API_SECRET="your_api_secret_here"
export TWITTER_ACCESS_TOKEN="your_access_token_here"
export TWITTER_ACCESS_SECRET="your_access_secret_here"
```

### 3. Test Twitter Script

```bash
# Daily summary tweet
./publish_results.sh 2025-10-18 summary

# Bet placed tweet (called by bot)
./publish_results.sh 2025-10-18 bet_placed "Arctic Fox" "Catterick" "8.80" "0.75" "A-Hybrid_V3"

# Bet result tweet (called manually)
./publish_results.sh 2025-10-18 bet_result "Arctic Fox" "Catterick" "WIN" "5.85"
```

---

## 📊 Tweet Templates

### Daily Summary
```
📊 2025-10-18 Summary

🎯 Total Selections: 45
💰 Total Staked: £67.50
✅ Bets Placed: 12
⏭️ Skipped: 33

#HorseRacing #Betting #Automation
```

### Bet Placed
```
🎯 New Bet Placed

🏇 Arctic Fox (GB) @ Catterick
💰 £0.75 @ 8.80
📈 Strategy: A-Hybrid_V3

#HorseRacing #Betting #Catterick #ArcticFox
```

### Bet Result
```
🎉 Bet Result

🏇 Arctic Fox (GB) @ Catterick
📊 Result: WIN
💰 P&L: £5.85

#HorseRacing #Betting #Catterick #ArcticFox
```

---

## 🔄 Workflow Integration

### Morning Routine
1. **Start Bot**: `python3 HorseBot_Simple.py start 2025-10-18 5000`
2. **Post Summary**: `./publish_results.sh 2025-10-18 summary`

### During Trading
- Bot automatically posts when bets are placed
- Bot logs all activity to CSV files

### Evening Routine
1. **Check Status**: `python3 HorseBot_Simple.py status`
2. **Stop Bot**: `python3 HorseBot_Simple.py stop`
3. **Post Final Summary**: `./publish_results.sh 2025-10-18 summary`

---

## 📁 File Structure

```
giddyup/
├── HorseBot_Simple.py          # Main bot with start/stop/status
├── publish_results.sh          # Twitter posting script
├── horsebot.pid               # PID file (auto-created)
└── strategies/logs/automated_bets/
    ├── bot_actions_2025-10-18.csv
    ├── bot_prices_2025-10-18.csv
    └── betting_report_2025-10-18.xlsx
```

---

## ⚙️ Configuration

### Bot Settings (in HorseBot_Simple.py)
```python
T_MINUS_START_TRACKING = 240  # Start tracking 4 hours before race
T_MINUS_BET_WINDOW = 60       # Make betting decision at T-60
RECHECK_INTERVAL = 300        # Re-check every 5 minutes
MIN_LIQUIDITY = 1000          # Min £ matched
MAX_DRIFT = 0.15              # Max 15% price drift
```

### Twitter Settings (in publish_results.sh)
- Generic tweet templates
- **Automatic hashtag inclusion** with course and horse tags
- **Smart normalization**: "Arctic Fox (GB)" → "#ArcticFox"
- **Course hashtags**: "Catterick" → "#Catterick"
- **Daily summary** includes top 3 most active courses
- Character limit compliance
- Error handling for API failures

---

## 🎯 Next Steps

1. **Set up Twitter API credentials**
2. **Test with dry run**: `python3 HorseBot_Simple.py start 2025-10-18 5000`
3. **Monitor tweets**: Check your Twitter account
4. **Go live**: `python3 HorseBot_Simple.py start 2025-10-18 5000 --live`

---

## 🏷️ Hashtag Examples

### Course Hashtags
- **Catterick** → `#Catterick`
- **Ascot** → `#Ascot`
- **Leopardstown** → `#Leopardstown`
- **Newton Abbot** → `#NewtonAbbot`

### Horse Name Hashtags
- **Arctic Fox (GB)** → `#ArcticFox`
- **Eagle Bay (IRE)** → `#EagleBay`
- **Mission Central (IRE)** → `#MissionCentral`
- **Flora Of Bermuda (IRE)** → `#FloraOfBermuda`

### Daily Summary Course Tags
If you bet at multiple courses, the summary includes the top 3 most active:
```
📊 2025-10-18 Summary

🎯 Total Selections: 45
💰 Total Staked: £67.50
✅ Bets Placed: 12
⏭️ Skipped: 33

#HorseRacing #Betting #Automation #Catterick #Ascot #Leopardstown
```

---

## 🔧 Troubleshooting

### Bot won't start
```bash
python3 HorseBot_Simple.py status
# If running: python3 HorseBot_Simple.py stop
```

### Twitter errors
```bash
# Check credentials
echo $TWITTER_API_KEY
# Test script
./publish_results.sh 2025-10-18 summary
```

### Permission errors
```bash
chmod +x publish_results.sh
```

---

## 📈 Benefits

✅ **Automated posting** - No manual tweeting  
✅ **Professional appearance** - Consistent format  
✅ **Real-time updates** - Immediate bet notifications  
✅ **Daily summaries** - Complete performance overview  
✅ **Process control** - Start/stop/status commands  
✅ **Error handling** - Graceful failure management  

**Your betting bot is now a complete social media automation system!** 🎉
