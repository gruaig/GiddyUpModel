# Getting Started with GiddyUp

## 🎯 5-Minute Quick Start

### 1. Install Dependencies
```bash
cd /home/smonaghan/GiddyUpModel/giddyup
pip3 install -r horsebot_requirements.txt
```

### 2. Configure Betfair
```bash
cp HorseBot_config.template.py HorseBot_config.py
nano HorseBot_config.py
# Add your Betfair credentials
```

### 3. Configure Telegram (Optional)
```bash
cp telegram_config.template.py telegram_config.py
nano telegram_config.py
# Add your bot token and chat ID
python3 telegram_bot.py  # Test it
```

### 4. Run Morning Workflow
```bash
./scripts/morning_prep.sh
```

### 5. Start the Bot
```bash
# Option A: Service mode
sudo systemctl start giddyup-bot

# Option B: Manual mode
python3 HorseBot_Simple.py start $(date +%Y-%m-%d) 5000
```

---

## 📚 Next Steps

- **[Complete Daily Workflow](docs/COMPLETE_DAILY_WORKFLOW.md)** - Full guide
- **[Quick Reference](docs/QUICK_START_SERVICE.md)** - Daily commands
- **[Telegram Setup](docs/TELEGRAM_QUICKSTART.md)** - 3-step Telegram
- **[Documentation Index](docs/README.md)** - All guides

---

## 🆘 Help

### Common Issues

**Bot not starting?**
```bash
# Check config
python3 -c "from HorseBot_config import *; print('Config OK')"

# Test manually
python3 HorseBot_Simple.py start $(date +%Y-%m-%d) 5000
```

**No selections?**
```bash
# Check database
docker exec horse_racing psql -U postgres -d horse_db -c "SELECT COUNT(*) FROM racing.races WHERE race_date = CURRENT_DATE"
```

**Telegram not working?**
```bash
# Test connection
python3 telegram_bot.py
```

---

## 📁 Project Structure

```
giddyup/
├── README.md              ← Overview
├── GETTING_STARTED.md     ← This file
├── docs/                  ← All documentation
├── scripts/               ← Workflow scripts
├── HorseBot_Simple.py     ← Main bot
└── telegram_bot.py        ← Telegram integration
```

See [DIRECTORY_STRUCTURE.txt](DIRECTORY_STRUCTURE.txt) for complete layout.

---

**Ready? Run:** `./scripts/morning_prep.sh` 🚀

