#!/usr/bin/env python3
"""
Show Daily P&L
==============
Display comprehensive P&L report for a specific date from the database.

Usage:
    python3 show_daily_pnl.py                  # Today's P&L
    python3 show_daily_pnl.py 2025-10-20       # Specific date
    python3 show_daily_pnl.py --telegram       # Also post to Telegram
"""

import sys
from datetime import date as date_module
from utilities.db_tracker import BotTracker

# ANSI Colors
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'

def format_currency(value):
    """Format currency with color based on positive/negative."""
    if value is None:
        return "£0.00"
    
    if value > 0:
        return f"{Colors.GREEN}+£{value:.2f}{Colors.RESET}"
    elif value < 0:
        return f"{Colors.RED}£{value:.2f}{Colors.RESET}"
    else:
        return f"£{value:.2f}"

def show_daily_pnl(date_str: str, post_to_telegram: bool = False):
    """Show daily P&L report."""
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}              📊 DAILY P&L REPORT - {date_str} 📊{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 80}{Colors.RESET}\n")
    
    tracker = BotTracker('postgresql://postgres:password@localhost/giddyup')
    
    try:
        # Get daily summary
        pnl = tracker.get_daily_pnl(date_str)
        
        if not pnl:
            print(f"{Colors.RED}❌ No data found for {date_str}{Colors.RESET}")
            print(f"\nDid you run the bot on this date?\n")
            return
        
        # Header
        print(f"{Colors.BOLD}🏇 Bot Type:{Colors.RESET} {pnl['bot_type']}")
        print(f"{Colors.BOLD}📅 Date:{Colors.RESET} {pnl['date']}")
        print(f"{Colors.BOLD}🎮 Mode:{Colors.RESET} {pnl['mode']}")
        print()
        
        # Selections & Bets
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}📋 BETTING ACTIVITY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}")
        print(f"  Total Selections: {Colors.CYAN}{pnl['total_selections'] or 0}{Colors.RESET}")
        print(f"  Bets Placed: {Colors.GREEN}{pnl['bets_placed'] or 0}{Colors.RESET}")
        print(f"  Bets Skipped: {Colors.YELLOW}{pnl['bets_skipped'] or 0}{Colors.RESET}")
        print()
        
        # Results
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}🎯 RESULTS{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}")
        
        wins = pnl.get('wins') or 0
        losses = pnl.get('losses') or 0
        total_decided = wins + losses
        
        if total_decided > 0:
            win_rate = (wins / total_decided) * 100
            print(f"  Winners: {Colors.GREEN}{wins}{Colors.RESET}")
            print(f"  Losers: {Colors.RED}{losses}{Colors.RESET}")
            print(f"  Win Rate: {Colors.CYAN}{win_rate:.1f}%{Colors.RESET}")
        else:
            print(f"  {Colors.YELLOW}⏳ No results yet (races may still be running){Colors.RESET}")
        print()
        
        # Financial Summary
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}💰 FINANCIAL SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}")
        
        total_staked = pnl.get('total_staked') or 0
        net_pnl = pnl.get('net_pnl') or 0
        roi = pnl.get('roi_percentage') or 0
        
        print(f"  Total Staked: £{total_staked:.2f}")
        print(f"  Net P&L: {format_currency(net_pnl)}")
        
        if roi > 0:
            print(f"  ROI: {Colors.GREEN}{roi:.2f}%{Colors.RESET}")
        elif roi < 0:
            print(f"  ROI: {Colors.RED}{roi:.2f}%{Colors.RESET}")
        else:
            print(f"  ROI: {roi:.2f}%")
        
        print()
        
        # Get bet details
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}📝 BET DETAILS{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}\n")
        
        bets = tracker.get_bet_details(date_str)
        
        if bets:
            # Group by decision
            placed_bets = [b for b in bets if b.get('decision') == 'PLACED']
            skipped_bets = [b for b in bets if b.get('decision') == 'SKIPPED']
            
            # Show placed bets with results
            if placed_bets:
                print(f"{Colors.BOLD}{Colors.GREEN}✅ BETS PLACED ({len(placed_bets)}):{Colors.RESET}\n")
                
                for bet in placed_bets:
                    result = bet.get('result', 'PENDING')
                    pnl_value = bet.get('net_pnl')
                    
                    if result == 'WIN':
                        emoji = "🏆"
                        color = Colors.GREEN
                    elif result == 'LOSS':
                        emoji = "❌"
                        color = Colors.RED
                    else:
                        emoji = "⏳"
                        color = Colors.YELLOW
                    
                    print(f"  {emoji} {bet['race_time']} {bet['course']} - {color}{bet['horse']}{Colors.RESET}")
                    print(f"     Strategy: {bet['strategy']} | Odds: {bet['actual_odds']} | Stake: £{bet['stake_gbp']}")
                    
                    if result != 'PENDING' and pnl_value is not None:
                        print(f"     Result: {result} | P&L: {format_currency(pnl_value)}")
                    elif result == 'PENDING':
                        print(f"     Result: {Colors.YELLOW}⏳ Pending{Colors.RESET}")
                    
                    print()
            
            # Show skipped bets summary
            if skipped_bets:
                print(f"{Colors.BOLD}{Colors.YELLOW}⏭️  BETS SKIPPED ({len(skipped_bets)}):{Colors.RESET}")
                print(f"   (Use --verbose to see details)\n")
        else:
            print(f"  {Colors.YELLOW}No bets found for this date{Colors.RESET}\n")
        
        # Get Telegram activity
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}📱 TELEGRAM ACTIVITY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'─' * 80}{Colors.RESET}\n")
        
        telegram_activity = tracker.get_telegram_activity(date_str)
        
        if telegram_activity:
            for activity in telegram_activity:
                notif_type = activity['notification_type']
                count = activity['count']
                successful = activity['successful']
                failed = activity['failed']
                
                status = f"{Colors.GREEN}{successful}✓{Colors.RESET}"
                if failed > 0:
                    status += f" / {Colors.RED}{failed}✗{Colors.RESET}"
                
                print(f"  {notif_type:20s}: {count:2d} sent ({status})")
        else:
            print(f"  {Colors.YELLOW}No Telegram notifications sent{Colors.RESET}")
        
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 80}{Colors.RESET}\n")
        
        # Post to Telegram if requested
        if post_to_telegram and net_pnl != 0:
            from integrations.telegram_bot import send_telegram_message
            
            result_emoji = "📈" if net_pnl > 0 else "📉"
            pnl_str = f"+£{net_pnl:.2f}" if net_pnl > 0 else f"£{net_pnl:.2f}"
            
            message = f"""📊 <b>DAILY SUMMARY - {date_str}</b>

🏇 {pnl['bot_type']} - {pnl['mode']}

📋 <b>Activity:</b>
• Total Selections: {pnl['total_selections'] or 0}
• Bets Placed: {pnl['bets_placed'] or 0}
• Bets Skipped: {pnl['bets_skipped'] or 0}

🎯 <b>Results:</b>
• Winners: {wins}
• Losers: {losses}
• Win Rate: {win_rate:.1f}%

💰 <b>Financial:</b>
• Total Staked: £{total_staked:.2f}
• Net P&L: {pnl_str}
• ROI: {roi:.2f}%

{result_emoji} {'Profitable day!' if net_pnl > 0 else 'Keep grinding!'}

#HorseRacing #DailyPNL #GiddyUp"""
            
            if send_telegram_message(message):
                print(f"{Colors.GREEN}✅ Summary posted to Telegram!{Colors.RESET}\n")
            else:
                print(f"{Colors.RED}❌ Failed to post to Telegram{Colors.RESET}\n")
    
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
    
    finally:
        tracker.close()

if __name__ == "__main__":
    # Parse arguments
    date_str = None
    post_telegram = False
    
    for arg in sys.argv[1:]:
        if arg == '--telegram':
            post_telegram = True
        elif not arg.startswith('--'):
            date_str = arg
    
    # Default to today
    if not date_str:
        date_str = date_module.today().strftime('%Y-%m-%d')
    
    show_daily_pnl(date_str, post_telegram)

