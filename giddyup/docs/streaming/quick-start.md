# Stream Quickstart - Get Live in 5 Minutes!

## 🎬 3-Step Setup for Twitch Streaming

### 1️⃣ Get OAuth Token
Visit: https://twitchapps.com/tmi/  
Copy the token: `oauth:abcd1234...`

### 2️⃣ Configure
```bash
cp twitch_config.template.py twitch_config.py
nano twitch_config.py
```

Change:
```python
TWITCH_CHANNEL = "your_channel"
TWITCH_BOT_USERNAME = "your_bot"
TWITCH_OAUTH_TOKEN = "oauth:abc123..."
```

### 3️⃣ Test & Stream
```bash
# Test
python3 twitch_bot.py

# Stream!
python3 HorseBot_Simple.py start 2025-10-18 5000 --stream
```

---

## 🎨 What You Get

### Colorized Terminal Output
- Exciting banners for bets
- Color-coded by importance
- ASCII art intro
- Live stats ticker
- Market analysis displays

### Auto Twitch Chat Updates
- Morning picks announcement
- Bet placed alerts
- Bet skipped notifications
- Win/loss celebrations
- End of day summary

---

## 📺 OBS Setup

1. **Window Capture** → Terminal
2. **Font Size** → 18-20
3. **Fullscreen** terminal
4. **Dark theme** background

---

## 🎯 Stream Command

```bash
# Morning: Generate picks
./scripts/morning_prep.sh

# Start stream with colors + Twitch chat
python3 HorseBot_Simple.py start $(date +%Y-%m-%d) 5000 --stream
```

---

## 💡 Preview

Test the visuals before going live:
```bash
python3 stream_mode.py
```

Shows demo of all banners and colors!

---

**See full guide:** `docs/STREAMING_GUIDE.md` 🎬

