#!/usr/bin/env python3
"""
Auto Results Monitor

Monitors races and automatically checks results 5 minutes after each race finishes.
Sends real-time win/loss notifications to stream, Telegram, and Twitch.

Can be run standalone or integrated into HorseBot.
"""

import time
import csv
from pathlib import Path
from datetime import datetime, timedelta
import pytz
from typing import List, Dict

from results_checker import fetch_results, check_horse_position, calculate_pnl

# Import notifications
try:
    from telegram_bot import send_result as telegram_result, TELEGRAM_ENABLED
except:
    TELEGRAM_ENABLED = False

try:
    from twitch_bot import send_win, send_loss, TWITCH_ENABLED
except:
    TWITCH_ENABLED = False

try:
    from stream_mode import win_announcement, loss_announcement, Colors, STREAM_MODE_AVAILABLE
    STREAM_MODE = True
except:
    STREAM_MODE_AVAILABLE = False
    STREAM_MODE = False


BST = pytz.timezone("Europe/London")


def monitor_results(date: str, actions_csv: Path, check_interval: int = 60):
    """
    Monitor race results and update as they become available.
    
    Args:
        date: Date to monitor (YYYY-MM-DD)
        actions_csv: Path to bot actions CSV
        check_interval: How often to check API (seconds)
    """
    print("")
    print("=" * 80)
    print("🔍 RESULTS MONITOR ACTIVE")
    print("=" * 80)
    print(f"Checking for results every {check_interval}s...")
    print("Results will be checked 5 minutes after each race finishes")
    print("")
    
    checked_races = set()  # Track which races we've already checked
    
    # Load all bets
    bets = []
    with actions_csv.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('bet_placed') in ['DRY_RUN', 'EXECUTED']:
                bets.append(row)
    
    while True:
        now = datetime.now(BST)
        
        # Check each bet
        for bet in bets:
            race_key = f"{bet['race_time']}_{bet['course']}_{bet['horse']}"
            
            # Skip if already checked
            if race_key in checked_races:
                continue
            
            # Skip if already has result
            if bet.get('result') in ['WIN', 'LOSS']:
                checked_races.add(race_key)
                continue
            
            # Parse race time
            try:
                race_time_str = f"{date} {bet['race_time']}"
                race_dt = BST.localize(datetime.strptime(race_time_str, "%Y-%m-%d %H:%M"))
                
                # Check if race finished + 5 minutes
                time_since_race = (now - race_dt).total_seconds() / 60
                
                if time_since_race >= 5:
                    # Time to check result!
                    print(f"⏰ Checking result for {bet['horse']} @ {bet['course']} ({bet['race_time']})...")
                    
                    # Fetch latest results
                    race_results = fetch_results(date)
                    
                    # Check result
                    result = check_horse_position(
                        bet['horse'],
                        bet['course'],
                        bet['race_time'],
                        race_results
                    )
                    
                    if result:
                        # Calculate P&L
                        odds = float(bet.get('actual_odds', bet.get('expected_odds', 0)))
                        stake = float(bet.get('stake', 0))
                        pnl = calculate_pnl(result, odds, stake)
                        
                        # Update CSV
                        update_bet_result(actions_csv, bet['horse'], result, pnl)
                        
                        # Announce result
                        if result == "WIN":
                            print(f"{Colors.BRIGHT_GREEN if STREAM_MODE_AVAILABLE else ''}🎉 WINNER! {bet['horse']} @ {bet['course']}")
                            print(f"   P&L: £{pnl:+.2f}{Colors.RESET if STREAM_MODE_AVAILABLE else ''}")
                            
                            if STREAM_MODE and STREAM_MODE_AVAILABLE:
                                print(win_announcement(bet['horse'], bet['course'], pnl))
                            
                            # Send notifications
                            if TELEGRAM_ENABLED:
                                try:
                                    telegram_result(
                                        horse=bet['horse'],
                                        course=bet['course'],
                                        race_time=bet['race_time'],
                                        result=result,
                                        odds=odds,
                                        stake=stake,
                                        pnl=pnl,
                                        strategy=bet.get('strategy', 'Unknown')
                                    )
                                except: pass
                            
                            if TWITCH_ENABLED:
                                try:
                                    send_win(bet['horse'], bet['course'], pnl)
                                except: pass
                        else:
                            print(f"{Colors.BRIGHT_RED if STREAM_MODE_AVAILABLE else ''}😔 Lost: {bet['horse']} @ {bet['course']}")
                            print(f"   P&L: £{pnl:.2f}{Colors.RESET if STREAM_MODE_AVAILABLE else ''}")
                            
                            if STREAM_MODE and STREAM_MODE_AVAILABLE:
                                print(loss_announcement(bet['horse'], bet['course'], pnl))
                            
                            # Send notifications
                            if TELEGRAM_ENABLED:
                                try:
                                    telegram_result(
                                        horse=bet['horse'],
                                        course=bet['course'],
                                        race_time=bet['race_time'],
                                        result=result,
                                        odds=odds,
                                        stake=stake,
                                        pnl=pnl,
                                        strategy=bet.get('strategy', 'Unknown')
                                    )
                                except: pass
                            
                            if TWITCH_ENABLED:
                                try:
                                    send_loss(bet['horse'], bet['course'], pnl)
                                except: pass
                        
                        print("")
                        checked_races.add(race_key)
                    else:
                        print(f"   ⏳ Result not available yet...")
                        
            except Exception as e:
                print(f"Error checking {bet['horse']}: {e}")
                checked_races.add(race_key)  # Don't retry failed checks
        
        # Check if all done
        if len(checked_races) >= len(bets):
            print("=" * 80)
            print("✅ All results checked!")
            print("=" * 80)
            break
        
        # Sleep before next check
        time.sleep(check_interval)


def update_bet_result(csv_file: Path, horse_name: str, result: str, pnl: float):
    """Update a single bet result in CSV."""
    from results_checker import normalize_horse_name
    
    # Read all rows
    rows = []
    with csv_file.open('r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    
    # Update matching row
    for row in rows:
        if normalize_horse_name(row['horse']) == normalize_horse_name(horse_name):
            row['result'] = result
            row['pnl_gbp'] = str(pnl)
            break
    
    # Write back
    with csv_file.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 auto_results_monitor.py <date>")
        sys.exit(1)
    
    date = sys.argv[1]
    actions_csv = Path(__file__).parent / "strategies" / "logs" / "automated_bets" / f"bot_actions_{date}.csv"
    
    if not actions_csv.exists():
        print(f"❌ No actions file found: {actions_csv}")
        sys.exit(1)
    
    monitor_results(date, actions_csv)

