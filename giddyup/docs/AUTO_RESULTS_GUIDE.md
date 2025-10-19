# Automatic Results Checking

## 🎉 NEW FEATURE: Auto-fetch Race Results!

Your bot now automatically fetches race results from Sporting Life API and updates your logs!

---

## 🚀 How It Works

### Data Source
**Sporting Life API:** https://www.sportinglife.com/api/horse-racing/v2/fast-results?countryGroups=UK,IRE

Returns official race results for UK & Irish racing:
- Course name
- Race time
- Winner and placed horses
- Official status (WEIGHEDIN)

### Automatic Matching
1. Fetches results from API
2. Matches by course name + race time
3. Checks if your horse won (position 1 = WIN)
4. Calculates P&L automatically
5. Updates CSV with results
6. Sends notifications

---

## 📋 Usage

### Option 1: Grade Day Script (Recommended)
```bash
./scripts/grade_day.sh 2025-10-18
```

**Does everything:**
- ✅ Fetches results from API
- ✅ Matches all your bets
- ✅ Updates CSV with WIN/LOSS
- ✅ Calculates P&L
- ✅ Generates Excel report
- ✅ Generates result tweets
- ✅ Sends Telegram/Twitch notifications
- ✅ Shows final summary

### Option 2: Check Results Only
```bash
python3 results_checker.py 2025-10-18
```

Just checks and updates results (no report generation).

### Option 3: Monitor Results Live (During Stream)
```bash
python3 auto_results_monitor.py 2025-10-18
```

Runs continuously, checking results 5 minutes after each race finishes.
Perfect for live streaming!

---

## 🎬 For Streaming

When running bot in stream mode, results are announced automatically:

```bash
# Start bot with auto-results
python3 HorseBot_Simple.py start 2025-10-18 5000 --stream
```

**5 minutes after each race:**
```
⏰ Checking result for Woodhay Whisper @ Kempton...

╔════════════════════════════════════════════════════════════╗
║                    🎉🎉🎉 WINNER! 🎉🎉🎉                  ║
╚════════════════════════════════════════════════════════════╝

  🏆 Woodhay Whisper (IRE) @ Kempton
  
  💰💰💰 PROFIT: +£244.60 💰💰💰
  
  🎉 YESSSSS! 🎉
```

**Twitch chat gets:**
```
🎉🎉🎉 WINNER! Woodhay Whisper @ Kempton won! Profit: +£244.60! YESSS! 🏆💰
```

---

## 💰 P&L Calculation

### Win
```
Gross Return = Odds × Stake
Commission = Gross Return × 2%
Net Profit = Gross Return - Stake - Commission
```

### Loss
```
Loss = -Stake
```

**Automatically calculated!** No manual math needed.

---

## 📊 Example Output

### Running grade_day.sh
```bash
$ ./scripts/grade_day.sh 2025-10-18

📊 GRADING DAY - 2025-10-18
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Found 42 bet(s) to check

STEP 1: Fetch Results from Sporting Life API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📡 Fetching results...
✅ Found 50 race results

😔 LOSS: Arkinthestars @ Catterick (11:56) | P&L: £-2.00
😔 LOSS: Made All @ Catterick (11:56) | P&L: £-2.00
🎉 WIN: Crown Of Oaks @ Ascot (16:40) | P&L: +£5.13
...

💾 Updating CSV with 42 result(s)...
✅ CSV updated

STEP 2: Generate Excel Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Generating Excel report with results...
✅ Report generated

STEP 3: Generate Result Tweets & Media
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐦 Generating tweet files...
✅ Generated 42 result tweets

STEP 4: Send to Communication Channels
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 Telegram: Sent daily summary

✅ GRADING COMPLETE FOR 2025-10-18
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Final Summary:
   Total Bets: 42
   Wins: 1 | Losses: 41 | Pending: 0
   Total Staked: £85.00
   Total P&L: £-79.87
   ROI: -94.0%
   Win Rate: 2.4%
```

---

## ⏰ Timing

**Results available:** ~5 minutes after race finishes

**Official status:** API shows `"status": "WEIGHEDIN"` when official

**Best practice:**
- Wait 30 minutes after last race
- Run `./scripts/grade_day.sh`
- All results will be fetched automatically

---

## 🔍 How Matching Works

### Course Matching
- Normalizes course names (lowercase, trim)
- Matches "Wolverhampton" with "wolverhampton"
- Handles slight variations

### Horse Matching
- Removes country codes: (GB), (IRE), (FR), (USA), (GER)
- Normalizes whitespace
- Case-insensitive
- Example: "Woodhay Whisper (IRE)" matches "Woodhay Whisper"

### Time Matching
- Direct match: "10:56" = "10:56"
- Allows ±60 minute difference (in case of delays)

### Result Determination
- **Position 1** = WIN
- **Position 2-20** = LOSS
- **Not found** = Pending (race not finished or not found)

---

## 🐛 Troubleshooting

### "No results found"
- Results not available yet (wait 5+ minutes after race)
- Check API directly: https://www.sportinglife.com/api/horse-racing/v2/fast-results?countryGroups=UK,IRE
- Race might not be in UK/IRE

### "Result not available yet"
- Race still running or being stewards inquiry
- Results not official yet
- Try again in 10 minutes

### "Horse not found in results"
- Name mismatch (check spelling)
- Course mismatch
- Time offset (check actual race time)
- Race might be non-UK/IRE

### Testing
```bash
# Test API access
curl "https://www.sportinglife.com/api/horse-racing/v2/fast-results?countryGroups=UK,IRE" | python3 -m json.tool | head -50

# Test matching
python3 results_checker.py 2025-10-18
```

---

## 📁 Files

| File | Purpose |
|------|---------|
| `results_checker.py` | Fetch & check results |
| `auto_results_monitor.py` | Live monitoring |
| `scripts/grade_day.sh` | Complete end-of-day workflow |
| `scripts/end_of_day.sh` | Calls grade_day.sh |

---

## ✅ Benefits

**Before:**
- Manual result entry
- Copy/paste from websites
- Prone to errors
- Time consuming

**After:**
- ✅ Automatic result fetching
- ✅ Instant notifications
- ✅ Pre-filled Excel reports
- ✅ No manual work needed!

---

## 🎯 Complete Workflow

### End of Day (One Command)
```bash
./scripts/grade_day.sh
```

That's it! Everything else is automatic:
1. Fetches results from API
2. Updates CSV
3. Generates Excel report (results pre-filled!)
4. Generates result tweets
5. Sends Telegram notifications
6. Shows summary

**No more manual result entry!** 🎉

---

## 📱 Notifications

Results sent to:
- ✅ Telegram - Individual results + daily summary
- ✅ Twitch Chat - Win/loss announcements
- ✅ Stream Display - Exciting banners
- ✅ Tweet Files - Ready to post

---

## 🔒 API Info

**Sporting Life API:**
- Free, public API
- No authentication needed
- Updates within 5 minutes of race finishing
- Official results only (WEIGHEDIN status)
- Covers UK & Irish racing

**Rate limits:** Be reasonable (we check once per minute max)

---

**Try it now:** `./scripts/grade_day.sh 2025-10-18` 🚀

