# Twitch Streaming Guide

## 🎬 Stream Your Automated Betting Live!

Stream your GiddyUp bot on Twitch with exciting, colorized output and automatic chat updates.

---

## 🚀 Quick Setup

### 1. Get Twitch OAuth Token

Visit: https://twitchapps.com/tmi/

Copy the OAuth token (looks like: `oauth:abcd1234...`)

### 2. Configure Twitch Bot

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
cp twitch_config.template.py twitch_config.py
nano twitch_config.py
```

Update:
```python
TWITCH_CHANNEL = "your_channel_name"      # Your Twitch channel (lowercase)
TWITCH_BOT_USERNAME = "your_bot_name"     # Bot username
TWITCH_OAUTH_TOKEN = "oauth:abc123..."    # Token from twitchapps.com
```

### 3. Test Connection

```bash
python3 twitch_bot.py
```

Should send test message to your Twitch chat!

### 4. Run Bot in Stream Mode

```bash
python3 HorseBot_Simple.py start 2025-10-18 5000 --stream
```

---

## 🎨 Stream Mode Features

### Colorized Output
- 🟢 **Green** - Successes, wins, good news
- 🔴 **Red** - Errors, losses, problems
- 🟡 **Yellow** - Warnings, important info
- 🔵 **Cyan** - General info, headers
- 🟣 **Magenta** - Bet placements

### Exciting Banners

**Morning Start:**
```
    🏇                                        
  ┌─────────────────────────────────────────┐
  │  🎯 GIDDYUP AUTOMATED BETTING SYSTEM 🎯 │
  └─────────────────────────────────────────┘

╔════════════════════════════════════════╗
║   🏇 GIDDYUP LIVE BETTING STREAM 🏇    ║
║            2025-10-18                   ║
╚════════════════════════════════════════╝

📊 TODAY'S CARD:
   Selections: 8
   Total Stake: £150.00
```

**Bet Placed:**
```
╔════════════════════════════════════════╗
║         🎯 BET PLACED! 🎯              ║
╚════════════════════════════════════════╝

  🏇 HORSE:  Woodhay Whisper (IRE)
  📍 COURSE: Kempton
  💰 STAKE:  £20.00
  📊 ODDS:   13.50
  ✨ PROFIT POTENTIAL: £250.00

  ⚡ LET'S GOOOOO! ⚡
```

**Bet Skipped:**
```
╔════════════════════════════════════════╗
║         ⏭️  BET SKIPPED  ⏭️            ║
╚════════════════════════════════════════╝

  🏇 HORSE:  Cayman Dancer (GB)
  📍 COURSE: Wolverhampton
  📊 CURRENT ODDS: 6.40
  ❌ NEEDED: 6.65
  
  ⚠️  REASON: Odds too low

  Moving on to next race...
```

**Selection Cards:**
```
┌─────────────────────────────────────────┐
│ 🔵 BET #1: Woodhay Whisper (IRE)        │
└─────────────────────────────────────────┘
  ⏰ 18:27 @ Kempton
  💰 £20.00 @ 13.50
  📊 B-Path_B
  💡 Edge +18pp | EV +500%
```

### Live Stats Ticker
```
📊 LIVE STATS | Bets: 3 | Skipped: 2 | Staked: £55.00 | Races Left: 5
```

---

## 📺 Twitch Chat Integration

When enabled, bot sends messages to your Twitch chat:

**Morning:**
```
🏇 LIVE BETTING STREAM! Today's card: 8 selections, £150 total stake. Let's make some money! 💰
```

**Bet Placed:**
```
🎯 BET PLACED! Woodhay Whisper @ Kempton (18:27) | £20 @ 13.50 | Potential profit: £250! LET'S GOOO! 🚀
```

**Bet Skipped:**
```
⏭️ SKIPPED: Cayman Dancer @ Wolverhampton - Odds too low: 6.40 < 6.65
```

**Win:**
```
🎉🎉🎉 WINNER! Woodhay Whisper @ Kempton won! Profit: +£244.60! YESSS! 🏆💰
```

**Loss:**
```
😔 Lost: Looks Fantastic @ Wolverhampton - £7.50. On to the next one! 💪
```

**End of Day:**
```
📈 END OF DAY: 3W-5L | P&L: +£450.00 | Thanks for watching! 🏇
```

---

## 🎥 OBS Setup

### Scene Setup

**Scene 1: Main View**
- Terminal window (fullscreen)
- Overlay: Your logo/branding
- Overlay: Social media links

**Scene 2: Bet Card**
- PNG betting card (full screen)
- Shows all day's bets

**Scene 3: Results**
- Excel report (screen capture)
- Shows P&L tracking

### Terminal Setup

**Font:** Monospace, size 16-20
**Background:** Black or dark theme
**Colors:** Enabled (stream mode provides ANSI colors)

**For best results:**
1. Use a terminal with good ANSI color support (iTerm2, Windows Terminal, GNOME Terminal)
2. Fullscreen or large window
3. Dark background
4. Increase font size for readability

### OBS Terminal Capture

Add source: Window Capture
- Select terminal window
- Enable "Capture Cursor"
- Crop to remove bars/edges

---

## 🎯 Streaming Commands

### Start Stream Session
```bash
# 1. Start OBS
# 2. Run bot in stream mode
python3 HorseBot_Simple.py start 2025-10-18 5000 --stream

# Bot will:
#   - Show ASCII art intro
#   - Display colorized selection cards
#   - Send updates to Twitch chat
#   - Show exciting banners for bets
```

### Tail Logs During Stream
```bash
# If running as service
tail -f logs/bot_service.log | while read line; do echo "$line"; done

# Color codes will work automatically
```

### Test Stream Mode
```bash
# Preview stream output
python3 stream_mode.py

# Shows demo of:
# - ASCII art
# - Banners
# - Selection cards
# - Market analysis
# - Live stats
```

---

## 💬 Chat Interaction

### Twitch Bot Commands (Optional)

You can add chat commands by extending `twitch_bot.py`:

```python
# Example commands
!picks - Show today's picks
!stats - Show current stats
!next - Show next race
!pnl - Show current P&L
```

### Chat Activity

Bot automatically posts to chat:
- ✅ Morning picks
- ✅ Each bet placed
- ✅ Each bet skipped
- ✅ Results
- ✅ End of day summary

Viewers can follow along in real-time!

---

## 🎭 Stream Tips

### 1. Build Hype
- Use countdown timers for big bets
- Celebrate wins enthusiastically
- Be transparent about losses

### 2. Explain Strategy
- Talk through why bets are placed/skipped
- Show the odds analysis
- Explain edge and expected value

### 3. Interact with Chat
- Ask chat for predictions
- Run polls on outcomes
- Share statistics

### 4. Show the Process
- Display PNG betting card at stream start
- Show Excel reports
- Explain P&L calculations

### 5. Be Consistent
- Same time every day
- Same format
- Regular updates

---

## 📊 Stream Overlays

### Suggested Overlays

1. **Top Bar:**
   - Channel name
   - "LIVE BETTING STREAM"
   - Current time

2. **Bottom Bar:**
   - Today's P&L (updates live)
   - Total bets placed
   - Win rate

3. **Side Panel:**
   - Next 3 races
   - Current bet
   - Social links

---

## 🔧 Configuration

### Enable/Disable Twitch Chat Messages

Edit `twitch_config.py`:
```python
SEND_MORNING_SUMMARY = True   # Morning summary
SEND_BET_PLACED = True         # Bet placed notifications
SEND_BET_SKIPPED = True        # Skip notifications
SEND_RESULTS = True            # Win/loss results
```

Set to `False` to disable specific message types.

### Stream Mode Only (No Chat)

```bash
# Just colorized output, no Twitch chat
python3 HorseBot_Simple.py start 2025-10-18 5000 --stream

# Chat messages only sent if twitch_config.py is configured
```

---

## 🎬 Sample Stream Schedule

### 08:00 - Stream Start
```
Starting Soon screen (5 minutes)
Show PNG betting card (review picks)
Explain today's strategy
```

### 08:30 - Bot Goes Live
```
Start bot in stream mode
Terminal fills screen
Exciting intro plays
Show selections one by one
```

### Throughout Day
```
Bot monitors markets
Shows odds checks
Exciting banners when betting
Chat gets notifications
```

### Evening - Results
```
Show Excel report
Fill in results live
Generate result tweets
Show final P&L
Thank viewers
```

---

## 🐛 Troubleshooting

### Colors not showing?

Your terminal needs ANSI color support:
```bash
# Test colors
python3 stream_mode.py

# If no colors, try different terminal:
# - GNOME Terminal (Linux)
# - Windows Terminal (Windows)
# - iTerm2 (Mac)
```

### Twitch chat not working?

```bash
# Test connection
python3 twitch_bot.py

# Check config
python3 -c "from twitch_config import *; print(f'Channel: {TWITCH_CHANNEL}')"
```

### Stream lagging?

- Reduce terminal font size
- Lower OBS quality settings
- Close other applications

---

## 📱 Example Stream Title

```
🏇 LIVE AUTOMATED HORSE RACING BETTING | GiddyUp Bot | !picks !stats
```

### Example Description
```
Automated betting bot using advanced algorithms to find value bets in UK/Irish horse racing.

Two strategies:
🟢 Strategy A: Mid-odds value (7-12)
🔵 Strategy B: High-odds value (7-16)

Bot places bets at T-60 if conditions are met.
All bets tracked with full transparency!

Commands:
!picks - Today's selections
!stats - Current stats
!discord - Join the community

⚠️ Gamble Responsibly
```

---

## ✅ Checklist Before Streaming

- [ ] OBS configured and tested
- [ ] Stream mode tested (`python3 stream_mode.py`)
- [ ] Twitch bot configured (`python3 twitch_bot.py`)
- [ ] Morning prep completed (`./scripts/morning_prep.sh`)
- [ ] PNG betting card ready to show
- [ ] Stream title/description updated
- [ ] Bot ready to start with `--stream` flag
- [ ] Chat ready for notifications

---

## 🎯 Sample Commands

```bash
# Test stream mode (no betting, just visuals)
python3 stream_mode.py

# Test Twitch chat
python3 twitch_bot.py

# Run bot in stream mode
python3 HorseBot_Simple.py start 2025-10-18 5000 --stream

# Run with Twitch chat (chat messages + colors)
python3 HorseBot_Simple.py start 2025-10-18 5000 --stream
# (Twitch messages auto-send if configured)
```

---

**Ready to stream?** Test with: `python3 stream_mode.py` 🎬🏇

