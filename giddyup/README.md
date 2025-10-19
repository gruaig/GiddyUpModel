# 🏇 GiddyUp Horse Racing Bot

**Professional automated betting and trading system for UK & Irish horse racing.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Private-red.svg)]()

---

## 🎯 What Is This?

GiddyUp is a complete automated horse racing betting and trading platform that includes:

- **Traditional Betting Bot** - Places bets at optimal times based on your model selections
- **Back-Lay Trading Bot** - Exploits price movements for guaranteed profits  
- **Live Results Monitor** - Real-time race results with beautiful console output
- **Full Integration** - Telegram notifications, Twitch streaming, Excel reports
- **Professional Tools** - Comprehensive logging, P&L tracking, automated workflows

Perfect for algorithmic betting, live streaming, and systematic trading.

---

## 🚀 Quick Start

```bash
# Start the traditional betting bot
python3 HorseBot_Simple.py start 2025-10-20 5000

# Or with strategy-specific bankrolls
python3 HorseBot_Simple.py start 2025-10-20 A5000 B50000
```

**That's it!** The bot will:
1. Load your morning selections
2. Monitor Betfair odds continuously
3. Place bets at T-60 before each race
4. Check results 10 minutes after races
5. Post everything to Telegram automatically

📚 **[Full Quick Start Guide →](docs/getting-started/01-quick-start.md)**

---

## 📦 What's Included

### 🤖 Core Bots

| Bot | Purpose | Best For |
|-----|---------|----------|
| **HorseBot_Simple.py** | Traditional betting at T-60 | Long-term systematic betting |
| **HorseBackLayBot.py** | Back-to-lay trading | Exploiting price movements |
| **live_results_monitor.py** | Live results display | Streaming & monitoring |

### 📡 Integrations

- **Telegram** - Automatic notifications to your channel
- **Twitch** - Live streaming integration with chat
- **Betfair** - Real-time odds and bet placement
- **Sporting Life** - Official race results

### 🔧 Utilities

- Excel report generation
- PNG betting card creation
- Tweet file generation
- Automated result checking
- Price tracking & logging

---

## 📚 Documentation

**[→ Complete Documentation Encyclopedia](docs/INDEX.md)**

### Quick Links

- 🚀 **[Getting Started](docs/getting-started/)** - Installation, configuration, first run
- 🤖 **[Bot Guides](docs/bots/)** - Detailed guides for each bot
- 📱 **[Integrations](docs/integrations/)** - Telegram, Twitch, Betfair setup
- 🎬 **[Streaming](docs/streaming/)** - OBS setup, Twitch streaming
- 📊 **[Strategies](docs/strategies/)** - Bankroll & risk management
- 🔧 **[Advanced](docs/advanced/)** - Customization, troubleshooting
- 📋 **[Reference](docs/reference/)** - File formats, API reference

---

## 💡 Key Features

### ✅ Traditional Betting (HorseBot)
- Load morning selections from your model
- Monitor Betfair odds continuously
- Place bets at T-60 with odds validation
- Automatic result checking & P&L calculation
- Telegram notifications for all actions
- Comprehensive logging & reporting

### 💰 Trading (BackLayBot)
- Record morning prices automatically
- Monitor for profitable price movements
- Lay when odds shorten (10%+ drop)
- Lock in profit before race runs
- Green book - profit either way!
- Detailed trade logging

### 📊 Monitoring & Reporting
- Live results from Sporting Life API
- Beautiful console output for streaming
- Excel reports with full trade details
- Tweet file generation
- P&L tracking & analysis

---

## 🎬 Perfect For Streaming

All bots have beautiful console output designed for OBS/Twitch streaming:

- **Live Results Monitor** - Colorful race results with medals & emojis
- **Real-time P&L** - Track profits live on stream
- **Telegram Integration** - Share with your audience
- **Professional Output** - Clean, engaging display

📺 **[Streaming Setup Guide →](docs/streaming/)**

---

## 🔒 Safety Features

✅ **Dry Run Mode** - Test everything with paper trading first  
✅ **Odds Validation** - Won't bet if odds drifted too much  
✅ **Time Windows** - Only bets within safe time frames  
✅ **Commission Handling** - All P&L calculations include Betfair commission  
✅ **Error Handling** - Robust error recovery & logging  
✅ **Duplicate Prevention** - Won't post same result twice  

---

## 📊 Example Output

```
══════════════════════════════════════════════════════════════
🏇 HORSEBOT - 2025-10-20
══════════════════════════════════════════════════════════════
Bankrolls by Strategy:
  Strategy A: £5000
  Strategy B: £50000
Mode: 🟢 DRY RUN

Loading selections for 2025-10-20...
  Strategy A: £5000
  Strategy B: £50000
✅ Loaded 8 selections (times corrected +1hr)
📱 Sent morning picks to Telegram

🏇 T-60: Zenato (IRE) @ Stratford
   Expected: 13.50 | Min: 12.15 | Current: 13.50
💰 BET PLACED @ 13.50
📱 Posted to Telegram

⏰ Checking result for Zenato (IRE) @ Stratford...
🏆 WINNER! +£177.34
📱 Posted WIN to Telegram
```

---

## 📱 Telegram Notifications

Every action is automatically posted to your Telegram channel:

- 🏇 Morning selections card
- 💰 Bet placement notifications
- 🏆 Winner announcements with P&L
- 📊 Daily summaries
- 💰 Back-lay trade profits

**[→ Telegram Setup Guide](docs/integrations/telegram-setup.md)**

---

## 🎯 Requirements

- **Python 3.8+**
- **Betfair API access** (for live betting)
- **Telegram bot** (optional, for notifications)
- **PostgreSQL database** (for your model selections)

**[→ Installation Guide](docs/getting-started/02-installation.md)**

---

## ⚙️ Configuration

All configuration is done through simple Python files:

- `telegram_config.py` - Telegram bot settings
- `twitch_config.py` - Twitch streaming settings  
- `betfair_certs/` - Betfair API credentials

Templates provided in `config/` directory.

**[→ Configuration Guide](docs/getting-started/03-configuration.md)**

---

## 🤝 Support

- 📚 **[Full Documentation](docs/INDEX.md)**
- 🔧 **[Troubleshooting Guide](docs/advanced/troubleshooting.md)**
- 📋 **[File Formats Reference](docs/reference/file-formats.md)**

---

## ⚠️ Disclaimer

**18+ Only. Please gamble responsibly.**

This software is for educational and entertainment purposes. Trading and betting involve risk of loss. Past performance does not guarantee future results. Never bet more than you can afford to lose.

For support: [BeGambleAware.org](https://www.begambleaware.org)

---

## 📄 License

Private project. All rights reserved.

---

<div align="center">

**Made with ☕ and algorithms**

*Happy betting! 🏇💰*

</div>
