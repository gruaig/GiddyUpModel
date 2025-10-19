#!/usr/bin/env python3
"""
GiddyUp HorseBot - Simplified Standalone Version
=================================================

Commands:
    python3 HorseBot_Simple.py start 2025-10-18 5000     # Start bot
    python3 HorseBot_Simple.py stop                      # Stop bot
    python3 HorseBot_Simple.py status                    # Check status
    python3 HorseBot_Simple.py 2025-10-18 5000 --live    # Legacy: run once

Default is DRY RUN (no real bets). Add --live to bet for real.
"""

import csv
import time
import sys
import subprocess
import os
import signal
import argparse
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

try:
    import pytz
    from betfairlightweight import APIClient
    from betfairlightweight.filters import (
        market_filter, time_range, price_projection,
        place_instruction, limit_order
    )
except ImportError:
    print("\n" + "="*80)
    print("Missing dependencies! Install with:")
    print("  pip3 install betfairlightweight pytz")
    print("="*80 + "\n")
    sys.exit(1)

# Import result checking functions
try:
    from results_checker import fetch_results, check_horse_position, calculate_pnl
    RESULTS_CHECKER_AVAILABLE = True
except ImportError:
    RESULTS_CHECKER_AVAILABLE = False
    print("⚠️  results_checker not available - automatic result checking disabled")

# Telegram integration
try:
    from telegram_bot import (
        send_morning_picks, send_bet_placed, send_bet_skipped,
        send_market_analysis, send_result, send_daily_summary,
        TELEGRAM_ENABLED
    )
except ImportError:
    TELEGRAM_ENABLED = False
    def send_morning_picks(*args, **kwargs): return False
    def send_bet_placed(*args, **kwargs): return False
    def send_bet_skipped(*args, **kwargs): return False
    def send_market_analysis(*args, **kwargs): return False
    def send_result(*args, **kwargs): return False
    def send_daily_summary(*args, **kwargs): return False

# Stream mode (colorized output for Twitch)
try:
    from stream_mode import (
        Colors, banner, big_announcement, racing_ascii_art,
        bet_placed_banner, bet_skipped_banner, win_announcement,
        loss_announcement, market_analysis as stream_market_analysis,
        selection_card, live_stats, countdown_timer,
        daily_summary_banner
    )
    STREAM_MODE_AVAILABLE = True
except ImportError:
    STREAM_MODE_AVAILABLE = False

# Twitch chat bot
try:
    from twitch_bot import (
        send_to_twitch, send_morning_summary as twitch_morning,
        send_bet_placed as twitch_bet_placed,
        send_bet_skipped as twitch_bet_skipped,
        send_win, send_loss,
        TWITCH_ENABLED
    )
except ImportError:
    TWITCH_ENABLED = False
    def send_to_twitch(*args, **kwargs): return False
    def twitch_morning(*args, **kwargs): return False
    def twitch_bet_placed(*args, **kwargs): return False
    def twitch_bet_skipped(*args, **kwargs): return False
    def send_win(*args, **kwargs): return False
    def send_loss(*args, **kwargs): return False

# Global stream mode flag
STREAM_MODE = False

# ══════════════════════════════════════════════════════════════════════════════
# HARDCODED CONFIG (Your Betfair credentials)
# ══════════════════════════════════════════════════════════════════════════════

BETFAIR_USERNAME = "colfish"
BETFAIR_PASSWORD = "Perlisagod$$1"
BETFAIR_APP_KEY = "Gs1Zut6sZQxncj6V"

# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

T_MINUS_START_TRACKING = 240  # Start tracking 4 hours before race
T_MINUS_BET_WINDOW = 60       # Make betting decision at T-60
RECHECK_INTERVAL = 300        # Re-check every 5 minutes
MIN_LIQUIDITY = 1000          # Min £ matched

# PID file for process management
PID_FILE = Path(__file__).parent / "horsebot.pid"
MAX_DRIFT = 0.15              # Max 15% price drift

BST = pytz.timezone("Europe/London")
LOG_DIR = Path(__file__).parent / "strategies" / "logs" / "automated_bets"
TWEET_DIR = Path(__file__).parent / "strategies" / "logs" / "tweets"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TWEET_DIR.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# PROCESS CONTROL FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def write_pid():
    """Write current process PID to file."""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

def read_pid():
    """Read PID from file."""
    try:
        with open(PID_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

def is_running():
    """Check if bot is running."""
    pid = read_pid()
    if not pid:
        return False
    
    try:
        os.kill(pid, 0)  # Check if process exists
        return True
    except OSError:
        # Process doesn't exist, clean up PID file
        PID_FILE.unlink(missing_ok=True)
        return False

def stop_bot():
    """Stop the running bot."""
    pid = read_pid()
    if not pid:
        print("❌ No bot is currently running")
        return False
    
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"🛑 Stopping bot (PID: {pid})...")
        
        # Wait for graceful shutdown
        for i in range(10):
            if not is_running():
                print("✅ Bot stopped successfully")
                return True
            time.sleep(1)
        
        # Force kill if needed
        os.kill(pid, signal.SIGKILL)
        print("⚠️  Bot force-stopped")
        return True
        
    except OSError:
        print("❌ Failed to stop bot - process not found")
        PID_FILE.unlink(missing_ok=True)
        return False

def show_status():
    """Show bot status."""
    if is_running():
        pid = read_pid()
        print(f"🟢 Bot is RUNNING (PID: {pid})")
        
        # Try to show some basic info
        try:
            with open(LOG_DIR / f"bot_actions_{datetime.now().strftime('%Y-%m-%d')}.csv", 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    print(f"📊 Today's activity: {len(lines)-1} entries logged")
        except FileNotFoundError:
            print("📊 No activity logged today")
    else:
        print("🔴 Bot is STOPPED")
        print("💡 Use 'python3 HorseBot_Simple.py start <date> <bank>' to start")

# ══════════════════════════════════════════════════════════════════════════════
# TWEET GENERATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def normalize_horse_name(horse: str) -> str:
    """Normalize horse name for hashtag."""
    return re.sub(r' \([A-Z]+\)$', '', horse).replace(' ', '').replace('-', '')

def normalize_course_name(course: str) -> str:
    """Normalize course name for hashtag."""
    return course.replace(' ', '').replace('-', '')

def generate_bet_tweet_file(race_time: str, course: str, horse: str, odds: float, stake: float, strategy: str, date: str):
    """Generate bet placed tweet file."""
    horse_tag = normalize_horse_name(horse)
    course_tag = normalize_course_name(course)
    
    # Clean race time for filename (remove colons)
    race_time_clean = race_time.replace(':', '')
    filename = f"{race_time_clean}_{course_tag}_{horse_tag}.tweet"
    filepath = TWEET_DIR / filename
    
    tweet_content = f"""🎯 New Bet Placed

🏇 {horse} @ {course}
⏰ Race: {race_time}
💰 £{stake:.2f} @ {odds:.2f}
📈 Strategy: {strategy}

#HorseRacing #Betting #{course_tag} #{horse_tag}"""
    
    with open(filepath, 'w') as f:
        f.write(tweet_content)
    
    log(f"   📄 Generated tweet file: {filename}", "SUCCESS")

def generate_result_tweet_file(race_time: str, course: str, horse: str, result: str, pnl: float, date: str):
    """Generate bet result tweet file."""
    horse_tag = normalize_horse_name(horse)
    course_tag = normalize_course_name(course)
    
    # Clean race time for filename (remove colons)
    race_time_clean = race_time.replace(':', '')
    filename = f"{race_time_clean}_{course_tag}_{horse_tag}_result.tweet"
    filepath = TWEET_DIR / filename
    
    # Choose emoji based on result
    if result.upper() == "WIN":
        emoji = "🎉"
        result_text = "WON"
        pnl_prefix = "+" if pnl > 0 else ""
    else:
        emoji = "😔"
        result_text = "Lost"
        pnl_prefix = ""
    
    tweet_content = f"""{emoji} Bet Result

🏇 {horse} @ {course}
⏰ Race: {race_time}
📊 Result: {result_text}
💰 P&L: {pnl_prefix}£{pnl:.2f}

#HorseRacing #Betting #{course_tag} #{horse_tag}"""
    
    with open(filepath, 'w') as f:
        f.write(tweet_content)
    
    log(f"   📄 Generated result tweet file: {filename}", "SUCCESS")

def generate_summary_tweet_file(date: str):
    """Generate daily summary tweet file."""
    actions_file = LOG_DIR / f"bot_actions_{date}.csv"
    
    if not actions_file.exists():
        log("No actions file found for summary tweet", "WARNING")
        return
    
    # Parse CSV data
    with open(actions_file, 'r') as f:
        lines = f.readlines()
    
    total_bets = len(lines) - 1  # Exclude header
    dry_run_bets = sum(1 for line in lines[1:] if "DRY_RUN" in line)
    skipped_bets = sum(1 for line in lines[1:] if ",NO," in line)
    
    # Calculate total staked
    total_staked = 0
    courses = set()
    for line in lines[1:]:
        parts = line.strip().split(',')
        if len(parts) >= 8:
            try:
                total_staked += float(parts[7])  # Stake column
                courses.add(parts[1])  # Course column
            except (ValueError, IndexError):
                continue
    
    # Get top 3 courses for hashtags
    course_counts = {}
    for line in lines[1:]:
        parts = line.strip().split(',')
        if len(parts) >= 2:
            course = parts[1]
            course_counts[course] = course_counts.get(course, 0) + 1
    
    top_courses = sorted(course_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    course_hashtags = "".join(f" #{normalize_course_name(course)}" for course, _ in top_courses)
    
    filename = f"{date}_summary.tweet"
    filepath = TWEET_DIR / filename
    
    tweet_content = f"""📊 {date} Summary

🎯 Total Selections: {total_bets}
💰 Total Staked: £{total_staked:.2f}
✅ Bets Placed: {dry_run_bets}
⏭️ Skipped: {skipped_bets}

#HorseRacing #Betting #Automation{course_hashtags}"""
    
    with open(filepath, 'w') as f:
        f.write(tweet_content)
    
    log(f"📄 Generated summary tweet file: {filename}", "SUCCESS")

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def ts():
    return datetime.now(BST).strftime("%Y-%m-%d %H:%M:%S")

def log(msg, level="INFO"):
    """Log message - stream mode aware."""
    global STREAM_MODE
    
    if STREAM_MODE and STREAM_MODE_AVAILABLE:
        # Colorized output for streaming
        color_map = {
            "INFO": Colors.BRIGHT_CYAN,
            "SUCCESS": Colors.BRIGHT_GREEN,
            "WARNING": Colors.BRIGHT_YELLOW,
            "ERROR": Colors.BRIGHT_RED,
            "BET": Colors.BRIGHT_MAGENTA
        }
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "BET": "💰"}
        color = color_map.get(level, Colors.WHITE)
        print(f"{color}[{ts()}] {icons.get(level, '•')} {msg}{Colors.RESET}")
    else:
        # Normal output
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "BET": "💰"}
        print(f"[{ts()}] {icons.get(level, '•')} {msg}")

# ══════════════════════════════════════════════════════════════════════════════
# LOAD SELECTIONS FROM DATABASE
# ══════════════════════════════════════════════════════════════════════════════

def get_selections(date: str, bankrolls: dict) -> List[Dict]:
    """
    Load selections by running the RUN_BOTH_STRATEGIES.sh script.
    
    Args:
        date: Date in YYYY-MM-DD format
        bankrolls: Dict with {strategy: bankroll} or {None: bankroll}
    """
    # Convert bankrolls dict to single value for script
    if None in bankrolls:
        total_bankroll = bankrolls[None]
        log(f"Loading selections for {date} (£{total_bankroll} bankroll)...")
    else:
        # Use total of both strategies
        total_bankroll = sum(bankrolls.values())
        log(f"Loading selections for {date}...")
        for strat, amount in bankrolls.items():
            log(f"  Strategy {strat}: £{amount}")
    
    script = Path(__file__).parent / "strategies" / "RUN_BOTH_STRATEGIES.sh"
    
    try:
        subprocess.run(
            [str(script), date, str(int(total_bankroll))],
            capture_output=True,
            text=True,
            cwd=script.parent,
            timeout=60
        )
        
        # Read from CSV
        csv_file = script.parent / "logs" / "daily_bets" / "betting_log_2025.csv"
        selections = []
        
        with csv_file.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["date"] == date:
                    # FIX: Database times are 1 hour behind UK time - add 1 hour
                    db_time = datetime.strptime(row["time"], "%H:%M")
                    corrected_time = db_time + timedelta(hours=1)
                    row["time"] = corrected_time.strftime("%H:%M")
                    row["original_db_time"] = db_time.strftime("%H:%M")
                    selections.append(row)
        
        log(f"Loaded {len(selections)} selections (times corrected +1hr)", "SUCCESS")
        
        # Send morning picks to Telegram
        if selections and TELEGRAM_ENABLED:
            try:
                send_morning_picks(date, selections)
                log("📱 Sent morning picks to Telegram", "SUCCESS")
            except Exception as e:
                log(f"Telegram error: {e}", "WARNING")
        
        return selections
        
    except Exception as e:
        log(f"Error loading selections: {e}", "ERROR")
        return []

# ══════════════════════════════════════════════════════════════════════════════
# BETFAIR
# ══════════════════════════════════════════════════════════════════════════════

class Betfair:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.client = None
    
    def login(self):
        if self.dry_run:
            log("DRY RUN MODE - Will track real prices but not place bets", "WARNING")
        
        log("Connecting to Betfair...")
        self.client = APIClient(
            username=BETFAIR_USERNAME,
            password=BETFAIR_PASSWORD,
            app_key=BETFAIR_APP_KEY,
        )
        self.client.login_interactive()
        log("Connected to Betfair", "SUCCESS")
    
    def logout(self):
        if self.client:
            self.client.logout()
    
    def find_market(self, horse: str, course: str, race_time: str) -> Optional[tuple]:
        """Find market and selection ID."""
        log(f"🔍 Finding: {horse} at {course} {race_time}")
        
        # In dry run without connection, use dummy IDs
        if self.dry_run and not self.client:
            market_id = f"1.{abs(hash(horse)) % 1000000}"
            sel_id = str(abs(hash(horse)) % 100000)
            log(f"   SIMULATED: {market_id} / {sel_id}", "WARNING")
            return (market_id, sel_id)
        
        # Otherwise find real market (works in dry run if connected)
        try:
            # Parse race time
            naive_dt = datetime.strptime(f"{race_time}", "%H:%M")
            today = datetime.now(BST).date()
            race_dt = BST.localize(datetime.combine(today, naive_dt.time()))
            
            time_from = (race_dt - timedelta(minutes=15)).isoformat()
            time_to = (race_dt + timedelta(minutes=15)).isoformat()
            
            markets = self.client.betting.list_market_catalogue(
                filter=market_filter(
                    event_type_ids=["7"],
                    market_type_codes=["WIN"],
                    market_start_time=time_range(from_=time_from, to=time_to),
                ),
                max_results=100,
                market_projection=["EVENT", "RUNNER_DESCRIPTION"]
            )
            
            # Try to match markets
            found_courses = []
            for market in markets:
                venue = market.event.venue.lower()
                found_courses.append(venue)
                
                # Fuzzy course matching
                if course.lower() in venue or venue in course.lower():
                    log(f"   ✓ Course matched: {market.event.venue}")
                    
                    # Try to match horse
                    for runner in market.runners:
                        runner_name = runner.runner_name.lower()
                        horse_name = horse.lower()
                        
                        # Fuzzy horse matching
                        if horse_name in runner_name or runner_name in horse_name:
                            log(f"   ✅ Market: {market.market_id} / Selection: {runner.selection_id}", "SUCCESS")
                            log(f"   ✅ Matched: '{horse}' → '{runner.runner_name}'")
                            return (market.market_id, str(runner.selection_id))
                    
                    log(f"   ✗ No horse match in {market.event.venue} (checked {len(market.runners)} runners)")
            
            log(f"   ❌ Not found. Available courses: {', '.join(set(found_courses[:5]))}", "WARNING")
            return None
            
        except Exception as e:
            log(f"   Error: {e}", "ERROR")
            return None
    
    def get_odds(self, market_id: str, sel_id: str) -> Optional[float]:
        """Get current odds."""
        # In dry run, we still get REAL odds from Betfair (just don't bet)
        if self.dry_run:
            import random
            # Simulate odds if not connected to Betfair
            if not self.client:
                odds = round(7.0 + random.uniform(-0.5, 0.5), 2)
                log(f"   SIMULATED odds: {odds:.2f}", "WARNING")
                return odds
            # Otherwise fall through to get real odds
        
        try:
            proj = price_projection(price_data=["EX_BEST_OFFERS"])
            books = self.client.betting.list_market_book([market_id], proj)
            
            if not books:
                return None
            
            book = books[0]
            if book.total_matched < MIN_LIQUIDITY:
                log(f"   Low liquidity: £{book.total_matched:.0f}", "WARNING")
                return None
            
            for runner in book.runners:
                if str(runner.selection_id) == str(sel_id):
                    if runner.ex.available_to_back:
                        odds = runner.ex.available_to_back[0].price
                        available = runner.ex.available_to_back[0].size
                        # Only log once - removed duplicate logging
                        return odds
                    else:
                        return None
            
            return None
            
        except Exception as e:
            log(f"   Error: {e}", "ERROR")
            return None
    
    def place_bet(self, market_id: str, sel_id: str, odds: float, stake: float, horse: str) -> Optional[str]:
        """Place bet."""
        log("=" * 80)
        log(f"💰 PLACING BET: {horse} @ {odds:.2f} for £{stake:.2f}", "BET")
        log(f"   Return: £{stake * odds:.2f} | Profit: £{stake * (odds - 1):.2f}")
        
        if self.dry_run:
            bet_id = f"DRY_{int(time.time())}"
            log(f"   DRY RUN - Not actually placed (ID: {bet_id})", "WARNING")
            log("=" * 80)
            return bet_id
        
        try:
            instruction = place_instruction(
                order_type="LIMIT",
                selection_id=int(sel_id),
                side="BACK",
                limit_order=limit_order(size=stake, price=odds, persistence_type="PERSIST")
            )
            
            report = self.client.betting.place_orders(market_id=market_id, instructions=[instruction])
            
            if report and report.status == "SUCCESS":
                for rep in report.place_instruction_reports:
                    if rep.status == "SUCCESS":
                        log(f"   ✅ BET PLACED! ID: {rep.bet_id}", "SUCCESS")
                        log("=" * 80)
                        return rep.bet_id
            
            log(f"   Failed: {report.error_code if report else 'Unknown'}", "ERROR")
            log("=" * 80)
            return None
            
        except Exception as e:
            log(f"   Error: {e}", "ERROR")
            log("=" * 80)
            return None

# ══════════════════════════════════════════════════════════════════════════════
# RESULT CHECKING
# ══════════════════════════════════════════════════════════════════════════════

def check_and_post_results(action_log: Path, date: str, race_results: dict) -> int:
    """
    Check for finished races and post results to Telegram.
    Returns number of new results posted.
    """
    if not RESULTS_CHECKER_AVAILABLE:
        return 0
    
    new_results = 0
    updated_rows = []
    
    # Read all bets from CSV
    with action_log.open('r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Ensure required fields exist
    if 'result' not in fieldnames:
        fieldnames = list(fieldnames) + ['result']
    if 'pnl_gbp' not in fieldnames:
        fieldnames = list(fieldnames) + ['pnl_gbp']
    if 'telegram_posted' not in fieldnames:
        fieldnames = list(fieldnames) + ['telegram_posted']
    
    # Check each bet
    for row in rows:
        # Initialize new fields if they don't exist
        if 'result' not in row:
            row['result'] = ''
        if 'pnl_gbp' not in row:
            row['pnl_gbp'] = ''
        if 'telegram_posted' not in row:
            row['telegram_posted'] = ''
        
        # Skip if already has result
        if row.get('result') in ['WIN', 'LOSS']:
            updated_rows.append(row)
            continue
        
        # Skip if not a placed bet
        if row.get('bet_placed') not in ['DRY_RUN', 'EXECUTED']:
            updated_rows.append(row)
            continue
        
        # Check if result available
        horse = row['horse']
        course = row['course']
        race_time = row['race_time']
        
        result = check_horse_position(horse, course, race_time, race_results)
        
        if result:
            # Calculate P&L
            odds = float(row.get('actual_odds', row.get('expected_odds', 0)))
            stake = float(row.get('stake', 0))
            pnl = calculate_pnl(result, odds, stake)
            
            # Update the row
            row['result'] = result
            row['pnl_gbp'] = str(pnl)
            row['telegram_posted'] = 'YES'
            
            # Post to Telegram
            if TELEGRAM_ENABLED:
                try:
                    send_result(
                        horse=horse,
                        course=course,
                        race_time=race_time,
                        result=result,
                        odds=odds,
                        stake=stake,
                        pnl=pnl,
                        strategy=row.get('strategy', 'Unknown')
                    )
                    log(f"   📱 Posted {result} to Telegram: {horse} @ {course}", "SUCCESS")
                    new_results += 1
                except Exception as e:
                    log(f"   Telegram error: {e}", "WARNING")
        
        updated_rows.append(row)
    
    # Write back to CSV if any results were updated
    if new_results > 0:
        with action_log.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)
    
    return new_results

# ══════════════════════════════════════════════════════════════════════════════
# MAIN BOT
# ══════════════════════════════════════════════════════════════════════════════

def run_bot(date: str, bankrolls: dict, live: bool = False, stream: bool = False):
    """Run the bot."""
    global STREAM_MODE
    STREAM_MODE = stream
    
    # Stream mode intro
    if STREAM_MODE and STREAM_MODE_AVAILABLE:
        print(racing_ascii_art())
        time.sleep(0.5)
    
    log("=" * 80)
    log(f"🏇 HORSEBOT - {date}")
    log("=" * 80)
    
    # Display bankroll info
    if None in bankrolls:
        log(f"Bankroll: £{bankrolls[None]:.0f}")
    else:
        log(f"Bankrolls by Strategy:")
        for strat, amount in bankrolls.items():
            log(f"  Strategy {strat}: £{amount:.0f}")
    
    log(f"Mode: {'🔴 LIVE BETTING' if live else '🟢 DRY RUN'}")
    
    if STREAM_MODE:
        log(f"🎬 Stream Mode: ENABLED (Colorized output)")
        if TWITCH_ENABLED:
            log(f"📺 Twitch Chat: ENABLED")
    
    log("")
    
    # Load selections
    selections = get_selections(date, bankrolls)
    if not selections:
        log("No selections - exiting", "WARNING")
        return
    
    # Stream mode: Show daily summary banner
    if STREAM_MODE and STREAM_MODE_AVAILABLE:
        total_stake = sum(float(s['stake_gbp']) for s in selections)
        print(daily_summary_banner(date, len(selections), total_stake))
        
        # Show each selection as a card
        for i, sel in enumerate(selections, 1):
            print(selection_card(
                i, sel['horse'], sel['course'], sel['time'],
                float(sel['odds']), float(sel['stake_gbp']),
                sel['strategy'], sel['reasoning']
            ))
            time.sleep(0.3)  # Dramatic pause
        
        # Send to Twitch chat
        if TWITCH_ENABLED:
            twitch_morning(date, len(selections), total_stake)
    
    # Setup
    betfair = Betfair(dry_run=not live)
    betfair.login()
    
    # Log files
    action_log = LOG_DIR / f"bot_actions_{date}.csv"
    price_log = LOG_DIR / f"bot_prices_{date}.csv"
    
    if not action_log.exists():
        with action_log.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "race_time", "course", "horse", "strategy",
                "expected_odds", "min_odds", "actual_odds", "stake",
                "bet_placed", "bet_id", "reason",
                "market_id", "selection_id", "result", "pnl_gbp", "telegram_posted"
            ])
    
    if not price_log.exists():
        with price_log.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "race_time", "course", "horse",
                "minutes_to_off", "odds", "market_id", "selection_id", "status"
            ])
    
    try:
        log("Starting monitoring loop...")
        log("📊 Will track prices continuously for each race")
        log("💰 Will make ONE betting decision per race at T-60")
        log("   (Betting window: T-65 to T-55, stops at T-1 before race)")
        log("")
        
        bet_placed = set()  # Races we've placed bets on
        market_cache = {}   # Store market IDs to avoid repeated lookups
        results_checked = set()  # Races we've checked results for
        last_result_check = datetime.now(BST) - timedelta(minutes=10)  # Last time we checked results
        
        # Get last race time
        last_time = max(datetime.strptime(s["time"], "%H:%M") for s in selections)
        today = datetime.now(BST).date()
        end_time = BST.localize(datetime.combine(today, last_time.time())) + timedelta(minutes=30)
        
        while datetime.now(BST) < end_time:
            now = datetime.now(BST)
            
            for sel in selections:
                key = f"{sel['time']}_{sel['horse']}"
                
                # Parse race time
                race_dt = BST.localize(
                    datetime.combine(
                        today,
                        datetime.strptime(sel["time"], "%H:%M").time()
                    )
                )
                
                minutes_to_off = (race_dt - now).total_seconds() / 60
                
                # Skip if race already finished
                if minutes_to_off < 0:
                    continue
                
                # Skip if too early to start tracking
                if minutes_to_off > T_MINUS_START_TRACKING:
                    continue
                
                # Skip if already bet on this race
                if key in bet_placed:
                    continue
                # Find market (cache to avoid repeated lookups)
                if key not in market_cache:
                    log("")
                    log(f"🏇 T-{int(minutes_to_off)}min: {sel['time']} {sel['course']} - {sel['horse']}")
                    if 'original_db_time' in sel:
                        log(f"   (DB: {sel['original_db_time']} → Corrected: {sel['time']} UK)")
                    
                    market_info = betfair.find_market(sel["horse"], sel["course"], sel["time"])
                    if not market_info:
                        log(f"   ❌ Market not found", "WARNING")
                        # Log to price tracking that we couldn't find market
                        with price_log.open("a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                ts(), sel["time"], sel["course"], sel["horse"],
                                f"{minutes_to_off:.1f}", "", "", "", "MARKET_NOT_FOUND"
                            ])
                        continue
                    
                    market_cache[key] = market_info
                
                market_id, sel_id = market_cache[key]
                
                # Get current odds
                current_odds = betfair.get_odds(market_id, sel_id)
                
                # Log odds lookup result
                if current_odds:
                    log(f"   💱 Odds: {current_odds:.2f}")
                
                # Log price to tracking file
                if minutes_to_off > T_MINUS_BET_WINDOW:
                    status = "TRACKING"
                elif minutes_to_off > 5:
                    status = "BET_WINDOW"
                else:
                    status = "TOO_LATE"
                with price_log.open("a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        ts(), sel["time"], sel["course"], sel["horse"],
                        f"{minutes_to_off:.1f}", 
                        f"{current_odds:.2f}" if current_odds else "",
                        market_id, sel_id, status
                    ])
                
                if not current_odds:
                    continue
                
                # Check if we should make a decision
                in_bet_window = 55 <= minutes_to_off <= 65  # T-60 window (±5 min buffer)
                
                # Evaluate betting criteria
                min_odds = float(sel["min_odds_needed"])
                criteria_met = current_odds >= min_odds
                
                expected = float(sel["odds"])
                drift = abs(current_odds - expected) / expected
                drift_ok = drift <= MAX_DRIFT
                
                # Show analysis even outside betting window
                if minutes_to_off < 240:  # Only show for races < 4 hours away
                    log("")
                    log(f"📊 T-{int(minutes_to_off)}: {sel['horse']} @ {current_odds:.2f}")
                    log(f"   Expected: {expected:.2f} | Min: {min_odds:.2f} | Stake: £{sel['stake_gbp']}")
                    
                    if criteria_met and drift_ok:
                        if in_bet_window:
                            log(f"   ✅ CRITERIA MET & IN WINDOW → ", "SUCCESS")
                        else:
                            log(f"   ⏰ CRITERIA MET but T-{int(minutes_to_off)} (need T-60)", "WARNING")
                    elif not criteria_met:
                        log(f"   ❌ Odds too low: {current_odds:.2f} < {min_odds:.2f}", "WARNING")
                    elif not drift_ok:
                        log(f"   ❌ Drifted {drift*100:.1f}% (max {MAX_DRIFT*100:.0f}%)", "WARNING")
                
                # Make betting decision ONCE at T-60 (with small buffer)
                if in_bet_window:
                    log("")
                    log("=" * 80)
                    log(f"⏰ T-{int(minutes_to_off)} BETTING DECISION FOR {sel['time']} RACE")
                    log(f"   Horse: {sel['horse']} at {sel['course']}")
                    log("=" * 80)
                    log(f"📊 Final odds check:")
                    log(f"   Expected: {expected:.2f}")
                    log(f"   Current:  {current_odds:.2f}")
                    log(f"   Minimum:  {min_odds:.2f}")
                    log(f"   Drift:    {drift*100:+.1f}% (max {MAX_DRIFT*100:.0f}%)")
                    log("")
                    
                    if not criteria_met:
                        reason = f"Odds too low: {current_odds:.2f} < {min_odds:.2f}"
                        log(f"⏭️  SKIP BET: {reason}", "WARNING")
                        log("=" * 80)
                        
                        # Stream mode: Show skip banner
                        if STREAM_MODE and STREAM_MODE_AVAILABLE:
                            print(bet_skipped_banner(
                                sel["horse"], sel["course"], reason,
                                current_odds, min_odds
                            ))
                        
                        # Send to Twitch chat
                        if TWITCH_ENABLED:
                            twitch_bet_skipped(sel["horse"], sel["course"], reason)
                        
                        # Send Telegram notification
                        if TELEGRAM_ENABLED:
                            try:
                                send_bet_skipped(
                                    horse=sel["horse"],
                                    course=sel["course"],
                                    race_time=sel["time"],
                                    current_odds=current_odds,
                                    min_odds=min_odds,
                                    expected_odds=float(sel["odds"]),
                                    reason=reason,
                                    strategy=sel["strategy"]
                                )
                            except Exception as e:
                                log(f"Telegram error: {e}", "WARNING")
                        
                        with action_log.open("a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                ts(), sel["time"], sel["course"], sel["horse"], sel["strategy"],
                                sel["odds"], sel["min_odds_needed"], current_odds, sel["stake_gbp"],
                                "NO", "", reason, market_id, sel_id, "", "", ""
                            ])
                        
                        bet_placed.add(key)
                        continue
                    
                    if not drift_ok:
                        reason = f"Drifted {drift*100:.1f}% (max {MAX_DRIFT*100:.0f}%)"
                        log(f"⏭️  SKIP BET: {reason}", "WARNING")
                        log("=" * 80)
                        
                        # Stream mode: Show skip banner
                        if STREAM_MODE and STREAM_MODE_AVAILABLE:
                            print(bet_skipped_banner(
                                sel["horse"], sel["course"], reason,
                                current_odds, min_odds
                            ))
                        
                        # Send to Twitch chat
                        if TWITCH_ENABLED:
                            twitch_bet_skipped(sel["horse"], sel["course"], reason)
                        
                        # Send Telegram notification
                        if TELEGRAM_ENABLED:
                            try:
                                send_bet_skipped(
                                    horse=sel["horse"],
                                    course=sel["course"],
                                    race_time=sel["time"],
                                    current_odds=current_odds,
                                    min_odds=min_odds,
                                    expected_odds=float(sel["odds"]),
                                    reason=reason,
                                    strategy=sel["strategy"]
                                )
                            except Exception as e:
                                log(f"Telegram error: {e}", "WARNING")
                        
                        with action_log.open("a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                ts(), sel["time"], sel["course"], sel["horse"], sel["strategy"],
                                sel["odds"], sel["min_odds_needed"], current_odds, sel["stake_gbp"],
                                "NO", "", reason, market_id, sel_id, "", "", ""
                            ])
                        
                        bet_placed.add(key)
                        continue
                    
                    # Place bet!
                    log(f"✅ ALL CONDITIONS MET", "SUCCESS")
                    log("")
                    
                    # Stream mode: Show exciting bet banner
                    if STREAM_MODE and STREAM_MODE_AVAILABLE:
                        profit_potential = (current_odds - 1) * float(sel["stake_gbp"])
                        print(bet_placed_banner(
                            sel["horse"], sel["course"], current_odds,
                            float(sel["stake_gbp"]), profit_potential
                        ))
                    
                    bet_id = betfair.place_bet(
                        market_id, sel_id, current_odds, 
                        float(sel["stake_gbp"]), sel["horse"]
                    )
                    
                    # Send to Twitch chat
                    if bet_id and TWITCH_ENABLED:
                        profit_potential = (current_odds - 1) * float(sel["stake_gbp"])
                        twitch_bet_placed(
                            sel["horse"], sel["course"], sel["time"],
                            current_odds, float(sel["stake_gbp"]), profit_potential
                        )
                    
                    # Generate tweet file for bet placed
                    try:
                        race_time = sel["time"]  # Use 'time' field from CSV
                        course = sel["course"]
                        horse = sel["horse"]
                        odds = current_odds
                        stake = float(sel["stake_gbp"])
                        strategy = sel["strategy"]
                        generate_bet_tweet_file(race_time, course, horse, odds, stake, strategy, date)
                    except Exception as e:
                        log(f"Could not generate bet tweet file: {e}", "WARNING")
                    
                    # Send Telegram notification
                    if bet_id and TELEGRAM_ENABLED:
                        try:
                            send_bet_placed(
                                horse=sel["horse"],
                                course=sel["course"],
                                race_time=sel["time"],
                                odds=current_odds,
                                stake=float(sel["stake_gbp"]),
                                strategy=sel["strategy"],
                                expected_odds=float(sel["odds"]),
                                is_dry_run=betfair.dry_run
                            )
                        except Exception as e:
                            log(f"Telegram error: {e}", "WARNING")
                    
                    if bet_id:
                        bet_status = "DRY_RUN" if betfair.dry_run else "EXECUTED"
                        reason = f"{bet_status} @ {current_odds:.2f}"
                        
                        with action_log.open("a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                ts(), sel["time"], sel["course"], sel["horse"], sel["strategy"],
                                sel["odds"], sel["min_odds_needed"], current_odds, sel["stake_gbp"],
                                bet_status, bet_id, reason, market_id, sel_id, "", "", ""
                            ])
                    else:
                        reason = "Bet placement failed"
                        
                        with action_log.open("a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                ts(), sel["time"], sel["course"], sel["horse"], sel["strategy"],
                                sel["odds"], sel["min_odds_needed"], current_odds, sel["stake_gbp"],
                                "FAILED", "", reason, market_id, sel_id, "", "", ""
                            ])
                    
                    bet_placed.add(key)
            
            # Check if done betting (all races either bet on or passed T-60)
            if len(bet_placed) == len(selections):
                log("")
                log("All betting decisions made - continuing price tracking until races finish", "SUCCESS")
                # Continue tracking prices even after betting is done
            
            # Check for race results (every 5 minutes, for races that finished 10+ mins ago)
            time_since_last_check = (now - last_result_check).total_seconds() / 60
            if RESULTS_CHECKER_AVAILABLE and time_since_last_check >= 5:
                # Check which races should have results by now (finished 10+ mins ago)
                races_to_check = []
                for sel in selections:
                    race_dt = BST.localize(
                        datetime.combine(
                            today,
                            datetime.strptime(sel["time"], "%H:%M").time()
                        )
                    )
                    time_since_race = (now - race_dt).total_seconds() / 60
                    
                    # Check if race finished 10+ minutes ago and not already checked
                    key = f"{sel['time']}_{sel['horse']}"
                    if time_since_race >= 10 and key not in results_checked and key in bet_placed:
                        races_to_check.append(sel)
                
                if races_to_check:
                    log("")
                    log(f"⏰ Checking results for {len(races_to_check)} finished race(s)...", "INFO")
                    
                    # Fetch results from API
                    race_results = fetch_results(date)
                    
                    if race_results:
                        # Check and post results
                        new_results = check_and_post_results(action_log, date, race_results)
                        
                        if new_results > 0:
                            log(f"   ✅ Posted {new_results} new result(s) to Telegram", "SUCCESS")
                        
                        # Mark races as checked
                        for sel in races_to_check:
                            key = f"{sel['time']}_{sel['horse']}"
                            results_checked.add(key)
                
                last_result_check = now
            
            # Sleep
            time.sleep(RECHECK_INTERVAL)
        
        # Summary
        log("")
        log("=" * 80)
        log("SESSION COMPLETE")
        log("=" * 80)
        log(f"Betting decisions made: {len(bet_placed)}/{len(selections)}")
        log(f"Action log: {action_log}")
        log(f"Price tracking log: {price_log}")
        log("")
        
        # Show some price movement stats
        with price_log.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                log(f"Total price observations: {len(rows)}")
                horses = set(r["horse"] for r in rows)
                log(f"Horses tracked: {len(horses)}")
        log("")
        
        # Generate Excel report
        log("📊 Generating Excel report...")
        try:
            report_script = Path(__file__).parent / "generate_betting_report.py"
            result = subprocess.run(
                [sys.executable, str(report_script), date],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                log(result.stdout, "SUCCESS")
            else:
                log("Report generation skipped (install openpyxl to enable)", "WARNING")
        except Exception as e:
            log(f"Could not generate report: {e}", "WARNING")
        
        # Generate daily summary tweet file
        log("🐦 Generating daily summary tweet file...")
        try:
            generate_summary_tweet_file(date)
        except Exception as e:
            log(f"Could not generate summary tweet file: {e}", "WARNING")
        
    finally:
        betfair.logout()

# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def parse_bankroll_arg(bankroll_arg):
    """
    Parse bankroll argument. Supports:
    - Single value: 5000
    - Strategy-specific: A5000 B2000
    
    Returns:
        dict: {strategy: bankroll} or {None: bankroll}
    """
    if isinstance(bankroll_arg, str):
        parts = bankroll_arg.split()
        
        # Check if any part starts with A or B (strategy prefix)
        if any(p.startswith(('A', 'B')) for p in parts):
            bankrolls = {}
            for part in parts:
                if part.startswith('A'):
                    bankrolls['A'] = float(part[1:])
                elif part.startswith('B'):
                    bankrolls['B'] = float(part[1:])
            return bankrolls
        else:
            # Single value
            return {None: float(bankroll_arg)}
    else:
        # Already a float
        return {None: float(bankroll_arg)}

def main():
    """Main CLI handler."""
    parser = argparse.ArgumentParser(description="GiddyUp HorseBot")
    parser.add_argument("command", nargs="?", help="Command: start, stop, status")
    parser.add_argument("date", nargs="?", help="Date (YYYY-MM-DD)")
    parser.add_argument("bankroll", nargs="?", help="Bankroll: 5000 OR A5000 B2000")
    parser.add_argument("strategy_b_bankroll", nargs="?", help="Strategy B bankroll (if using A/B format)")
    parser.add_argument("--live", action="store_true", help="Place real bets (default: dry run)")
    parser.add_argument("--stream", action="store_true", help="Enable stream mode (colorized output for Twitch)")
    
    args = parser.parse_args()
    
    # Handle control commands
    if args.command == "stop":
        stop_bot()
        return
    
    if args.command == "status":
        show_status()
        return
    
    if args.command == "start":
        if not args.date or not args.bankroll:
            print("❌ Usage: python3 HorseBot_Simple.py start <date> <bankroll> [--live]")
            print("   Example: python3 HorseBot_Simple.py start 2025-10-18 5000")
            print("   Or:      python3 HorseBot_Simple.py start 2025-10-18 A5000 B2000")
            return
        
        if is_running():
            print("⚠️  Bot is already running! Use 'stop' first.")
            return
        
        # Parse bankroll (supports A5000 B2000 format)
        bankroll_str = args.bankroll
        if args.strategy_b_bankroll:
            bankroll_str = f"{args.bankroll} {args.strategy_b_bankroll}"
        
        bankrolls = parse_bankroll_arg(bankroll_str)
        
        # Display bankroll info
        if None in bankrolls:
            print(f"🚀 Starting bot for {args.date} with £{bankrolls[None]} bankroll")
        else:
            print(f"🚀 Starting bot for {args.date} with strategy-specific bankrolls:")
            for strat, amount in bankrolls.items():
                print(f"   Strategy {strat}: £{amount}")
        
        if args.live:
            print("⚠️  LIVE MODE - Real bets will be placed!")
        else:
            print("🔍 DRY RUN mode - No real bets")
        
        if args.stream:
            print("🎬 STREAM MODE - Colorized output enabled for Twitch!")
        
        # Write PID and start
        write_pid()
        try:
            run_bot(args.date, bankrolls, args.live, args.stream)
        finally:
            # Clean up PID file on exit
            PID_FILE.unlink(missing_ok=True)
        return
    
    # Legacy mode: direct run
    if not args.date or not args.bankroll:
        print("\n🤖 GiddyUp HorseBot")
        print("=" * 50)
        print("\nCommands:")
        print("  python3 HorseBot_Simple.py start <date> <bankroll> [--live]")
        print("  python3 HorseBot_Simple.py stop")
        print("  python3 HorseBot_Simple.py status")
        print("\nLegacy mode:")
        print("  python3 HorseBot_Simple.py <date> <bankroll> [--live]")
        print("\nExamples:")
        print("  python3 HorseBot_Simple.py start 2025-10-18 5000")
        print("  python3 HorseBot_Simple.py 2025-10-18 5000 --live")
        print("")
        return
    
    # Legacy direct run
    run_bot(args.date, args.bankroll, args.live)

if __name__ == "__main__":
    main()

