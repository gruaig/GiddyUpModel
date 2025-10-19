#!/usr/bin/env python3
"""
Horse Back-Lay Trading Bot
===========================
Places paper bets on morning selections and tracks for profitable lay opportunities.

Strategy:
- Record morning expected prices (9-11 AM)
- Monitor price movements throughout the day
- Lay (cash out) when:
  * Price shortens significantly (odds drop 10-20% below expected)
  * Criteria met but outside T-60 window
  * T-15 before race if profitable
- Track all trades in daily backlay CSV

Usage:
    python3 HorseBackLayBot.py start 2025-10-19 5000
    python3 HorseBackLayBot.py stop
"""

import csv
import time
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

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

# Telegram integration
try:
    from telegram_bot import send_telegram_message, TELEGRAM_ENABLED
except ImportError:
    TELEGRAM_ENABLED = False

# Constants
BST = pytz.timezone("Europe/London")
RECHECK_INTERVAL = 5  # Check every 5 seconds
LOG_DIR = Path(__file__).parent / "strategies" / "logs" / "backlay_trades"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Trading parameters
MIN_PROFIT_PERCENTAGE = 5.0  # Minimum 5% profit to close trade
PRICE_DROP_THRESHOLD = 10.0  # Lay when price drops 10% or more
T_MINUS_CASHOUT = 15  # Cash out at T-15 if profitable

def ts():
    """Timestamp in UK time."""
    return datetime.now(BST).strftime("%Y-%m-%d %H:%M:%S")

def log(msg, level="INFO"):
    """Log with timestamp and color."""
    colors = {
        "INFO": "\033[36m",      # Cyan
        "SUCCESS": "\033[92m",   # Green
        "WARNING": "\033[93m",   # Yellow
        "ERROR": "\033[91m",     # Red
        "BET": "\033[95m"        # Magenta
    }
    reset = "\033[0m"
    icons = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "BET": "💰"
    }
    print(f"[{ts()}] {icons.get(level, '•')} {colors.get(level, '')}{msg}{reset}")

def get_selections(date: str, bankroll: float) -> List[Dict]:
    """Load morning selections."""
    log(f"Loading morning selections for {date}...")
    
    script = Path(__file__).parent / "strategies" / "RUN_BOTH_STRATEGIES.sh"
    
    try:
        subprocess.run(
            [str(script), date, str(int(bankroll))],
            capture_output=True,
            text=True,
            cwd=script.parent,
            timeout=60
        )
        
        csv_file = script.parent / "logs" / "daily_bets" / "betting_log_2025.csv"
        selections = []
        
        with csv_file.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["date"] == date:
                    # Fix time offset
                    db_time = datetime.strptime(row["time"], "%H:%M")
                    corrected_time = db_time + timedelta(hours=1)
                    row["time"] = corrected_time.strftime("%H:%M")
                    row["original_db_time"] = db_time.strftime("%H:%M")
                    selections.append(row)
        
        log(f"Loaded {len(selections)} morning selections", "SUCCESS")
        return selections
        
    except Exception as e:
        log(f"Error loading selections: {e}", "ERROR")
        return []

class Betfair:
    """Betfair API wrapper."""
    
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.client = None
        
    def login(self):
        """Login to Betfair."""
        if self.dry_run:
            log("🟢 DRY RUN MODE - No real bets will be placed")
            return
        
        try:
            certs = Path(__file__).parent / "betfair_certs"
            self.client = APIClient(
                username=os.getenv("BF_USERNAME"),
                password=os.getenv("BF_PASSWORD"),
                app_key=os.getenv("BF_APP_KEY"),
                certs=certs
            )
            self.client.login()
            log("Logged into Betfair", "SUCCESS")
        except Exception as e:
            log(f"Betfair login failed: {e}", "ERROR")
            sys.exit(1)
    
    def logout(self):
        """Logout from Betfair."""
        if self.client:
            self.client.logout()
            log("Logged out of Betfair")
    
    def find_market(self, horse: str, course: str, race_time: str):
        """Find market for a horse."""
        # Implementation similar to HorseBot_Simple.py
        # For brevity, returning mock data in dry run
        if self.dry_run:
            return ("mock_market_id", "mock_selection_id")
        # ... actual implementation ...
        return None
    
    def get_odds(self, market_id: str, selection_id: str) -> Optional[float]:
        """Get current back odds for a selection."""
        if self.dry_run:
            # Return mock odds for testing
            import random
            return round(random.uniform(5.0, 15.0), 2)
        
        try:
            book = self.client.betting.list_market_book(
                market_ids=[market_id],
                price_projection=price_projection(
                    price_data=["EX_BEST_OFFERS"]
                )
            )
            
            if book and book[0].runners:
                for runner in book[0].runners:
                    if str(runner.selection_id) == str(selection_id):
                        if runner.ex and runner.ex.available_to_back:
                            return runner.ex.available_to_back[0].price
            return None
        except Exception as e:
            log(f"Error getting odds: {e}", "WARNING")
            return None

def calculate_lay_profit(back_stake: float, back_odds: float, lay_odds: float) -> float:
    """
    Calculate profit from back-to-lay trade.
    
    Args:
        back_stake: Initial back stake
        back_odds: Odds we backed at
        lay_odds: Odds we're laying at
        
    Returns:
        Profit (positive if profitable, negative if loss)
    """
    # Back liability
    back_liability = back_stake
    back_return = back_stake * back_odds
    
    # Lay stake (to match back return)
    lay_stake = back_return / lay_odds
    lay_liability = lay_stake * (lay_odds - 1)
    
    # Profit calculation
    # If horse wins: we win back, lose lay = back_return - back_stake - lay_liability
    # If horse loses: we lose back, win lay = lay_stake - back_stake
    
    # Green up (same profit both outcomes)
    profit_if_wins = back_return - back_stake - lay_liability
    profit_if_loses = lay_stake - back_stake
    
    # Return average profit (or minimum to be conservative)
    return min(profit_if_wins, profit_if_loses)

def should_lay_now(back_odds: float, current_odds: float, minutes_to_off: float) -> tuple[bool, str, float]:
    """
    Determine if we should lay now.
    
    Returns:
        (should_lay, reason, profit_percentage)
    """
    # Calculate potential profit
    profit_pct = ((back_odds - current_odds) / back_odds) * 100
    
    # Reason 1: Price shortened significantly (10%+ drop)
    if current_odds <= back_odds * (1 - PRICE_DROP_THRESHOLD / 100):
        return True, f"Price shortened {profit_pct:.1f}%", profit_pct
    
    # Reason 2: T-15 and any profit available
    if minutes_to_off <= T_MINUS_CASHOUT and current_odds < back_odds:
        return True, f"T-{int(minutes_to_off)} cash out", profit_pct
    
    # Reason 3: Significant profit available (20%+)
    if profit_pct >= 20.0:
        return True, f"Large profit available {profit_pct:.1f}%", profit_pct
    
    return False, "No lay opportunity", profit_pct

def run_backlay_bot(date: str, bankroll: float, dry_run: bool = True):
    """Main back-lay trading bot."""
    
    log("=" * 80)
    log(f"🏇 HORSE BACK-LAY TRADING BOT - {date}")
    log("=" * 80)
    log(f"Bankroll: £{bankroll:.0f}")
    log(f"Mode: {'🟢 DRY RUN (Paper Trading)' if dry_run else '🔴 LIVE TRADING'}")
    log("")
    
    # Load selections
    selections = get_selections(date, bankroll)
    if not selections:
        log("No selections - exiting", "WARNING")
        return
    
    # Setup Betfair
    betfair = Betfair(dry_run=dry_run)
    betfair.login()
    
    # Create daily log
    backlay_log = LOG_DIR / f"{date}_backlay.csv"
    if not backlay_log.exists():
        with backlay_log.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "race_time", "course", "horse", "strategy",
                "back_odds", "back_stake", "lay_odds", "lay_stake",
                "profit_gbp", "profit_pct", "reason", "status"
            ])
    
    log(f"📊 Tracking {len(selections)} morning selections for back-lay opportunities")
    log("")
    
    # Track all positions
    positions = {}  # key: horse -> position data
    
    # Record initial "backs" (paper trades)
    for sel in selections:
        key = f"{sel['time']}_{sel['horse']}"
        positions[key] = {
            'selection': sel,
            'back_odds': float(sel['odds']),
            'back_stake': float(sel['stake_gbp']),
            'backed_at': datetime.now(BST),
            'laid': False,
            'best_odds_seen': float(sel['odds']),
            'market_id': None,
            'selection_id': None
        }
        
        log(f"📝 PAPER BACK: {sel['horse']} @ {sel['course']}", "BET")
        log(f"   Race: {sel['time']} | Odds: {sel['odds']} | Stake: £{sel['stake_gbp']}")
    
    log("")
    log("🔍 Now monitoring for lay opportunities...")
    log("")
    
    try:
        # Get last race time
        last_time = max(datetime.strptime(s["time"], "%H:%M") for s in selections)
        today = datetime.now(BST).date()
        end_time = BST.localize(datetime.combine(today, last_time.time())) + timedelta(minutes=30)
        
        while datetime.now(BST) < end_time:
            now = datetime.now(BST)
            
            for key, pos in positions.items():
                # Skip if already laid
                if pos['laid']:
                    continue
                
                sel = pos['selection']
                race_dt = BST.localize(
                    datetime.combine(
                        today,
                        datetime.strptime(sel["time"], "%H:%M").time()
                    )
                )
                
                minutes_to_off = (race_dt - now).total_seconds() / 60
                
                # Skip if race finished
                if minutes_to_off < -5:
                    pos['laid'] = True
                    log(f"⏰ Race finished: {sel['horse']} @ {sel['course']}")
                    continue
                
                # Skip if too early (before T-120)
                if minutes_to_off > 120:
                    continue
                
                # Get market if not cached
                if not pos['market_id']:
                    market_info = betfair.find_market(sel['horse'], sel['course'], sel['time'])
                    if market_info:
                        pos['market_id'], pos['selection_id'] = market_info
                    else:
                        continue
                
                # Get current odds
                current_odds = betfair.get_odds(pos['market_id'], pos['selection_id'])
                if not current_odds:
                    continue
                
                # Track best odds
                if current_odds < pos['best_odds_seen']:
                    pos['best_odds_seen'] = current_odds
                
                # Check if we should lay
                should_lay, reason, profit_pct = should_lay_now(
                    pos['back_odds'],
                    current_odds,
                    minutes_to_off
                )
                
                if should_lay:
                    # Calculate lay details
                    back_stake = pos['back_stake']
                    back_odds = pos['back_odds']
                    lay_odds = current_odds
                    
                    profit = calculate_lay_profit(back_stake, back_odds, lay_odds)
                    
                    # Only lay if profitable
                    if profit > 0:
                        # Calculate lay stake
                        back_return = back_stake * back_odds
                        lay_stake = back_return / lay_odds
                        
                        log("")
                        log("=" * 60, "SUCCESS")
                        log(f"💰 LAY OPPORTUNITY: {sel['horse']} @ {sel['course']}", "SUCCESS")
                        log(f"   Race: {sel['time']} (T-{int(minutes_to_off)})", "SUCCESS")
                        log(f"   Backed: £{back_stake:.2f} @ {back_odds:.2f}", "SUCCESS")
                        log(f"   Laying: £{lay_stake:.2f} @ {lay_odds:.2f}", "SUCCESS")
                        log(f"   Profit: £{profit:.2f} ({profit_pct:.1f}%)", "SUCCESS")
                        log(f"   Reason: {reason}", "SUCCESS")
                        log("=" * 60, "SUCCESS")
                        log("")
                        
                        # Log to CSV
                        with backlay_log.open("a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                ts(), sel['time'], sel['course'], sel['horse'],
                                sel['strategy'], back_odds, back_stake,
                                lay_odds, f"{lay_stake:.2f}", f"{profit:.2f}",
                                f"{profit_pct:.1f}", reason, "COMPLETED"
                            ])
                        
                        # Mark as laid
                        pos['laid'] = True
                        
                        # Send Telegram notification
                        if TELEGRAM_ENABLED:
                            try:
                                message = f"""💰 <b>BACK-LAY PROFIT</b>

🏇 {sel['horse']} @ {sel['course']}
⏰ Race: {sel['time']} (T-{int(minutes_to_off)})

📊 <b>Trade Details:</b>
Back: £{back_stake:.2f} @ {back_odds:.2f}
Lay: £{lay_stake:.2f} @ {lay_odds:.2f}

💵 <b>Profit: £{profit:.2f} ({profit_pct:.1f}%)</b>

Reason: {reason}

#BackLay #Trading #Profit"""
                                send_telegram_message(message)
                            except Exception as e:
                                log(f"Telegram error: {e}", "WARNING")
            
            # Sleep
            time.sleep(RECHECK_INTERVAL)
        
        # Summary
        log("")
        log("=" * 80)
        log("SESSION COMPLETE")
        log("=" * 80)
        
        total_trades = sum(1 for p in positions.values() if p['laid'])
        log(f"Total trades completed: {total_trades}/{len(positions)}")
        log(f"Trade log: {backlay_log}")
        
        # Calculate total profit
        total_profit = 0.0
        with backlay_log.open('r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('profit_gbp'):
                    total_profit += float(row['profit_gbp'])
        
        log(f"Total P&L: £{total_profit:+.2f}")
        log("")
        
    finally:
        betfair.logout()

def main():
    parser = argparse.ArgumentParser(description="Horse Back-Lay Trading Bot")
    parser.add_argument("command", choices=["start", "stop", "status"], help="Command")
    parser.add_argument("date", nargs="?", help="Date (YYYY-MM-DD)")
    parser.add_argument("bankroll", type=float, nargs="?", help="Bankroll in GBP")
    parser.add_argument("--live", action="store_true", help="Live trading (default: dry run)")
    
    args = parser.parse_args()
    
    if args.command == "start":
        if not args.date or not args.bankroll:
            print("Usage: python3 HorseBackLayBot.py start YYYY-MM-DD BANKROLL [--live]")
            sys.exit(1)
        
        run_backlay_bot(args.date, args.bankroll, dry_run=not args.live)
    
    elif args.command == "stop":
        print("Stop not yet implemented (use Ctrl+C)")
    
    elif args.command == "status":
        print("Status not yet implemented")

if __name__ == "__main__":
    main()

