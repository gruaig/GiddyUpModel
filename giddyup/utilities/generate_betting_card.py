#!/usr/bin/env python3
"""
Generate PNG betting card from daily selections CSV.

Usage:
    python3 generate_betting_card.py 2025-10-18
"""

import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("\n" + "="*80)
    print("Missing Pillow! Install with:")
    print("  pip3 install pillow")
    print("="*80 + "\n")
    sys.exit(1)


def load_bets(date: str) -> List[Dict]:
    """Load bets for a specific date from CSV."""
    csv_file = Path(__file__).parent / "strategies" / "logs" / "daily_bets" / "betting_log_2025.csv"
    
    if not csv_file.exists():
        print(f"❌ No betting log found: {csv_file}")
        return []
    
    bets = []
    with csv_file.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == date:
                bets.append(row)
    
    return bets


def create_betting_card(date: str, bets: List[Dict], output_path: Path):
    """Create a PNG betting card image."""
    
    # Card dimensions
    CARD_WIDTH = 1200
    HEADER_HEIGHT = 120
    BET_HEIGHT = 160
    FOOTER_HEIGHT = 80
    PADDING = 40
    
    CARD_HEIGHT = HEADER_HEIGHT + (BET_HEIGHT * len(bets)) + FOOTER_HEIGHT + (PADDING * 2)
    
    # Colors
    BG_COLOR = (15, 23, 42)  # Dark slate
    HEADER_BG = (30, 41, 59)  # Lighter slate
    BET_BG_A = (22, 163, 74)  # Green for Strategy A
    BET_BG_B = (59, 130, 246)  # Blue for Strategy B
    TEXT_COLOR = (248, 250, 252)  # Almost white
    SUBTEXT_COLOR = (148, 163, 184)  # Gray
    ACCENT_COLOR = (234, 179, 8)  # Yellow/gold
    
    # Create image
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts (fallback to default if not available)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_bet_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_bet_detail = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        font_bet_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_bet_title = ImageFont.load_default()
        font_bet_detail = ImageFont.load_default()
        font_bet_small = ImageFont.load_default()
    
    # Header
    draw.rectangle([(0, 0), (CARD_WIDTH, HEADER_HEIGHT)], fill=HEADER_BG)
    
    # Title
    title_text = f"🏇 GiddyUp Betting Card"
    draw.text((PADDING, 25), title_text, fill=TEXT_COLOR, font=font_title)
    
    # Date and count
    subtitle_text = f"{date} • {len(bets)} Selection{'s' if len(bets) != 1 else ''}"
    draw.text((PADDING, 80), subtitle_text, fill=SUBTEXT_COLOR, font=font_subtitle)
    
    # Calculate total stake
    total_stake = sum(float(bet['stake_gbp']) for bet in bets)
    stake_text = f"Total Stake: £{total_stake:.2f}"
    draw.text((CARD_WIDTH - PADDING - 250, 80), stake_text, fill=ACCENT_COLOR, font=font_subtitle)
    
    # Bets
    y_offset = HEADER_HEIGHT + PADDING
    
    for i, bet in enumerate(bets):
        # Determine strategy color
        strategy_color = BET_BG_A if bet['strategy'] == 'A-Hybrid_V3' else BET_BG_B
        
        # Bet card background
        bet_y = y_offset + (i * BET_HEIGHT)
        draw.rectangle(
            [(PADDING, bet_y), (CARD_WIDTH - PADDING, bet_y + BET_HEIGHT - 10)],
            fill=strategy_color,
            outline=TEXT_COLOR,
            width=2
        )
        
        # Race time and course
        time_course = f"{bet['time']} • {bet['course']}"
        draw.text((PADDING + 20, bet_y + 15), time_course, fill=TEXT_COLOR, font=font_bet_small)
        
        # Horse name
        horse_name = bet['horse']
        draw.text((PADDING + 20, bet_y + 45), horse_name, fill=TEXT_COLOR, font=font_bet_title)
        
        # Odds and stake
        odds_stake = f"@ {bet['odds']} → £{bet['stake_gbp']}"
        draw.text((PADDING + 20, bet_y + 85), odds_stake, fill=TEXT_COLOR, font=font_bet_detail)
        
        # Min odds needed
        min_odds_text = f"Min odds: {bet['min_odds_needed']}"
        draw.text((CARD_WIDTH - PADDING - 200, bet_y + 85), min_odds_text, fill=TEXT_COLOR, font=font_bet_small)
        
        # Strategy badge
        strategy_text = bet['strategy']
        draw.text((CARD_WIDTH - PADDING - 200, bet_y + 15), strategy_text, fill=TEXT_COLOR, font=font_bet_small)
        
        # Reasoning (truncated if too long)
        reasoning = bet['reasoning']
        if len(reasoning) > 70:
            reasoning = reasoning[:67] + "..."
        draw.text((PADDING + 20, bet_y + 115), reasoning, fill=SUBTEXT_COLOR, font=font_bet_small)
    
    # Footer
    footer_y = CARD_HEIGHT - FOOTER_HEIGHT
    footer_text = "🎯 Place bets at T-60 if Betfair odds ≥ min_odds_needed • #GiddyUp"
    draw.text((PADDING, footer_y + 20), footer_text, fill=SUBTEXT_COLOR, font=font_bet_small)
    
    # Save
    img.save(output_path)
    print(f"✅ Betting card saved: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python3 generate_betting_card.py <date>")
        print("Example: python3 generate_betting_card.py 2025-10-18\n")
        sys.exit(1)
    
    date = sys.argv[1]
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    # Load bets
    print(f"📊 Generating betting card for {date}...")
    bets = load_bets(date)
    
    if not bets:
        print(f"❌ No bets found for {date}")
        sys.exit(1)
    
    print(f"   Found {len(bets)} bet(s)")
    
    # Output path
    output_dir = Path(__file__).parent / "strategies" / "logs" / "daily_bets"
    output_path = output_dir / f"betting_card_{date}.png"
    
    # Generate card
    create_betting_card(date, bets, output_path)
    
    print(f"📁 Location: {output_path}")
    print("")
    print("💡 You can now:")
    print(f"   - View: xdg-open {output_path}")
    print(f"   - Share on social media")
    print(f"   - Print for physical reference")
    print("")


if __name__ == "__main__":
    main()

