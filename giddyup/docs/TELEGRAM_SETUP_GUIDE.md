# Telegram Integration Setup Guide

## 🎯 Overview

Your GiddyUp bot now sends real-time notifications to Telegram:
- 🏇 Morning picks summary
- 🎯 Bets placed (with full details)
- ⏭️ Bets skipped (with reasoning)
- 📊 Market analysis
- 🎉 Results

## 📱 Setup Steps

### Step 1: Get Your Chat ID

You already have the bot token. Now you need the chat ID:

**Option A: Direct Message (Private Chat)**
1. Search for your bot on Telegram: `@YourBotName`
2. Send it a message: `/start`
3. Visit this URL in your browser:
   ```
   https://api.telegram.org/bot8419851120:AAHTWE5k67fR7_wuyS5Lv9JFjKJ30ODClHI/getUpdates
   ```
4. Look for `"chat":{"id":YOUR_NUMBER_HERE}`
5. Copy that number (e.g., `123456789`)

**Option B: Group Chat (Recommended)**
1. Create a new Telegram group
2. Add your bot to the group
3. Send a message in the group: `Hello bot!`
4. Visit the same URL above
5. Look for `"chat":{"id":-YOUR_NUMBER_HERE}` (negative for groups)
6. Copy that number (e.g., `-987654321`)

### Step 2: Update Configuration

Edit `telegram_config.py`:
```bash
cd /home/smonaghan/GiddyUpModel/giddyup
nano telegram_config.py
```

Change this line:
```python
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"  # ← UPDATE THIS!
```

To your actual chat ID:
```python
TELEGRAM_CHAT_ID = "123456789"  # or "-987654321" for groups
```

Save and exit (Ctrl+X, Y, Enter).

### Step 3: Test Connection

```bash
python3 telegram_bot.py
```

You should see:
```
✅ Telegram test message sent successfully!
```

And receive a message in Telegram:
```
🤖 GiddyUp Bot Connected!

✅ Telegram integration is working!

You'll receive notifications for:
🏇 Morning picks
🎯 Bets placed
⏭️ Bets skipped
📊 Market analysis
🎉 Results

#GiddyUp #HorseRacing
```

If you get an error:
- Check your chat ID is correct
- Make sure bot token is correct
- Verify you've messaged the bot or added it to the group

---

## 📋 Message Types

### 1. Morning Picks (When bot starts)
```
🏇 GiddyUp Betting Card - 2025-10-18

📊 Daily Selections
━━━━━━━━━━━━━━━━━━━━━━

🎯 Total Selections: 8
💰 Total Stake: £150.00

Today's Bets:

🟢 18:27 Kempton
   🏇 Woodhay Whisper (IRE)
   💰 £20.00 @ 13.50
   📊 Min: 12.15

━━━━━━━━━━━━━━━━━━━━━━
🎯 Bets placed at T-60 if odds ≥ minimum

#HorseRacing #Betting #GiddyUp
```

### 2. Bet Placed
```
🎯 BET PLACED 🟡 DRY RUN

🔵 B-Path_B

🏇 Woodhay Whisper (IRE)
📍 Kempton
⏰ Race: 18:27

💰 Stake: £20.00
📊 Odds: 13.50 (expected 14.00)
💵 Potential Return: £270.00
✨ Potential Profit: £250.00

#HorseRacing #Betting #BetPlaced
```

### 3. Bet Skipped
```
⏭️ BET SKIPPED

🔵 B-Path_B

🏇 Cayman Dancer (GB)
📍 Wolverhampton
⏰ Race: 20:30

📊 Odds Analysis:
   Expected: 7.00
   Current: 6.40
   Minimum: 6.65

⚠️ Reason: Odds too low: 6.40 < 6.65

#HorseRacing #Betting #Skipped
```

### 4. Result (After race)
```
🎉 BET WON

🔵 B-Path_B

🏇 Woodhay Whisper (IRE)
📍 Kempton
⏰ Race: 18:27

📊 Result: WON
💰 Stake: £20.00 @ 13.50
💵 P&L: +£244.60

#HorseRacing #BetResult
```

---

## ⚙️ Configuration Options

Edit `telegram_config.py` to enable/disable message types:

```python
# Enable/disable different message types
SEND_MORNING_PICKS = True      # Morning summary of all bets
SEND_BET_PLACED = True          # When bot places a bet
SEND_BET_SKIPPED = True         # When bet is skipped
SEND_MARKET_ANALYSIS = True     # Market odds analysis
SEND_RESULTS = True             # Win/loss results
```

Set to `False` to disable specific notifications.

---

## 🤖 Bot Commands (Optional)

You can add these commands to your bot via @BotFather:

```
/start - Start receiving notifications
/help - Show help message
/today - Show today's picks
/status - Bot status
```

(Implementation optional - bot works without commands)

---

## 🔒 Security

Your `telegram_config.py` is already protected:
- ✅ File permissions set to 600 (owner only)
- ✅ Added to `.gitignore` (won't be committed)
- ✅ Template file provided for safety

**Never share:**
- Your bot token
- Your chat ID
- The `telegram_config.py` file

---

## 🧪 Testing

### Test Individual Functions

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
python3 << 'EOF'
from telegram_bot import *

# Test bet placed
send_bet_placed(
    horse="Test Horse",
    course="Test Course",
    race_time="14:30",
    odds=10.0,
    stake=20.0,
    strategy="A-Hybrid_V3",
    expected_odds=9.5,
    is_dry_run=True
)

print("✅ Test message sent!")
EOF
```

### Test with Bot

Run the bot and check Telegram:
```bash
python3 HorseBot_Simple.py start 2025-10-18 5000
```

You should receive:
1. Morning picks when bot starts
2. Bet placed/skipped messages during the day

---

## 🐛 Troubleshooting

### No messages received?

1. **Check config file exists:**
   ```bash
   ls -la telegram_config.py
   ```

2. **Verify credentials:**
   ```bash
   python3 -c "from telegram_config import *; print(f'Token: {TELEGRAM_BOT_TOKEN[:20]}...'); print(f'Chat ID: {TELEGRAM_CHAT_ID}')"
   ```

3. **Test connection:**
   ```bash
   python3 telegram_bot.py
   ```

4. **Check bot logs:**
   ```bash
   tail -f logs/bot_service.log | grep -i telegram
   ```

### Bot token invalid?

- Make sure you copied the full token from @BotFather
- Token should look like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
- No spaces or extra characters

### Chat ID wrong?

- Make sure you got the chat ID from `/getUpdates`
- Group chat IDs are negative (e.g., `-987654321`)
- Private chat IDs are positive (e.g., `123456789`)

### Messages delayed?

- Telegram API can have delays (usually < 1 second)
- Check your internet connection
- Verify bot isn't rate-limited (max 30 msgs/second)

---

## 📊 Example Session

```
08:00 - Morning prep runs
📱 Telegram: "🏇 GiddyUp Betting Card - 8 selections"

09:27 - T-60 for first race, odds check
📱 Telegram: "⏭️ BET SKIPPED - Odds too low"

10:15 - T-60 for second race, criteria met
📱 Telegram: "🎯 BET PLACED - Horse @ 9.50"

14:30 - Race finishes, horse wins!
📱 Telegram: "🎉 BET WON - P&L: +£176.40"

20:00 - All races finished
📱 Telegram: "📊 DAILY SUMMARY - 8 bets, +£450.00"
```

---

## 🎯 Tips

1. **Use a group** - Easier to track history
2. **Pin important messages** - Morning picks, summary
3. **Mute if needed** - Can be chatty during racing days
4. **Screenshots** - Great for social proof
5. **Forward to friends** - Share the action!

---

## 🔗 Useful Links

- Get updates: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
- Bot father: `https://t.me/BotFather`
- Telegram API docs: `https://core.telegram.org/bots/api`

---

## ✅ Quick Checklist

- [ ] Got bot token from @BotFather
- [ ] Got chat ID from `/getUpdates`
- [ ] Updated `telegram_config.py`
- [ ] Ran `python3 telegram_bot.py` successfully
- [ ] Received test message in Telegram
- [ ] Configured message type preferences
- [ ] Ready to run bot!

---

Enjoy your real-time betting notifications! 🏇💰📱

