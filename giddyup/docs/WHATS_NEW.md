# What's New - Service Mode & Media Generation

## 🎉 New Features

### 1. ✅ Service Mode - Run Bot All Day

The bot can now run as a **systemd service** that monitors bets all day without re-querying the database.

**Key Benefits:**
- 🔒 **Locked-in selections** - Query database once in morning, use all day
- 🔄 **Auto-restart** - Service restarts if it crashes
- ⏰ **Auto-stop** - Stops after 16 hours (racing day over)
- 📊 **Consistent** - Same bets all day, no surprises from database changes

### 2. ✅ PNG Betting Card Generation

Automatically creates a visual betting card when generating selections.

**Features:**
- 🎨 Modern, professional design
- 🟢 Color-coded strategies (Green=A, Blue=B)
- 📱 Perfect for sharing or printing
- 📊 Shows all key info: odds, stakes, reasoning

### 3. ✅ Auto Tweet File Generation

Tweet files are now automatically created when bets are placed.

**Features:**
- 🐦 Ready-to-post Twitter content
- #️⃣ Auto-generated hashtags
- 📁 Saved to `strategies/logs/tweets/`
- ✅ Works in both dry-run and live mode

---

## 🔧 New Functionality

### `--no-refresh` Flag

**Purpose:** Use existing CSV selections without re-querying database

```bash
# WITH --no-refresh (recommended for service)
python3 HorseBot.py --date 2025-10-19 --bankroll 5000 --no-refresh

# WITHOUT --no-refresh (re-queries database)
python3 HorseBot.py --date 2025-10-19 --bankroll 5000
```

**When to use:**
- ✅ Running as a service
- ✅ Testing with known selections
- ✅ Want consistent bets all day
- ✅ Restarting bot mid-day

**When NOT to use:**
- ❌ First run of the day (need to query DB)
- ❌ Want to pick up new races
- ❌ Testing strategy changes

### Morning Prep Script

New script that handles all morning preparation:

```bash
./morning_prep.sh
```

**What it does:**
1. Checks if odds data is ready
2. Queries database for today's selections
3. Generates CSV with locked-in bets
4. Creates PNG betting card
5. Shows summary and next steps

---

## 📁 New Files

| File | Purpose |
|------|---------|
| `giddyup-bot.service` | Systemd service definition |
| `morning_prep.sh` | Morning preparation script |
| `generate_betting_card.py` | PNG card generator |
| `SERVICE_SETUP_GUIDE.md` | Complete service setup guide |
| `QUICK_START_SERVICE.md` | Quick reference for daily use |
| `BETTING_MEDIA_GUIDE.md` | Guide for PNG and tweets |
| `WHATS_NEW.md` | This file! |

---

## 🔄 New Workflow

### Old Workflow (Manual)
```
8:00 AM → Query database manually
        → Run bot manually
        → Monitor all day
        → Stop bot manually
```

### New Workflow (Automated)
```
8:00 AM → ./morning_prep.sh (once)
8:30 AM → sudo systemctl start giddyup-bot
        → Bot runs all day automatically
        → Auto-stops when done
```

---

## 🎯 How It Works

### Morning (One Time)

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
./morning_prep.sh
```

**This:**
1. Queries database
2. Locks in selections
3. Saves to CSV
4. Generates PNG

**Output:**
- `betting_log_2025.csv` - All selections
- `betting_card_2025-10-19.png` - Visual card

### During Day (Automatic)

```bash
sudo systemctl start giddyup-bot
```

**Bot:**
1. Loads pre-generated CSV (`--no-refresh`)
2. Does NOT query database
3. Monitors Betfair all day
4. Places bets at T-60
5. Generates tweet files

**Output:**
- `bot_log_2025-10-19.csv` - Bet execution log
- `*.tweet` files - Ready-to-post tweets

### Evening

```bash
# Generate Excel report
python3 generate_betting_report.py 2025-10-19

# Service auto-stops after 16 hours
```

---

## 🆕 Code Changes

### HorseBot.py

**Added:**
- `refresh_from_db` parameter to `get_daily_selections()`
- `--no-refresh` CLI argument
- `refresh_from_db` to `HorseBot` class
- Auto-tweet generation in bet placement
- Better console output with hashtags

**Behavior:**
- Default: Re-queries database (backward compatible)
- With `--no-refresh`: Uses existing CSV only

### RUN_BOTH_STRATEGIES.sh

**Added:**
- Automatic PNG generation after CSV creation
- Graceful failure if Pillow not installed

### Dependencies

**Added to `horsebot_requirements.txt`:**
```
pillow>=10.0.0   # For PNG generation
```

---

## 🚀 Migration Guide

### If You're Currently Running Manually

**Option A: Keep Manual (No Changes Needed)**
```bash
# Continue as before - works exactly the same
python3 HorseBot.py --date $(date +%Y-%m-%d) --bankroll 5000 --dry-run
```

**Option B: Switch to Service Mode**
```bash
# 1. One-time setup
sudo cp giddyup-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

# 2. Daily usage
./morning_prep.sh                     # Morning
sudo systemctl start giddyup-bot      # Start bot
```

### If You Have Custom Scripts

Update any scripts that call `HorseBot.py`:

**Before:**
```bash
python3 HorseBot.py --date $DATE --bankroll $BANKROLL
```

**After (for service-like behavior):**
```bash
python3 HorseBot.py --date $DATE --bankroll $BANKROLL --no-refresh
```

---

## 🔍 Testing New Features

### Test PNG Generation
```bash
./morning_prep.sh

# View PNG
xdg-open strategies/logs/daily_bets/betting_card_$(date +%Y-%m-%d).png
```

### Test --no-refresh Flag
```bash
# 1. Generate selections
./morning_prep.sh

# 2. Run bot with --no-refresh
python3 HorseBot.py --date $(date +%Y-%m-%d) --bankroll 5000 --dry-run --no-refresh

# Should see: "(Not querying database - using pre-generated selections)"
```

### Test Tweet Generation
```bash
# Run bot and wait for a bet to be placed
python3 HorseBot.py --date $(date +%Y-%m-%d) --bankroll 5000 --dry-run --no-refresh

# Check tweet files
ls -lh strategies/logs/tweets/

# View a tweet
cat strategies/logs/tweets/*.tweet
```

### Test Service
```bash
# 1. Install service
sudo cp giddyup-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

# 2. Start service
sudo systemctl start giddyup-bot

# 3. Watch logs
tail -f logs/bot_service.log

# 4. Check status
sudo systemctl status giddyup-bot

# 5. Stop service
sudo systemctl stop giddyup-bot
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `SERVICE_SETUP_GUIDE.md` | Complete service setup and configuration |
| `QUICK_START_SERVICE.md` | Quick daily reference |
| `BETTING_MEDIA_GUIDE.md` | PNG and tweet generation |
| `HORSEBOT_README.md` | Original bot documentation |
| `WHATS_NEW.md` | This file - new features |

---

## 🎓 Best Practices

1. **Always run morning prep first** 
   - Ensures fresh selections
   - Creates PNG for reference
   
2. **Use --no-refresh in service**
   - Consistent strategy all day
   - No surprises from DB changes
   
3. **Start in dry-run mode**
   - Test new features safely
   - Verify behavior before live
   
4. **Monitor logs initially**
   - Watch first few days
   - Verify everything works
   
5. **Check CSV before starting**
   - Verify selections make sense
   - Confirm odds look right

---

## 🐛 Known Issues / Limitations

1. **Python cache** - If tweet files aren't being generated:
   ```bash
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} +
   ```

2. **Service date** - Service uses current date, doesn't support specific dates
   - For specific dates, run manually

3. **PNG requires Pillow** - Install with `pip3 install pillow`

4. **Service needs config** - Must have `HorseBot_config.py` configured

---

## ❓ FAQ

**Q: Will old commands still work?**  
A: Yes! All changes are backward compatible.

**Q: Do I have to use service mode?**  
A: No! You can continue running manually.

**Q: What if database updates during the day?**  
A: With `--no-refresh`, bot ignores updates (uses morning selections).

**Q: Can I add bets mid-day?**  
A: Yes! Edit CSV manually, restart bot with `--no-refresh`.

**Q: How do I go back to querying database?**  
A: Remove `--no-refresh` flag.

---

## 🆘 Need Help?

1. Read `SERVICE_SETUP_GUIDE.md` for detailed setup
2. Check logs: `tail -f logs/bot_service.log`
3. Test manually first before using service
4. Use `--dry-run` until confident

---

## 🎉 Summary

**You can now:**
- ✅ Run bot as a service all day
- ✅ Generate beautiful PNG betting cards
- ✅ Auto-create tweet files for every bet
- ✅ Lock in selections (no mid-day DB changes)
- ✅ Automate entire daily workflow

**All while maintaining:**
- ✅ Backward compatibility
- ✅ Manual control when needed
- ✅ Dry-run safety testing
- ✅ Complete logging

Enjoy! 🏇💰

