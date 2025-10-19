#!/usr/bin/env python3
"""
Live Racing Results Monitor
============================
Continuously polls Sporting Life API and displays results in real-time.
Perfect for streaming!

Usage:
    python3 live_results_monitor.py
"""

import requests
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Set
import json

# ANSI Color codes for terminal
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Backgrounds
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_BLUE = '\033[44m'
    BG_YELLOW = '\033[43m'
    BG_MAGENTA = '\033[45m'

# API URL
API_URL = "https://www.sportinglife.com/api/horse-racing/v2/fast-results?countryGroups=UK,IRE"

# Track which races we've already displayed
displayed_races: Set[str] = set()

def clear_screen():
    """Clear the terminal screen."""
    print('\033[2J\033[H', end='')

def print_header():
    """Print the cool header banner."""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}                    🏇 LIVE RACING RESULTS MONITOR 🏇{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 80}{Colors.RESET}\n")
    
    now = datetime.now().strftime("%H:%M:%S")
    print(f"{Colors.BRIGHT_WHITE}⏰ Current Time: {Colors.BRIGHT_CYAN}{now}{Colors.RESET}")
    print(f"{Colors.BRIGHT_WHITE}🔄 Checking for new results every 30 seconds...{Colors.RESET}\n")

def print_race_result(race: Dict, is_new: bool = True):
    """Print a single race result with fancy formatting."""
    
    # Only print if status is RESULT or WEIGHEDIN
    if race.get('status') not in ['RESULT', 'WEIGHEDIN']:
        return
    
    course = race.get('courseName', 'Unknown')
    time_str = race.get('time', '??:??')
    race_name = race.get('name', 'Unknown Race')
    distance = race.get('distance', '?')
    country = race.get('country_group', 'UK')
    top_horses = race.get('top_horses', [])
    
    # Race key for tracking
    race_key = f"{course}_{time_str}"
    
    # Skip if already displayed (unless forcing new display)
    if not is_new and race_key in displayed_races:
        return
    
    # Mark as displayed
    displayed_races.add(race_key)
    
    # Print race header
    if is_new:
        print(f"\n{Colors.BOLD}{Colors.BG_GREEN}{Colors.BLACK} 🏁 NEW RESULT! {Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┏{'━' * 78}┓{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┃{Colors.RESET} {Colors.BOLD}{Colors.BRIGHT_YELLOW}{time_str}{Colors.RESET} - {Colors.BOLD}{Colors.BRIGHT_WHITE}{course}{Colors.RESET} {Colors.BRIGHT_CYAN}({country}){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┃{Colors.RESET} {Colors.BRIGHT_WHITE}{race_name[:74]}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┃{Colors.RESET} {Colors.BRIGHT_BLUE}Distance:{Colors.RESET} {distance}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┣{'━' * 78}┫{Colors.RESET}")
    
    # Print top horses (winner, 2nd, 3rd)
    if top_horses:
        for i, horse in enumerate(top_horses[:3], 1):
            horse_name = horse.get('horse_name', 'Unknown')
            odds = horse.get('odds', 'N/A')
            position = horse.get('position', i)
            is_fav = horse.get('favourite', False)
            
            # Position styling
            if position == 1:
                pos_color = Colors.BRIGHT_GREEN
                medal = "🥇"
                pos_bg = Colors.BG_GREEN
            elif position == 2:
                pos_color = Colors.BRIGHT_WHITE
                medal = "🥈"
                pos_bg = Colors.RESET
            elif position == 3:
                pos_color = Colors.BRIGHT_YELLOW
                medal = "🥉"
                pos_bg = Colors.RESET
            else:
                pos_color = Colors.BRIGHT_WHITE
                medal = "  "
                pos_bg = Colors.RESET
            
            fav_indicator = f"{Colors.BRIGHT_RED}⭐ FAV{Colors.RESET}" if is_fav else ""
            
            print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┃{Colors.RESET} {medal} {Colors.BOLD}{pos_color}{position}st{Colors.RESET}: {Colors.BOLD}{Colors.BRIGHT_WHITE}{horse_name:<35}{Colors.RESET} @ {Colors.BRIGHT_CYAN}{odds:<8}{Colors.RESET} {fav_indicator}")
        
        # Print winning jockey/trainer if available
        winning_jockeys = race.get('winning_jockeys', [])
        winning_trainers = race.get('winning_trainers', [])
        
        if winning_jockeys or winning_trainers:
            print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┣{'━' * 78}┫{Colors.RESET}")
            
            if winning_jockeys:
                jockey = winning_jockeys[0].get('name', 'Unknown')
                print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┃{Colors.RESET} {Colors.BRIGHT_BLUE}👤 Jockey:{Colors.RESET}  {Colors.BRIGHT_WHITE}{jockey}{Colors.RESET}")
            
            if winning_trainers:
                trainer = winning_trainers[0].get('name', 'Unknown')
                print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┃{Colors.RESET} {Colors.BRIGHT_BLUE}🎓 Trainer:{Colors.RESET} {Colors.BRIGHT_WHITE}{trainer}{Colors.RESET}")
        
        # Print forecast/tricast if available
        forecast = race.get('straight_forecast')
        tricast = race.get('tricast')
        
        if forecast or tricast:
            print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┣{'━' * 78}┫{Colors.RESET}")
            if forecast:
                print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┃{Colors.RESET} {Colors.BRIGHT_GREEN}💰 Forecast:{Colors.RESET} {Colors.BRIGHT_YELLOW}{forecast}{Colors.RESET}")
            if tricast:
                print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┃{Colors.RESET} {Colors.BRIGHT_GREEN}💰 Tricast:{Colors.RESET}  {Colors.BRIGHT_YELLOW}{tricast}{Colors.RESET}")
    else:
        print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┃{Colors.RESET} {Colors.YELLOW}⏳ Waiting for placings...{Colors.RESET}")
    
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}┗{'━' * 78}┛{Colors.RESET}")

def fetch_results() -> List[Dict]:
    """Fetch results from Sporting Life API."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}❌ Error fetching results: {e}{Colors.RESET}")
        return []

def print_summary(results: List[Dict]):
    """Print summary of today's racing."""
    total_races = len(results)
    finished_races = sum(1 for r in results if r.get('status') in ['RESULT', 'WEIGHEDIN'])
    off_races = sum(1 for r in results if r.get('status') == 'OFF')
    
    print(f"\n{Colors.BRIGHT_CYAN}{'─' * 80}{Colors.RESET}")
    print(f"{Colors.BRIGHT_WHITE}📊 Summary:{Colors.RESET} {Colors.BRIGHT_GREEN}{finished_races}{Colors.RESET} Finished | {Colors.BRIGHT_YELLOW}{off_races}{Colors.RESET} Running | {Colors.BRIGHT_BLUE}{total_races}{Colors.RESET} Total")
    print(f"{Colors.BRIGHT_CYAN}{'─' * 80}{Colors.RESET}")

def print_animation():
    """Print a cool racing animation."""
    horses = ["🐎", "🏇", "🐴"]
    for horse in horses:
        sys.stdout.write(f"\r{Colors.BRIGHT_YELLOW}{horse * 10}{Colors.RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    print("\r" + " " * 50 + "\r", end="")

def monitor_results():
    """Main monitoring loop."""
    print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}")
    print(r"""
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║   ██╗     ██╗██╗   ██╗███████╗    ██████╗ ███████╗███████╗██╗   ██╗    ║
    ║   ██║     ██║██║   ██║██╔════╝    ██╔══██╗██╔════╝██╔════╝██║   ██║    ║
    ║   ██║     ██║██║   ██║█████╗      ██████╔╝█████╗  ███████╗██║   ██║    ║
    ║   ██║     ██║╚██╗ ██╔╝██╔══╝      ██╔══██╗██╔══╝  ╚════██║██║   ██║    ║
    ║   ███████╗██║ ╚████╔╝ ███████╗    ██║  ██║███████╗███████║╚██████╔╝    ║
    ║   ╚══════╝╚═╝  ╚═══╝  ╚══════╝    ╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝     ║
    ║                                                                           ║
    ║                    🏇  M O N I T O R  🏇                                  ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    print(f"{Colors.RESET}")
    
    time.sleep(2)
    
    print(f"{Colors.BRIGHT_YELLOW}🚀 Starting monitor...{Colors.RESET}\n")
    time.sleep(1)
    
    last_result_count = 0
    check_count = 0
    
    try:
        while True:
            check_count += 1
            
            # Only print header on first run
            if check_count == 1:
                print_header()
            
            # Fetch results
            now = datetime.now().strftime("%H:%M:%S")
            print(f"\n{Colors.BRIGHT_CYAN}[{now}]{Colors.RESET} {Colors.BRIGHT_WHITE}🔍 Checking for results (Check #{check_count})...{Colors.RESET}")
            results = fetch_results()
            
            if not results:
                print(f"{Colors.BRIGHT_RED}⚠️  No results available yet{Colors.RESET}")
                print(f"{Colors.BRIGHT_WHITE}⏳ Waiting 30 seconds...{Colors.RESET}")
                time.sleep(30)
                continue
            
            # Filter for finished races
            finished_races = [r for r in results if r.get('status') in ['RESULT', 'WEIGHEDIN']]
            
            # Check for new results
            new_results = []
            for race in finished_races:
                race_key = f"{race.get('courseName')}_{race.get('time')}"
                if race_key not in displayed_races:
                    new_results.append(race)
            
            # Display new results with fanfare
            if new_results:
                print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}🎉 {len(new_results)} NEW RESULT(S)!{Colors.RESET}")
                print_animation()
                
                for race in new_results:
                    print_race_result(race, is_new=True)
                    time.sleep(0.5)  # Dramatic pause between results
            else:
                print(f"{Colors.BRIGHT_YELLOW}✓ Up to date - No new results{Colors.RESET}")
            
            # Summary
            print_summary(results)
            
            # Next check countdown
            print(f"\n{Colors.BRIGHT_WHITE}⏱️  Next check in: {Colors.RESET}", end="")
            for i in range(30, 0, -1):
                print(f"\r{Colors.BRIGHT_WHITE}⏱️  Next check in: {Colors.BRIGHT_CYAN}{i:2d}{Colors.RESET} seconds... ", end="")
                sys.stdout.flush()
                time.sleep(1)
            print()
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_RED}🛑 Monitor stopped by user{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═' * 80}{Colors.RESET}\n")
        print(f"{Colors.BRIGHT_WHITE}📊 Final Stats:{Colors.RESET}")
        print(f"   Total checks: {Colors.BRIGHT_CYAN}{check_count}{Colors.RESET}")
        print(f"   Races displayed: {Colors.BRIGHT_GREEN}{len(displayed_races)}{Colors.RESET}")
        print(f"\n{Colors.BRIGHT_GREEN}✅ Thanks for watching!{Colors.RESET}\n")
        sys.exit(0)

if __name__ == "__main__":
    monitor_results()

