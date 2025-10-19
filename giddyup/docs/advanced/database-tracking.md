# 📊 Database Tracking System

**Complete guide to the database tracking system for bot activities**

---

## 🎯 Overview

The database tracking system replaces CSV files with a proper PostgreSQL database for:

- ✅ **Accurate P&L calculations**
- ✅ **Telegram notification tracking**
- ✅ **Price movement history**
- ✅ **Complete audit trail**
- ✅ **Easy querying & reporting**
- ✅ **No data loss or overwrites**

---

## 📁 Database Schema

### Tables

1. **`bot_sessions`** - Each bot run (daily or per execution)
2. **`morning_selections`** - All morning picks from your model
3. **`price_observations`** - Every price check throughout the day
4. **`bet_decisions`** - Every betting decision (placed/skipped)
5. **`bet_results`** - Final results & P&L
6. **`telegram_notifications`** - All Telegram messages sent
7. **`backlay_trades`** - Back-to-lay trading activity

### Views

- **`vw_daily_pnl`** - Daily profit/loss summary
- **`vw_bet_details`** - Complete bet information
- **`vw_telegram_activity`** - Notification tracking
- **`vw_strategy_performance`** - Strategy metrics

---

## 🚀 Setup

### 1. Install PostgreSQL Client

```bash
pip3 install psycopg2-binary
```

### 2. Run Migration

```bash
cd /home/smonaghan/GiddyUpModel/giddyup
psql -U your_user -d giddyup -f migrations/002_bot_tracking_schema.sql
```

### 3. Set Database URL

```bash
export DATABASE_URL="postgresql://localhost/giddyup"
# Or add to ~/.bashrc or ~/.zshrc
```

---

## 💻 Usage in Code

### Basic Example

```python
from utilities.db_tracker import BotTracker

# Create tracker
tracker = BotTracker()

# Start session
session_id = tracker.start_session(
    date='2025-10-20',
    bot_type='HorseBot',
    bankroll_a=5000,
    bankroll_b=50000,
    mode='DRY_RUN'
)

# Record morning selection
selection_id = tracker.record_selection(
    session_id=session_id,
    date='2025-10-20',
    race_time='13:46',
    course='Kempton',
    horse='Bohemian Breeze (IRE)',
    strategy='A-Hybrid_V3',
    expected_odds=8.00,
    min_odds_needed=7.60,
    stake_gbp=7.50,
    reasoning='Strong form, good odds'
)

# Record price observation
tracker.record_price_observation(
    selection_id=selection_id,
    minutes_to_off=60,
    back_odds=9.60,
    market_status='OPEN'
)

# Record bet decision (skipped due to drift)
decision_id = tracker.record_bet_decision(
    selection_id=selection_id,
    decision='SKIPPED',
    minutes_to_off=60,
    current_odds=9.60,
    reason='Drifted 20.0% (max 15%)',
    drift_percentage=20.0
)

# Record Telegram notification
tracker.record_telegram_notification(
    notification_type='BET_SKIPPED',
    selection_id=selection_id,
    decision_id=decision_id,
    message_text='⏭️ BET SKIPPED...',
    success=True
)

# End session
tracker.end_session(
    session_id=session_id,
    status='COMPLETED',
    total_selections=48,
    total_bets_placed=8,
    total_bets_skipped=40,
    final_pnl=-35.00
)

# Close connection
tracker.close()
```

### Context Manager (Recommended)

```python
with BotTracker() as tracker:
    session_id = tracker.start_session(...)
    # ... do stuff ...
# Automatically closes connection
```

---

## 📊 Querying Data

### Daily P&L

```python
tracker = BotTracker()

# Get today's P&L
pnl = tracker.get_daily_pnl('2025-10-20')
print(f"Net P&L: £{pnl['net_pnl']}")
print(f"ROI: {pnl['roi_percentage']}%")
print(f"Win Rate: {pnl['wins']}/{pnl['wins'] + pnl['losses']}")
```

### Bet Details

```python
# Get all bets for a date
bets = tracker.get_bet_details('2025-10-20')

for bet in bets:
    print(f"{bet['race_time']} {bet['course']} - {bet['horse']}")
    print(f"  Decision: {bet['decision']}")
    print(f"  Result: {bet['result']}")
    print(f"  P&L: £{bet['net_pnl']}")
```

### Strategy Performance

```python
# Get last 30 days performance for A-Hybrid_V3
perf = tracker.get_strategy_performance('A-Hybrid_V3', days=30)

for day in perf:
    print(f"{day['date']}: £{day['net_pnl']} ({day['win_rate_percentage']}% win rate)")
```

### Custom Queries

```python
# Direct SQL for custom queries
query = """
    SELECT 
        date,
        COUNT(*) as total_notifications,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
    FROM telegram_notifications
    WHERE date >= CURRENT_DATE - 7
    GROUP BY date
    ORDER BY date DESC
"""

results = tracker._execute(query, fetch_all=True)
```

---

## 🔧 Integration with HorseBot

### Modify HorseBot_Simple.py

Add at the start of `run_bot()`:

```python
from utilities.db_tracker import BotTracker

def run_bot(date: str, bankrolls: dict, live: bool = False):
    tracker = BotTracker()
    
    # Start session
    session_id = tracker.start_session(
        date=date,
        bot_type='HorseBot',
        bankroll_a=bankrolls.get('A', bankrolls.get(None)),
        bankroll_b=bankrolls.get('B'),
        mode='LIVE' if live else 'DRY_RUN'
    )
    
    try:
        # Load selections
        selections = get_selections(date, bankrolls)
        
        # Record each selection
        for sel in selections:
            selection_id = tracker.record_selection(
                session_id=session_id,
                date=date,
                race_time=sel['time'],
                course=sel['course'],
                horse=sel['horse'],
                strategy=sel['strategy'],
                expected_odds=float(sel['odds']),
                min_odds_needed=float(sel['min_odds_needed']),
                stake_gbp=float(sel['stake_gbp']),
                reasoning=sel.get('reasoning', '')
            )
            sel['selection_id'] = selection_id  # Store for later use
        
        # ... rest of bot logic ...
        
        # When recording price observation:
        tracker.record_price_observation(
            selection_id=sel['selection_id'],
            minutes_to_off=int(minutes_to_off),
            back_odds=current_odds,
            market_id=market_id,
            selection_id_betfair=sel_id
        )
        
        # When making bet decision:
        decision_id = tracker.record_bet_decision(
            selection_id=sel['selection_id'],
            decision='PLACED',  # or 'SKIPPED' or 'FAILED'
            minutes_to_off=int(minutes_to_off),
            current_odds=current_odds,
            stake_gbp=float(sel['stake_gbp']),
            bet_id=bet_id,
            market_id=market_id,
            selection_id_betfair=sel_id,
            reason=reason,
            drift_percentage=drift_pct
        )
        
        # When sending Telegram:
        tracker.record_telegram_notification(
            notification_type='BET_PLACED',
            selection_id=sel['selection_id'],
            decision_id=decision_id,
            message_text=message,
            success=True
        )
        
        # When recording result:
        tracker.record_result_by_selection(
            selection_id=sel['selection_id'],
            result='WIN',  # or 'LOSS'
            settled_odds=current_odds,
            stake_gbp=float(sel['stake_gbp'])
        )
        
    finally:
        # End session
        tracker.end_session(
            session_id=session_id,
            status='COMPLETED',
            total_selections=len(selections),
            total_bets_placed=placed_count,
            total_bets_skipped=skipped_count,
            final_pnl=total_pnl
        )
        tracker.close()
```

---

## 📈 Benefits

### Accurate P&L

- ✅ No overwrites from Excel reports
- ✅ Commission calculations stored
- ✅ Running totals always correct
- ✅ Historical data preserved

### Telegram Tracking

- ✅ Know exactly what was sent
- ✅ Track success/failure
- ✅ No duplicate notifications
- ✅ Audit trail for debugging

### Price History

- ✅ Every price observation recorded
- ✅ Analyze drift patterns
- ✅ Optimize entry timing
- ✅ Back-test strategies

### Reporting

- ✅ Daily summaries
- ✅ Strategy comparison
- ✅ Win rate tracking
- ✅ ROI analysis

---

## 🔍 Example Queries

### Today's Winners

```sql
SELECT 
    ms.race_time,
    ms.course,
    ms.horse,
    ms.strategy,
    br.settled_odds,
    br.net_pnl
FROM bet_results br
JOIN bet_decisions bd ON br.decision_id = bd.decision_id
JOIN morning_selections ms ON bd.selection_id = ms.selection_id
WHERE ms.date = '2025-10-20'
  AND br.result = 'WIN'
ORDER BY ms.race_time;
```

### Telegram Success Rate

```sql
SELECT 
    notification_type,
    COUNT(*) as total,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM telegram_notifications
WHERE DATE(sent_at) = '2025-10-20'
GROUP BY notification_type;
```

### Price Drift Analysis

```sql
SELECT 
    ms.horse,
    ms.expected_odds,
    AVG(po.back_odds) as avg_observed_odds,
    MAX(po.back_odds) as max_odds,
    MIN(po.back_odds) as min_odds
FROM morning_selections ms
JOIN price_observations po ON ms.selection_id = po.selection_id
WHERE ms.date = '2025-10-20'
GROUP BY ms.selection_id, ms.horse, ms.expected_odds;
```

### Strategy ROI Last 30 Days

```sql
SELECT * FROM vw_strategy_performance
WHERE date >= CURRENT_DATE - 30
ORDER BY strategy, date DESC;
```

---

## 🛠️ Maintenance

### Backup Database

```bash
pg_dump giddyup > backup_$(date +%Y%m%d).sql
```

### Archive Old Data

```sql
-- Archive data older than 90 days
DELETE FROM price_observations 
WHERE observed_at < CURRENT_DATE - 90;

-- Keep selections, decisions, results for analysis
```

### Check Data Integrity

```sql
-- Find selections without decisions
SELECT * FROM morning_selections ms
LEFT JOIN bet_decisions bd ON ms.selection_id = bd.selection_id
WHERE bd.decision_id IS NULL
  AND ms.date = CURRENT_DATE;

-- Find decisions without results
SELECT * FROM bet_decisions bd
LEFT JOIN bet_results br ON bd.decision_id = br.decision_id
WHERE bd.decision = 'PLACED'
  AND br.result_id IS NULL;
```

---

## 🚨 Troubleshooting

### Connection Errors

```python
# Test connection
tracker = BotTracker('postgresql://localhost/giddyup')
try:
    conn = tracker._get_connection()
    print("✅ Connected successfully")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Missing Data

```python
# Check if selection exists
selection_id = tracker.get_selection_id(
    date='2025-10-20',
    race_time='13:46',
    course='Kempton',
    horse='Bohemian Breeze (IRE)',
    strategy='A-Hybrid_V3'
)
print(f"Selection ID: {selection_id}")
```

### Duplicate Entries

The schema uses `ON CONFLICT` clauses to handle duplicates gracefully:
- Selections: Updates odds if already exists
- Decisions: Updates decision if timestamp matches
- Results: Updates result if decision_id matches

---

## 📚 Next Steps

1. **Run migration** to create tables
2. **Test with db_tracker.py** standalone
3. **Integrate into HorseBot_Simple.py**
4. **Monitor for a few days**
5. **Compare with CSV data** for accuracy
6. **Deprecate CSV files** once confident

---

**🎯 Result: Complete, accurate tracking of all bot activities with no data loss!**

