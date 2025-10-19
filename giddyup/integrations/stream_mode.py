#!/usr/bin/env python3
"""
Stream Mode - Colorized, Exciting Logs for Twitch Streaming

Usage:
    python3 HorseBot_Simple.py start 2025-10-18 5000 --stream
"""

from datetime import datetime
import pytz

# ANSI color codes for terminal
class Colors:
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Backgrounds
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # Reset
    RESET = '\033[0m'
    CLEAR = '\033[2J\033[H'


def banner(text: str, color=Colors.BRIGHT_CYAN) -> str:
    """Create a large banner."""
    width = 100
    line = "═" * width
    
    return f"""
{color}{Colors.BOLD}{line}
{text.center(width)}
{line}{Colors.RESET}
"""


def big_announcement(text: str, color=Colors.BRIGHT_GREEN) -> str:
    """Create a big announcement banner."""
    return f"""
{color}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║  {text.center(92)}  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
"""


def racing_ascii_art() -> str:
    """Horse racing ASCII art."""
    return f"""{Colors.BRIGHT_CYAN}
    🏇                                        
  ┌─────────────────────────────────────────┐
  │  🎯 GIDDYUP AUTOMATED BETTING SYSTEM 🎯 │
  └─────────────────────────────────────────┘
{Colors.RESET}"""


def bet_placed_banner(horse: str, course: str, odds: float, stake: float, profit: float) -> str:
    """Exciting bet placed banner."""
    return f"""
{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                    🎯 BET PLACED! 🎯                                             ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
{Colors.BRIGHT_GREEN}{Colors.BOLD}
  🏇 HORSE:  {horse}
  📍 COURSE: {course}
  💰 STAKE:  £{stake:.2f}
  📊 ODDS:   {odds:.2f}
  ✨ PROFIT POTENTIAL: £{profit:.2f}
{Colors.RESET}
{Colors.YELLOW}
  ⚡ LET'S GOOOOO! ⚡
{Colors.RESET}
"""


def bet_skipped_banner(horse: str, course: str, reason: str, current: float, needed: float) -> str:
    """Bet skipped banner."""
    return f"""
{Colors.BG_RED}{Colors.BLACK}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                    ⏭️  BET SKIPPED  ⏭️                                            ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
{Colors.BRIGHT_RED}
  🏇 HORSE:  {horse}
  📍 COURSE: {course}
  📊 CURRENT ODDS: {current:.2f}
  ❌ NEEDED: {needed:.2f}
  
  ⚠️  REASON: {reason}
{Colors.RESET}
{Colors.DIM}
  Moving on to next race...
{Colors.RESET}
"""


def win_announcement(horse: str, course: str, pnl: float) -> str:
    """Big win announcement."""
    return f"""
{Colors.BG_GREEN}{Colors.BRIGHT_YELLOW}{Colors.BOLD}{Colors.BLINK}
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                   🎉🎉🎉 WINNER! 🎉🎉🎉                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
{Colors.BRIGHT_GREEN}{Colors.BOLD}
  🏆 {horse} @ {course}
  
  💰💰💰 PROFIT: £{pnl:+.2f} 💰💰💰
  
  🎉 YESSSSS! 🎉
{Colors.RESET}
"""


def loss_announcement(horse: str, course: str, pnl: float) -> str:
    """Loss announcement."""
    return f"""
{Colors.BRIGHT_RED}
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                      😔 LOST 😔                                                   ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
{Colors.RED}
  🏇 {horse} @ {course}
  📉 Loss: £{pnl:.2f}
  
  On to the next one! 💪
{Colors.RESET}
"""


def market_analysis(horse: str, course: str, race_time: str, expected: float, 
                   current: float, minimum: float, drift_pct: float) -> str:
    """Market analysis display."""
    
    drift_color = Colors.GREEN if drift_pct >= 0 else Colors.RED
    criteria_met = current >= minimum
    criteria_color = Colors.BRIGHT_GREEN if criteria_met else Colors.BRIGHT_RED
    criteria_text = "✅ GOOD TO BET!" if criteria_met else "❌ TOO LOW"
    
    return f"""
{Colors.BRIGHT_CYAN}{Colors.BOLD}
═══════════════════════════════════════════════════════════════════════════════════════════════════
                                📊 MARKET ANALYSIS 📊
═══════════════════════════════════════════════════════════════════════════════════════════════════
{Colors.RESET}

{Colors.BRIGHT_WHITE}{Colors.BOLD}  🏇 {horse}{Colors.RESET}
{Colors.CYAN}  📍 {course} • ⏰ {race_time}{Colors.RESET}

{Colors.BRIGHT_YELLOW}  📈 ODDS COMPARISON:{Colors.RESET}
     Expected:  {Colors.WHITE}{expected:.2f}{Colors.RESET}
     Current:   {Colors.BRIGHT_WHITE}{Colors.BOLD}{current:.2f}{Colors.RESET}
     Minimum:   {Colors.YELLOW}{minimum:.2f}{Colors.RESET}
     Drift:     {drift_color}{drift_pct:+.1f}%{Colors.RESET}

{criteria_color}{Colors.BOLD}  {criteria_text}{Colors.RESET}

{Colors.CYAN}{'═' * 99}{Colors.RESET}
"""


def countdown_timer(minutes_left: int) -> str:
    """Display countdown to race."""
    if minutes_left > 60:
        return f"{Colors.DIM}⏰ T-{minutes_left} ({minutes_left // 60}h {minutes_left % 60}m to race){Colors.RESET}"
    elif minutes_left > 10:
        return f"{Colors.YELLOW}⏰ T-{minutes_left} minutes{Colors.RESET}"
    elif minutes_left > 5:
        return f"{Colors.BRIGHT_YELLOW}{Colors.BOLD}⏰ T-{minutes_left} minutes - Getting close!{Colors.RESET}"
    else:
        return f"{Colors.BRIGHT_RED}{Colors.BOLD}{Colors.BLINK}⏰ T-{minutes_left} minutes - RACE STARTING SOON!{Colors.RESET}"


def daily_summary_banner(date: str, total_bets: int, total_stake: float) -> str:
    """Daily summary for stream start."""
    return f"""
{Colors.CLEAR}
{Colors.BRIGHT_CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                         🏇 GIDDYUP LIVE BETTING STREAM 🏇                                        ║
║                                                                                                  ║
║                                   {date}                                                         ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}

{Colors.BRIGHT_WHITE}{Colors.BOLD}📊 TODAY'S CARD:{Colors.RESET}
   {Colors.GREEN}Selections: {total_bets}{Colors.RESET}
   {Colors.YELLOW}Total Stake: £{total_stake:.2f}{Colors.RESET}

{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}
"""


def progress_bar(current: int, total: int, width: int = 50) -> str:
    """Create a visual progress bar."""
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    pct = (current / total * 100) if total > 0 else 0
    
    return f"{Colors.BRIGHT_CYAN}[{bar}]{Colors.RESET} {Colors.BRIGHT_WHITE}{current}/{total}{Colors.RESET} ({pct:.0f}%)"


def odds_meter(current: float, minimum: float, expected: float) -> str:
    """Visual odds meter."""
    
    # Calculate position on scale
    scale_min = minimum * 0.8
    scale_max = expected * 1.2
    scale_range = scale_max - scale_min
    
    current_pos = int(30 * (current - scale_min) / scale_range) if scale_range > 0 else 15
    min_pos = int(30 * (minimum - scale_min) / scale_range) if scale_range > 0 else 10
    exp_pos = int(30 * (expected - scale_min) / scale_range) if scale_range > 0 else 20
    
    # Clamp positions
    current_pos = max(0, min(30, current_pos))
    min_pos = max(0, min(30, min_pos))
    exp_pos = max(0, min(30, exp_pos))
    
    # Build meter
    meter = [" "] * 31
    meter[min_pos] = f"{Colors.RED}M{Colors.RESET}"  # Minimum
    meter[exp_pos] = f"{Colors.YELLOW}E{Colors.RESET}"  # Expected
    meter[current_pos] = f"{Colors.BRIGHT_GREEN}{Colors.BOLD}C{Colors.RESET}"  # Current
    
    meter_str = "".join(meter)
    
    return f"""
  {Colors.DIM}Odds Meter:{Colors.RESET}
  [{meter_str}]
  {Colors.RED}M{Colors.RESET}=Min:{minimum:.2f}  {Colors.YELLOW}E{Colors.RESET}=Exp:{expected:.2f}  {Colors.BRIGHT_GREEN}C{Colors.RESET}=Now:{current:.2f}
"""


def selection_card(num: int, horse: str, course: str, time: str, odds: float, 
                  stake: float, strategy: str, reasoning: str) -> str:
    """Beautiful selection card."""
    
    strategy_color = Colors.BRIGHT_GREEN if strategy == 'A-Hybrid_V3' else Colors.BRIGHT_BLUE
    strategy_emoji = "🟢" if strategy == 'A-Hybrid_V3' else "🔵"
    
    return f"""
{strategy_color}{Colors.BOLD}┌─────────────────────────────────────────────────────────────────────────────────────┐
│ {strategy_emoji} BET #{num}: {horse[:60].ljust(60)} │
└─────────────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}
{Colors.WHITE}  ⏰ {time} @ {course}{Colors.RESET}
{Colors.BRIGHT_YELLOW}  💰 £{stake:.2f} @ {odds:.2f}{Colors.RESET}
{Colors.CYAN}  📊 {strategy}{Colors.RESET}
{Colors.DIM}  💡 {reasoning[:80]}{Colors.RESET}
"""


def waiting_animation(message: str = "Monitoring markets") -> str:
    """Waiting animation."""
    dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    import time
    idx = int(time.time() * 2) % len(dots)
    
    return f"{Colors.BRIGHT_CYAN}{dots[idx]} {message}...{Colors.RESET}"


def live_stats(bets_placed: int, bets_skipped: int, total_staked: float, 
              races_left: int) -> str:
    """Live stats ticker."""
    return f"""
{Colors.BG_BLUE}{Colors.BRIGHT_WHITE}{Colors.BOLD} 📊 LIVE STATS {Colors.RESET} {Colors.CYAN}Bets: {Colors.BRIGHT_GREEN}{bets_placed}{Colors.CYAN} | Skipped: {Colors.BRIGHT_RED}{bets_skipped}{Colors.CYAN} | Staked: {Colors.BRIGHT_YELLOW}£{total_staked:.2f}{Colors.CYAN} | Races Left: {Colors.BRIGHT_WHITE}{races_left}{Colors.RESET}
"""


def twitch_chat_format(message: str) -> str:
    """Format message for Twitch chat (no colors)."""
    # Strip ANSI codes for Twitch
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', message)


if __name__ == "__main__":
    # Demo of stream mode
    print(racing_ascii_art())
    print(daily_summary_banner("2025-10-18", 8, 150.00))
    print(selection_card(1, "Woodhay Whisper (IRE)", "Kempton", "18:27", 13.50, 20.00, "B-Path_B", "Edge +18pp | EV +500%"))
    print(market_analysis("Test Horse", "Kempton", "14:30", 10.0, 11.5, 9.5, 15.0))
    print(bet_placed_banner("Woodhay Whisper (IRE)", "Kempton", 13.50, 20.00, 250.00))
    print(live_stats(3, 2, 55.00, 5))
    print(countdown_timer(45))

