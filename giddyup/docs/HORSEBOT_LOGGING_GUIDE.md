# 📊 HorseBot Logging Guide

Complete guide to understanding HorseBot's logs and tracking bet execution.

---

## 📺 Console Output (Live View)

When the bot runs, you'll see detailed, step-by-step output:

### 1. Startup & Selection Loading

```
[2025-10-18 08:00:00] ℹ️ Fetching selections for 2025-10-18 with £5000 bankroll...
[2025-10-18 08:00:03] ✅ Loaded 53 potential bets
[2025-10-18 08:00:03] ℹ️   1. 09:30 Catterick - Arctic Fox (GB) @ 7.40 (min 7.03) [A-Hybrid_V3] £0.75
[2025-10-18 08:00:03] ℹ️   2. 09:30 Catterick - Wasthatok (GB) @ 9.00 (min 8.10) [B-Path_B] £2.00
...
[2025-10-18 08:00:05] ✅ Logged in successfully
[2025-10-18 08:00:05] ℹ️ Starting monitoring loop...
```

### 2. Processing Each Selection (at T-60)

```
================================================================================
[2025-10-18 08:30:00] ℹ️ 🏇 PROCESSING SELECTION
================================================================================
[2025-10-18 08:30:00] ℹ️    Horse: Arctic Fox (GB)
[2025-10-18 08:30:00] ℹ️    Course: Catterick
[2025-10-18 08:30:00] ℹ️    Race Time: 09:30
[2025-10-18 08:30:00] ℹ️    Strategy: A-Hybrid_V3
[2025-10-18 08:30:00] ℹ️    Expected Odds: 7.40
[2025-10-18 08:30:00] ℹ️    Minimum Odds Needed: 7.03
[2025-10-18 08:30:00] ℹ️    Stake: £0.75
```

### 3. Market Discovery

```
[2025-10-18 08:30:01] ℹ️ 🔍 Searching for market: Arctic Fox (GB) at Catterick
[2025-10-18 08:30:01] ℹ️    Querying Betfair API (time window: 09:30 ±15min)
[2025-10-18 08:30:02] ℹ️    Found 12 racing markets in time window
[2025-10-18 08:30:02] ℹ️    ✓ Course match: Catterick Bridge
[2025-10-18 08:30:02] ✅ MARKET FOUND | Market: 1.234567890 | Selection: 12345678 | Horse: Arctic Fox (GB)
```

### 4. Price Fetching

```
[2025-10-18 08:30:03] ℹ️ 💱 Fetching odds from Betfair...
[2025-10-18 08:30:03] ℹ️    Market ID: 1.234567890
[2025-10-18 08:30:03] ℹ️    Selection ID: 12345678
[2025-10-18 08:30:04] ℹ️    Market status: OPEN
[2025-10-18 08:30:04] ℹ️    Total matched: £45,234
[2025-10-18 08:30:04] ℹ️    Runner status: ACTIVE
[2025-10-18 08:30:04] ✅ PRICE OBTAINED: 7.40 (£1,234 available)
```

### 5. Decision Making

```
[2025-10-18 08:30:04] ℹ️ 📊 ODDS COMPARISON
[2025-10-18 08:30:04] ℹ️    Expected: 7.40
[2025-10-18 08:30:04] ℹ️    Current:  7.40
[2025-10-18 08:30:04] ℹ️    Minimum:  7.03
[2025-10-18 08:30:04] ℹ️    Drift:    +0.0%

[2025-10-18 08:30:04] ✅ BET CONDITIONS MET: Conditions met: odds 7.40 >= 7.03
```

### 6. Bet Execution

```
================================================================================
[2025-10-18 08:30:05] 💰 PLACING BET
================================================================================
[2025-10-18 08:30:05] 💰    Horse: Arctic Fox (GB)
[2025-10-18 08:30:05] 💰    Market ID: 1.234567890
[2025-10-18 08:30:05] 💰    Selection ID: 12345678
[2025-10-18 08:30:05] 💰    Stake: £0.75
[2025-10-18 08:30:05] 💰    Odds: 7.40
[2025-10-18 08:30:05] 💰    Potential Return: £5.55
[2025-10-18 08:30:05] 💰    Potential Profit: £4.80
[2025-10-18 08:30:05] 💰    Sending order to Betfair...
================================================================================
[2025-10-18 08:30:06] ✅ BET SUCCESSFULLY EXECUTED
================================================================================
[2025-10-18 08:30:06] ✅    Bet ID: 123456789012
[2025-10-18 08:30:06] ✅    Size Matched: £0.75
[2025-10-18 08:30:06] ✅    Average Price Matched: 7.40
[2025-10-18 08:30:06] ✅    Order Status: EXECUTION_COMPLETE
================================================================================
```

### 7. Skipped Bets (Odds Too Low)

```
================================================================================
[2025-10-18 08:30:15] ℹ️ 🏇 PROCESSING SELECTION
================================================================================
[2025-10-18 08:30:15] ℹ️    Horse: Wasthatok (GB)
[2025-10-18 08:30:15] ℹ️    Course: Catterick
...
[2025-10-18 08:30:17] ✅ PRICE OBTAINED: 7.85 (£890 available)

[2025-10-18 08:30:17] ℹ️ 📊 ODDS COMPARISON
[2025-10-18 08:30:17] ℹ️    Expected: 9.00
[2025-10-18 08:30:17] ℹ️    Current:  7.85
[2025-10-18 08:30:17] ℹ️    Minimum:  8.10
[2025-10-18 08:30:17] ℹ️    Drift:    -12.8%

[2025-10-18 08:30:17] ⚠️  SKIPPING BET: Odds too low: 7.85 < 8.10
================================================================================
```

### 8. Market Not Found

```
================================================================================
[2025-10-18 08:30:20] ℹ️ 🏇 PROCESSING SELECTION
================================================================================
[2025-10-18 08:30:20] ℹ️    Horse: Mystery Horse (IRE)
...
[2025-10-18 08:30:21] ℹ️ 🔍 Searching for market: Mystery Horse (IRE) at Leopardstown
[2025-10-18 08:30:21] ℹ️    Querying Betfair API (time window: 15:30 ±15min)
[2025-10-18 08:30:22] ℹ️    Found 8 racing markets in time window
[2025-10-18 08:30:22] ⚠️  ❌ MARKET NOT FOUND: Mystery Horse (IRE) at Leopardstown (checked 8 markets)

[2025-10-18 08:30:22] ⚠️  ⏭️  SKIPPING: Market not found on Betfair
================================================================================
```

---

## 📄 CSV Log File

**Location**: `strategies/logs/automated_bets/bot_log_2025-10-18.csv`

### CSV Headers

```csv
timestamp,race_time,course,horse,strategy,expected_odds,min_odds_needed,actual_odds,stake_gbp,bet_placed,bet_id,reason,matched,result,pnl_gbp,market_id,selection_id,market_found,price_obtained
```

### Example Entries

#### ✅ Successful Bet

```csv
2025-10-18 08:30:06,09:30,Catterick,Arctic Fox (GB),A-Hybrid_V3,7.40,7.03,7.40,0.75,YES,123456789012,Conditions met: odds 7.40 >= 7.03,YES,,,1.234567890,12345678,YES,YES
```

#### ⏭️ Skipped - Odds Too Low

```csv
2025-10-18 08:30:17,09:30,Catterick,Wasthatok (GB),B-Path_B,9.00,8.10,7.85,2.00,NO,,Odds too low: 7.85 < 8.10,NO,,,1.234567891,87654321,YES,YES
```

#### ❌ Market Not Found

```csv
2025-10-18 08:30:22,15:30,Leopardstown,Mystery Horse (IRE),B-Path_B,10.50,9.45,,2.00,NO,,Could not find market on Betfair,NO,,,,,NO,NO
```

#### ⚠️ Price Not Available

```csv
2025-10-18 09:15:33,12:30,Newmarket,Fast Runner (GB),A-Hybrid_V3,8.20,7.79,,0.75,NO,,No odds available,NO,,,1.234567892,99887766,YES,NO
```

---

## 📊 Understanding the Log Fields

| Field | Description | Example |
|-------|-------------|---------|
| **timestamp** | When action occurred (BST) | `2025-10-18 08:30:06` |
| **race_time** | Scheduled race time | `09:30` |
| **course** | Race course name | `Catterick` |
| **horse** | Horse name | `Arctic Fox (GB)` |
| **strategy** | Which strategy selected it | `A-Hybrid_V3` or `B-Path_B` |
| **expected_odds** | Odds when strategy ran | `7.40` |
| **min_odds_needed** | Minimum to place bet | `7.03` (95% of expected for A, 90% for B) |
| **actual_odds** | Current odds at T-60 | `7.40` (blank if not obtained) |
| **stake_gbp** | Bet stake amount | `0.75` |
| **bet_placed** | Was bet executed? | `YES` or `NO` |
| **bet_id** | Betfair bet ID | `123456789012` (blank if not placed) |
| **reason** | Why placed/skipped | `Conditions met: odds 7.40 >= 7.03` |
| **matched** | Bet matched on exchange? | `YES` or `NO` |
| **result** | Win/Loss (fill manually) | blank initially |
| **pnl_gbp** | Profit/Loss (fill manually) | blank initially |
| **market_id** | Betfair market ID | `1.234567890` |
| **selection_id** | Betfair selection ID | `12345678` |
| **market_found** | Could find on Betfair? | `YES` or `NO` |
| **price_obtained** | Got current price? | `YES` or `NO` |

---

## 🔍 Quick Queries

### Count Bets Placed Today

```bash
cat strategies/logs/automated_bets/bot_log_2025-10-18.csv | grep ",YES," | wc -l
```

### See Only Executed Bets

```bash
cat strategies/logs/automated_bets/bot_log_2025-10-18.csv | grep ",YES," | column -t -s,
```

### Check Market Finding Success Rate

```bash
# Markets found
cat strategies/logs/automated_bets/bot_log_2025-10-18.csv | grep -c ",YES,YES$"

# Markets not found  
cat strategies/logs/automated_bets/bot_log_2025-10-18.csv | grep -c ",NO,NO$"
```

### See All Betfair IDs

```bash
cat strategies/logs/automated_bets/bot_log_2025-10-18.csv | awk -F, '{print $16","$17","$4}' | grep -v "^,$"
```

Output:
```
1.234567890,12345678,Arctic Fox (GB)
1.234567891,87654321,Wasthatok (GB)
```

### Export for Betfair Reconciliation

```bash
# Get all executed bets with Betfair IDs
cat strategies/logs/automated_bets/bot_log_2025-10-18.csv | \
  awk -F, '$10=="YES" {print $11","$16","$17","$4","$8","$9}' | \
  column -t -s,
```

Output:
```
Bet_ID         Market_ID    Selection_ID  Horse          Odds  Stake
123456789012   1.234567890  12345678      Arctic Fox     7.40  0.75
```

---

## 📈 Analysis Examples

### Daily Summary

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
LOG="strategies/logs/automated_bets/bot_log_${DATE}.csv"

echo "=== Daily Summary for $DATE ==="
echo ""
echo "Total selections processed: $(tail -n +2 $LOG | wc -l)"
echo "Markets found: $(tail -n +2 $LOG | grep -c ",YES,YES$")"
echo "Markets not found: $(tail -n +2 $LOG | grep -c ",NO,NO$")"
echo "Prices obtained: $(tail -n +2 $LOG | awk -F, '$19=="YES"' | wc -l)"
echo ""
echo "Bets placed: $(tail -n +2 $LOG | grep -c ",YES,")"
echo "Bets skipped (odds): $(tail -n +2 $LOG | grep -c "Odds too low")"
echo "Bets skipped (market): $(tail -n +2 $LOG | grep -c "not found")"
echo ""
echo "Total staked: £$(tail -n +2 $LOG | awk -F, '$10=="YES" {sum+=$9} END {print sum}')"
```

### Compare Expected vs Actual Odds

```bash
# Show odds drift for all selections
cat strategies/logs/automated_bets/bot_log_2025-10-18.csv | \
  awk -F, 'NR>1 && $8!="" {
    drift = ($8 - $6) / $6 * 100;
    printf "%-30s %6.2f → %6.2f (%+5.1f%%)\n", $4, $6, $8, drift
  }'
```

Output:
```
Arctic Fox (GB)               7.40 →   7.40 ( +0.0%)
Wasthatok (GB)                9.00 →   7.85 (-12.8%)
Wagyu Star                   13.50 →  14.20 ( +5.2%)
```

---

## 🎯 Using Betfair IDs for Reconciliation

### Why Betfair IDs Matter

1. **Unique Identification**: Horse names can be similar; IDs are unique
2. **API Queries**: Can check bet status programmatically
3. **Settlements**: Match your logs with Betfair's settled bets
4. **Audit Trail**: Prove exactly which bet was placed

### Manual Betfair Check

1. Go to Betfair website
2. My Account → My Bets
3. Search by Bet ID from log
4. Verify:
   - ✅ Correct horse
   - ✅ Correct odds
   - ✅ Correct stake
   - ✅ Matched/unmatched status

### Programmatic Check (Future Feature)

```python
# Future enhancement: Check bet status
bet_status = client.betting.list_current_orders(
    bet_ids=['123456789012']
)

# Update CSV with results
```

---

## 🚨 Troubleshooting Log Issues

### No Entries in CSV

**Problem**: CSV file empty or only has header

**Causes**:
1. No selections loaded
2. All outside betting window
3. Script crashed before logging

**Check**:
```bash
# Did selections load?
cat strategies/logs/daily_bets/betting_log_2025.csv | grep 2025-10-18

# Console output?
# (should see "Loaded X potential bets")
```

### Market Found = NO

**Problem**: `market_found` column shows `NO`

**Causes**:
1. Market not published yet (too early)
2. Course name mismatch
3. Horse name mismatch
4. Non-UK/Irish racing

**Check**:
- Betfair website manually
- Run 1-2 hours before race
- Verify course name spelling

### Price Obtained = NO

**Problem**: Market found but no price

**Causes**:
1. Market suspended
2. Horse scratched
3. No liquidity yet
4. API error

**Check**:
```bash
# See the error message in reason column
cat strategies/logs/automated_bets/bot_log_2025-10-18.csv | \
  awk -F, '$19=="NO" {print $4": "$12}'
```

---

## 📊 Paper Trade Log Example

**Paper trade logs look identical** but have:

1. Dummy Betfair IDs (based on hash)
2. Simulated odds (real odds ± small variation)
3. "PAPER_" prefix on bet IDs
4. Warning messages in console

**Example Paper Trade Bet ID**: `PAPER_1729256405`

**Console shows**:
```
📋 PAPER TRADE MODE - BET NOT ACTUALLY PLACED
   Generated Paper Bet ID: PAPER_1729256405
```

---

## 💡 Pro Tips

1. **Monitor Console in Real-Time**: `tmux` recommended
2. **Save Console Output**: `./run_bot_today.sh 5000 2>&1 | tee bot_console_$(date +%Y-%m-%d).log`
3. **Daily Archive**: Keep logs for analysis
4. **Excel Import**: CSV loads perfectly into Excel/Google Sheets
5. **Backup Betfair Statements**: Download monthly for reconciliation

---

**Questions?** Check `HORSEBOT_README.md` or `HORSEBOT_QUICKSTART.md`

