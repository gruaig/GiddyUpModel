# GiddyUp Bot - Service Setup Guide

## Overview

Run the GiddyUp betting bot as a systemd service that:
- ✅ Runs automatically all day
- ✅ Uses pre-generated morning selections (doesn't re-query database)
- ✅ Restarts on failure
- ✅ Stops after racing day ends (16 hours)
- ✅ Logs all activity

## 🔄 Daily Workflow

### Morning (8:00 AM) - Generate Selections

Run the morning prep script **ONCE** to query the database and lock in selections:

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
./morning_prep.sh
```

Or for a specific date/bankroll:
```bash
./morning_prep.sh 2025-10-19 5000
```

**What it does:**
1. ✅ Checks if odds data is ready in database
2. ✅ Queries database and generates betting selections
3. ✅ Creates CSV with locked-in bets
4. ✅ Generates PNG betting card
5. ✅ Shows summary and next steps

### During Day (8:30 AM onwards) - Run Bot as Service

Start the bot service to monitor and place bets all day:

```bash
sudo systemctl start giddyup-bot
```

**What it does:**
1. ✅ Loads pre-generated selections from CSV (doesn't re-query database)
2. ✅ Monitors Betfair markets
3. ✅ Places bets at T-60 if odds conditions met
4. ✅ Generates tweet files automatically
5. ✅ Runs until all races complete

### Evening - Check Results

```bash
# Generate Excel report
python3 generate_betting_report.py 2025-10-19

# Stop service manually if needed
sudo systemctl stop giddyup-bot
```

## 🛠️ Service Installation

### 1. Copy Service File

```bash
sudo cp /home/smonaghan/GiddyUpModel/giddyup/giddyup-bot.service /etc/systemd/system/
```

### 2. Update Service File (if needed)

Edit `/etc/systemd/system/giddyup-bot.service` and update:
- `User=smonaghan` (your username)
- `WorkingDirectory=` (your path)
- `--bankroll 5000` (your bankroll)

```bash
sudo nano /etc/systemd/system/giddyup-bot.service
```

### 3. Reload Systemd

```bash
sudo systemctl daemon-reload
```

### 4. Enable Service (optional - start on boot)

```bash
sudo systemctl enable giddyup-bot
```

## 📋 Service Commands

### Start the Bot
```bash
sudo systemctl start giddyup-bot
```

### Stop the Bot
```bash
sudo systemctl stop giddyup-bot
```

### Check Status
```bash
sudo systemctl status giddyup-bot
```

### View Live Logs
```bash
# Real-time logs
sudo journalctl -u giddyup-bot -f

# Or view the log file directly
tail -f /home/smonaghan/GiddyUpModel/giddyup/logs/bot_service.log
```

### Restart the Bot
```bash
sudo systemctl restart giddyup-bot
```

## 🔍 Monitoring

### Service Logs
```bash
# Last 50 lines
sudo journalctl -u giddyup-bot -n 50

# Follow in real-time
sudo journalctl -u giddyup-bot -f

# Today's logs
sudo journalctl -u giddyup-bot --since today
```

### Bot Activity Logs
```bash
# Main service log
tail -f logs/bot_service.log

# Daily bot log (CSV)
cat strategies/logs/automated_bets/bot_log_2025-10-19.csv

# Tweet files
ls -lh strategies/logs/tweets/
```

## ⚙️ Configuration

### Change Bankroll

Edit service file:
```bash
sudo nano /etc/systemd/system/giddyup-bot.service
```

Change the line:
```
--bankroll 5000 \
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart giddyup-bot
```

### Change to Live Mode (⚠️ REAL MONEY)

Edit service file and remove `--dry-run`:
```bash
sudo nano /etc/systemd/system/giddyup-bot.service
```

Change:
```
ExecStart=/usr/bin/python3 /home/smonaghan/GiddyUpModel/giddyup/HorseBot.py \
    --date $(date +%Y-%m-%d) \
    --bankroll 5000 \
    --no-refresh
```

(Removed `--dry-run`)

**⚠️ WARNING:** This will place REAL bets with REAL money!

## 🎯 Key Features

### --no-refresh Flag

**CRITICAL:** The service uses `--no-refresh` flag, which means:

✅ **Does:**
- Loads selections from existing CSV
- Uses pre-determined odds and stakes from morning
- Fast startup (no database query)
- Consistent bets throughout day

❌ **Does NOT:**
- Re-query the database
- Pick up new races added during day
- Recalculate odds/stakes
- Run strategy script

### Why This Matters

Without `--no-refresh`, every bot restart would:
1. Re-query the database
2. Get potentially different odds
3. Generate different selections
4. Change stakes/thresholds

With `--no-refresh`:
1. Locked-in selections from morning
2. Consistent strategy all day
3. No surprises from database updates
4. Faster, more reliable

## 🔧 Troubleshooting

### Service Won't Start

Check logs:
```bash
sudo systemctl status giddyup-bot
sudo journalctl -u giddyup-bot -n 50
```

Common issues:
- **Path wrong:** Check `WorkingDirectory` in service file
- **No CSV:** Run `./morning_prep.sh` first
- **Python not found:** Check `/usr/bin/python3` exists
- **Permissions:** Check user has access to files

### Bot Not Placing Bets

Check:
```bash
# Is it running?
sudo systemctl status giddyup-bot

# Are there selections?
tail -n 20 strategies/logs/daily_bets/betting_log_2025.csv

# Is it T-60 window yet?
date

# Check bot logic
tail -f logs/bot_service.log
```

### Service Keeps Restarting

```bash
# Check error log
tail -f logs/bot_service_error.log

# Check systemd logs
sudo journalctl -u giddyup-bot -n 100
```

Common causes:
- Database connection issues
- No selections found
- API errors (Betfair down)

### Want to Add New Selections

❌ **Don't restart with refresh!** This would re-query database.

✅ **Instead:**
1. Manually add to CSV
2. Restart service: `sudo systemctl restart giddyup-bot`

## 📅 Automated Morning Prep (Optional)

Create a cron job to run morning prep automatically:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 8:00 AM every day)
0 8 * * * /home/smonaghan/GiddyUpModel/giddyup/morning_prep.sh >> /home/smonaghan/GiddyUpModel/giddyup/logs/morning_prep/cron.log 2>&1
```

Then start the service manually or add another cron:
```bash
# Start bot at 8:30 AM
30 8 * * * sudo systemctl start giddyup-bot
```

## 🚀 Complete Daily Automation

For fully automated betting:

1. **Create morning prep cron:**
   ```bash
   0 8 * * * /home/smonaghan/GiddyUpModel/giddyup/morning_prep.sh
   ```

2. **Create bot start cron:**
   ```bash
   30 8 * * * sudo systemctl start giddyup-bot
   ```

3. **Service auto-stops after 16 hours** (configured in service file)

4. **Check results:**
   ```bash
   # Evening - generate report
   0 20 * * * /usr/bin/python3 /home/smonaghan/GiddyUpModel/giddyup/generate_betting_report.py $(date +\%Y-\%m-\%d)
   ```

## 📊 Example Daily Timeline

| Time | Action | Command |
|------|--------|---------|
| 08:00 | Morning prep runs | `cron: morning_prep.sh` |
| 08:30 | Bot service starts | `cron: systemctl start giddyup-bot` |
| 09:00-17:00 | Bot monitors and places bets | Automatic |
| 18:00 | Racing day ends | Automatic |
| 20:00 | Generate Excel report | `cron: generate_betting_report.py` |

## ✅ Best Practices

1. **Always run morning prep first** - Get fresh selections
2. **Use --no-refresh in service** - Consistent strategy
3. **Monitor logs initially** - Watch first few days
4. **Start in dry-run mode** - Test before real money
5. **Check CSV before starting** - Verify selections make sense
6. **Review reports daily** - Track performance

## 🎓 Advanced: Multiple Strategies

Run different services for different strategies:

```bash
# Copy service file
sudo cp giddyup-bot.service giddyup-bot-conservative.service

# Edit to use different bankroll/parameters
sudo nano /etc/systemd/system/giddyup-bot-conservative.service

# Start both
sudo systemctl start giddyup-bot
sudo systemctl start giddyup-bot-conservative
```

## 📝 Notes

- Service runs as your user (not root)
- Logs rotate automatically (systemd handles this)
- Service auto-restarts on failure (60s delay)
- Max runtime: 16 hours (57600 seconds)
- Bot creates tweet files automatically
- PNG card generated in morning prep

## 🆘 Getting Help

If you run into issues:

1. Check service status
2. Read logs
3. Verify morning prep ran successfully
4. Check CSV file exists and has today's date
5. Test bot manually first (without service)

```bash
# Test manually
python3 HorseBot.py --date $(date +%Y-%m-%d) --bankroll 5000 --dry-run --no-refresh
```

If that works, the service should too!

