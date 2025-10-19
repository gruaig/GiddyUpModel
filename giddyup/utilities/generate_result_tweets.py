#!/usr/bin/env python3
"""
Generate result tweets from bot actions CSV after results have been filled in.

Usage:
    python3 generate_result_tweets.py 2025-10-18
    
This reads the bot_actions_<date>.csv file and generates result tweets 
for any bets that have results (WIN/LOSS) filled in.
"""

import sys
import csv
import re
from pathlib import Path
from datetime import datetime


def normalize_horse_name(horse: str) -> str:
    """Normalize horse name for hashtag."""
    horse = re.sub(r'\s*\((GB|IRE|FR|USA)\)$', '', horse)
    return re.sub(r'[^a-zA-Z0-9]', '', horse)


def normalize_course_name(course: str) -> str:
    """Normalize course name for hashtag."""
    return re.sub(r'[^a-zA-Z0-9]', '', course.replace(' ', ''))


def calculate_pnl(result: str, odds: float, stake: float) -> float:
    """Calculate P&L for a bet."""
    if result.upper() == "WIN":
        # Profit after 2% commission
        gross_return = odds * stake
        commission = gross_return * 0.02
        net_profit = gross_return - stake - commission
        return net_profit
    elif result.upper() == "LOSS":
        return -stake
    else:
        return 0.0


def generate_result_tweet(race_time: str, course: str, horse: str, result: str, 
                         pnl: float, tweet_dir: Path) -> str:
    """Generate a result tweet file."""
    horse_tag = normalize_horse_name(horse)
    course_tag = normalize_course_name(course)
    
    # Clean race time for filename
    race_time_clean = race_time.replace(':', '')
    filename = f"{race_time_clean}_{course_tag}_{horse_tag}_result.tweet"
    filepath = tweet_dir / filename
    
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

#HorseRacing #Betting #{course_tag} #{horse_tag}
"""
    
    # Write tweet file
    with filepath.open('w') as f:
        f.write(tweet_content)
    
    return filename


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python3 generate_result_tweets.py <date>")
        print("Example: python3 generate_result_tweets.py 2025-10-18\n")
        sys.exit(1)
    
    date = sys.argv[1]
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    # File paths
    base_dir = Path(__file__).parent
    actions_csv = base_dir / "strategies" / "logs" / "automated_bets" / f"bot_actions_{date}.csv"
    tweet_dir = base_dir / "strategies" / "logs" / "tweets"
    
    if not actions_csv.exists():
        print(f"❌ No actions file found: {actions_csv}")
        print(f"   Run the bot first to generate actions CSV")
        sys.exit(1)
    
    print(f"📊 Generating result tweets for {date}...")
    print(f"   Reading: {actions_csv}")
    print("")
    
    # Read CSV and find bets with results
    results_found = 0
    tweets_generated = 0
    
    with actions_csv.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        for row in reader:
            # Only process rows with bet placed and result filled in
            if row.get("bet_placed") in ["DRY_RUN", "EXECUTED", "YES"]:
                result = row.get("result", "").strip().upper()
                
                if result in ["WIN", "LOSS"]:
                    results_found += 1
                    
                    # Calculate P&L if not provided
                    if row.get("pnl_gbp"):
                        try:
                            pnl = float(row["pnl_gbp"])
                        except ValueError:
                            pnl = calculate_pnl(result, float(row["actual_odds"]), float(row["stake"]))
                    else:
                        pnl = calculate_pnl(result, float(row["actual_odds"]), float(row["stake"]))
                    
                    # Generate tweet
                    try:
                        filename = generate_result_tweet(
                            race_time=row["race_time"],
                            course=row["course"],
                            horse=row["horse"],
                            result=result,
                            pnl=pnl,
                            tweet_dir=tweet_dir
                        )
                        
                        emoji = "🎉" if result == "WIN" else "😔"
                        pnl_str = f"+£{pnl:.2f}" if pnl > 0 else f"£{pnl:.2f}"
                        
                        print(f"{emoji} {row['horse']} @ {row['race_time']}")
                        print(f"   Result: {result} | P&L: {pnl_str}")
                        print(f"   Tweet: {filename}")
                        print("")
                        
                        tweets_generated += 1
                        
                    except Exception as e:
                        print(f"⚠️  Error generating tweet for {row['horse']}: {e}")
                        print("")
    
    print("=" * 80)
    print(f"✅ COMPLETE")
    print("=" * 80)
    print(f"   Results found: {results_found}")
    print(f"   Tweets generated: {tweets_generated}")
    print("")
    print(f"📁 Tweets saved to: {tweet_dir}")
    print("")
    
    if tweets_generated > 0:
        print("📋 Next steps:")
        print("   1. Review tweets: ls -lh strategies/logs/tweets/*_result.tweet")
        print("   2. Post to social media")
        print("   3. Archive: ./tweet_manager.sh archive <filename>")
        print("")
    else:
        print("💡 No tweets generated. Make sure:")
        print("   1. Bot has been run and placed bets")
        print("   2. Results (WIN/LOSS) are filled in the CSV")
        print("   3. Check: cat strategies/logs/automated_bets/bot_actions_" + date + ".csv")
        print("")


if __name__ == "__main__":
    main()

