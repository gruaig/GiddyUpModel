#!/usr/bin/env python3
"""
Automatic Results Checker

Fetches race results from Sporting Life API and automatically updates
your betting logs with WIN/LOSS results.

API: https://www.sportinglife.com/api/horse-racing/v2/fast-results?countryGroups=UK,IRE

Usage:
    python3 results_checker.py 2025-10-18
    
Or import and use programmatically:
    from results_checker import check_results_for_date
"""

import sys
import csv
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re


# API endpoint
RESULTS_API = "https://www.sportinglife.com/api/horse-racing/v2/fast-results?countryGroups=UK,IRE"


def normalize_horse_name(name: str) -> str:
    """Normalize horse name for matching."""
    # Remove country codes
    name = re.sub(r'\s*\((GB|IRE|FR|USA|GER)\)$', '', name)
    # Remove extra whitespace
    name = ' '.join(name.split())
    # Lowercase for comparison
    return name.lower()


def normalize_course_name(name: str) -> str:
    """Normalize course name for matching."""
    return name.lower().strip()


def fetch_results(date: str) -> List[Dict]:
    """
    Fetch race results from Sporting Life API.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        List of race result dictionaries
    """
    try:
        response = requests.get(RESULTS_API, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        
        # Filter for specific date
        date_results = [r for r in results if r.get('date') == date]
        
        return date_results
        
    except Exception as e:
        print(f"❌ Error fetching results: {e}")
        return []


def check_horse_position(horse_name: str, course_name: str, race_time: str, 
                        race_results: List[Dict]) -> Optional[str]:
    """
    Check if a horse won, placed, or lost.
    
    Args:
        horse_name: Name of horse to check
        course_name: Course name
        race_time: Race time (HH:MM format)
        race_results: List of race results from API
        
    Returns:
        "WIN", "PLACE", "LOSS", or None if not found
    """
    horse_norm = normalize_horse_name(horse_name)
    course_norm = normalize_course_name(course_name)
    
    # Find matching race
    for race in race_results:
        race_course = normalize_course_name(race.get('courseName', ''))
        race_time_api = race.get('time', '')
        
        # Match course and time
        if course_norm in race_course or race_course in course_norm:
            # Time might be off by 1 hour or have slight differences
            if race_time_api == race_time or \
               abs_time_diff(race_time, race_time_api) <= 60:
                
                # Check if results are available (RESULT or WEIGHEDIN)
                if race.get('status') not in ['RESULT', 'WEIGHEDIN']:
                    continue
                
                # Check top horses for our horse
                top_horses = race.get('top_horses', [])
                
                for horse in top_horses:
                    horse_name_api = normalize_horse_name(horse.get('horse_name', ''))
                    position = horse.get('position', 999)
                    
                    if horse_norm == horse_name_api or \
                       horse_norm in horse_name_api or \
                       horse_name_api in horse_norm:
                        
                        if position == 1:
                            return "WIN"
                        elif position <= 3:  # Placed (but we only care about WIN for betting)
                            return "LOSS"  # Not a win = loss for us
                        else:
                            return "LOSS"
                
                # If we got here, horse ran but not in top positions
                return "LOSS"
    
    return None  # Race not found or results not available yet


def abs_time_diff(time1: str, time2: str) -> int:
    """Calculate absolute difference in minutes between two HH:MM times."""
    try:
        h1, m1 = map(int, time1.split(':'))
        h2, m2 = map(int, time2.split(':'))
        
        mins1 = h1 * 60 + m1
        mins2 = h2 * 60 + m2
        
        return abs(mins1 - mins2)
    except:
        return 999


def calculate_pnl(result: str, odds: float, stake: float) -> float:
    """Calculate P&L for a bet."""
    if result == "WIN":
        # Profit after 2% commission
        gross_return = odds * stake
        commission = gross_return * 0.02
        net_profit = gross_return - stake - commission
        return round(net_profit, 2)
    else:  # LOSS
        return round(-stake, 2)


def update_csv_with_results(csv_file: Path, results_data: List[Tuple[str, str, str, float]]):
    """
    Update CSV file with results.
    
    Args:
        csv_file: Path to CSV file
        results_data: List of (horse, result, pnl_str, pnl_float) tuples
    """
    # Read all rows
    rows = []
    with csv_file.open('r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    
    # Update rows with results
    for horse, result, pnl_str, pnl_float in results_data:
        for row in rows:
            if normalize_horse_name(row['horse']) == normalize_horse_name(horse):
                row['result'] = result
                row['pnl_gbp'] = pnl_str
    
    # Write back
    with csv_file.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def check_results_for_date(date: str, send_notifications: bool = True) -> Dict:
    """
    Check results for all bets on a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        send_notifications: If True, send Telegram/Twitch notifications
        
    Returns:
        Dictionary with summary stats
    """
    print(f"🔍 Checking results for {date}...")
    print("")
    
    # File paths
    base_dir = Path(__file__).parent
    actions_csv = base_dir / "strategies" / "logs" / "automated_bets" / f"bot_actions_{date}.csv"
    
    if not actions_csv.exists():
        print(f"❌ No actions file found: {actions_csv}")
        return {}
    
    # Fetch results from API
    print("📡 Fetching results from Sporting Life API...")
    race_results = fetch_results(date)
    
    if not race_results:
        print(f"⚠️  No results found for {date} (races may not be finished yet)")
        return {}
    
    print(f"✅ Found {len(race_results)} race results")
    print("")
    
    # Read bets from CSV
    results_to_update = []
    wins = 0
    losses = 0
    pending = 0
    total_pnl = 0.0
    
    # Import notification functions
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
    except:
        STREAM_MODE_AVAILABLE = False
    
    with actions_csv.open('r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        for row in rows:
            # Only check bets that were actually placed
            if row.get('bet_placed') not in ['DRY_RUN', 'EXECUTED', 'YES']:
                continue
            
            # Skip if already has result
            if row.get('result') in ['WIN', 'LOSS']:
                result = row['result']
                pnl = float(row.get('pnl_gbp', 0))
                
                if result == 'WIN':
                    wins += 1
                    total_pnl += pnl
                else:
                    losses += 1
                    total_pnl += pnl
                
                continue
            
            # Check result
            horse = row['horse']
            course = row['course']
            race_time = row['race_time']
            
            result = check_horse_position(horse, course, race_time, race_results)
            
            if result:
                # Calculate P&L
                odds = float(row.get('actual_odds', row.get('expected_odds', 0)))
                stake = float(row.get('stake', 0))
                pnl = calculate_pnl(result, odds, stake)
                
                # Update tracking
                if result == "WIN":
                    wins += 1
                    emoji = "🎉"
                    color = Colors.BRIGHT_GREEN if STREAM_MODE_AVAILABLE else ""
                    reset = Colors.RESET if STREAM_MODE_AVAILABLE else ""
                else:
                    losses += 1
                    emoji = "😔"
                    color = Colors.BRIGHT_RED if STREAM_MODE_AVAILABLE else ""
                    reset = Colors.RESET if STREAM_MODE_AVAILABLE else ""
                
                total_pnl += pnl
                
                # Print result
                print(f"{color}{emoji} {result}: {horse} @ {course} ({race_time})")
                print(f"   P&L: £{pnl:+.2f}{reset}")
                print("")
                
                # Stream mode announcement
                if STREAM_MODE_AVAILABLE:
                    if result == "WIN":
                        print(win_announcement(horse, course, pnl))
                    else:
                        print(loss_announcement(horse, course, pnl))
                
                # Store for CSV update
                results_to_update.append((horse, result, str(pnl), pnl))
                
                # Send notifications
                if send_notifications:
                    if TELEGRAM_ENABLED:
                        try:
                            telegram_result(
                                horse=horse,
                                course=course,
                                race_time=race_time,
                                result=result,
                                odds=odds,
                                stake=stake,
                                pnl=pnl,
                                strategy=row.get('strategy', 'Unknown')
                            )
                        except Exception as e:
                            print(f"Telegram error: {e}")
                    
                    if TWITCH_ENABLED:
                        try:
                            if result == "WIN":
                                send_win(horse, course, pnl)
                            else:
                                send_loss(horse, course, pnl)
                        except Exception as e:
                            print(f"Twitch error: {e}")
            else:
                pending += 1
                print(f"⏳ PENDING: {horse} @ {course} ({race_time})")
                print(f"   Race not found or results not available yet")
                print("")
    
    # Update CSV file
    if results_to_update:
        print(f"💾 Updating CSV with {len(results_to_update)} result(s)...")
        update_csv_with_results(actions_csv, results_to_update)
        print("✅ CSV updated")
        print("")
    
    # Summary
    print("=" * 80)
    print(f"📊 RESULTS SUMMARY FOR {date}")
    print("=" * 80)
    print(f"  Wins: {wins}")
    print(f"  Losses: {losses}")
    print(f"  Pending: {pending}")
    print(f"  Total P&L: £{total_pnl:+.2f}")
    
    if wins + losses > 0:
        win_rate = (wins / (wins + losses)) * 100
        print(f"  Win Rate: {win_rate:.1f}%")
    
    print("=" * 80)
    print("")
    
    return {
        'wins': wins,
        'losses': losses,
        'pending': pending,
        'total_pnl': total_pnl,
        'results_updated': len(results_to_update)
    }


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python3 results_checker.py <date>")
        print("Example: python3 results_checker.py 2025-10-18\n")
        sys.exit(1)
    
    date = sys.argv[1]
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    summary = check_results_for_date(date)
    
    if summary.get('results_updated', 0) > 0:
        print("💡 Next steps:")
        print(f"   1. Review: cat strategies/logs/automated_bets/bot_actions_{date}.csv")
        print(f"   2. Generate report: python3 generate_betting_report.py {date}")
        print(f"   3. Generate tweets: python3 generate_result_tweets.py {date}")
        print("")


if __name__ == "__main__":
    main()

