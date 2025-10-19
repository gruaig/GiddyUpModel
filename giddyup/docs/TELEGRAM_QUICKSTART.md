# Telegram Integration - Quick Start

## 🚀 3-Step Setup

### 1️⃣ Get Your Chat ID

Visit this URL to get your chat ID:
```
https://api.telegram.org/bot8419851120:AAHTWE5k67fR7_wuyS5Lv9JFjKJ30ODClHI/getUpdates
```

Look for `"chat":{"id":YOUR_NUMBER_HERE}`

### 2️⃣ Update Config

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
nano telegram_config.py
```

Change:
```python
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
```

To your actual chat ID (e.g., `"123456789"`)

### 3️⃣ Test It

```bash
python3 telegram_bot.py
```

Should see: `✅ Telegram test message sent successfully!`

---

## ✅ Done!

Now when you run the bot:
```bash
python3 HorseBot_Simple.py start 2025-10-18 5000
```

You'll get Telegram notifications for:
- 🏇 Morning picks
- 🎯 Bets placed
- ⏭️ Bets skipped
- 📊 Market analysis
- 🎉 Results

---

## 📱 Example Messages

**Morning:**
```
🏇 GiddyUp Betting Card - 2025-10-18

📊 Daily Selections
━━━━━━━━━━━━━━━━━━━━━━

🎯 Total Selections: 8
💰 Total Stake: £150.00
```

**Bet Placed:**
```
🎯 BET PLACED 🟡 DRY RUN

🏇 Woodhay Whisper (IRE)
📍 Kempton
⏰ Race: 18:27

💰 Stake: £20.00
📊 Odds: 13.50
```

**Bet Skipped:**
```
⏭️ BET SKIPPED

🏇 Cayman Dancer (GB)
⏰ Race: 20:30

⚠️ Reason: Odds too low: 6.40 < 6.65
```

---

## 🔧 Disable Notifications

Edit `telegram_config.py`:
```python
SEND_BET_SKIPPED = False  # Stop skip notifications
```

---

## 📚 Full Guide

See `TELEGRAM_SETUP_GUIDE.md` for complete documentation.

---

**Ready? Test it now:** `python3 telegram_bot.py` 🚀

