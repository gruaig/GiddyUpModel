#!/bin/bash
# publish_results.sh - Twitter posting script for betting results
# Usage: ./publish_results.sh [date] [type]
# Types: summary, bet_placed, bet_result

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/strategies/logs/automated_bets"
REPORT_DIR="$LOG_DIR"

# Default to today if no date provided
DATE=${1:-$(date +%Y-%m-%d)}
TYPE=${2:-"summary"}

# Twitter API credentials (you'll need to set these)
TWITTER_API_KEY="${TWITTER_API_KEY:-}"
TWITTER_API_SECRET="${TWITTER_API_SECRET:-}"
TWITTER_ACCESS_TOKEN="${TWITTER_ACCESS_TOKEN:-}"
TWITTER_ACCESS_SECRET="${TWITTER_ACCESS_SECRET:-}"

# Check if credentials are set
if [[ -z "$TWITTER_API_KEY" ]]; then
    echo "❌ Twitter API credentials not set!"
    echo "Set these environment variables:"
    echo "  export TWITTER_API_KEY='your_key'"
    echo "  export TWITTER_API_SECRET='your_secret'"
    echo "  export TWITTER_ACCESS_TOKEN='your_token'"
    echo "  export TWITTER_ACCESS_SECRET='your_secret'"
    exit 1
fi

# Function to post tweet
post_tweet() {
    local tweet_text="$1"
    echo "🐦 Posting tweet: $tweet_text"
    
    # Use Python script for proper OAuth handling
    python3 "$SCRIPT_DIR/twitter_post.py" "$tweet_text"
}

# Function to generate daily summary tweet
generate_summary_tweet() {
    local report_file="$REPORT_DIR/betting_report_$DATE.xlsx"
    local actions_file="$LOG_DIR/bot_actions_$DATE.csv"
    
    if [[ ! -f "$actions_file" ]]; then
        echo "❌ No actions file found for $DATE"
        return 1
    fi
    
    # Parse CSV data
    local total_bets=$(tail -n +2 "$actions_file" | wc -l)
    local dry_run_bets=$(grep -c "DRY_RUN" "$actions_file" || echo "0")
    local executed_bets=$(grep -c "EXECUTED" "$actions_file" || echo "0")
    local skipped_bets=$(grep -c "NO" "$actions_file" || echo "0")
    
    # Calculate total staked
    local total_staked=$(tail -n +2 "$actions_file" | awk -F',' '{sum += $8} END {printf "%.2f", sum}')
    
    # Get top courses for hashtags (limit to 3 most active)
    local top_courses=$(tail -n +2 "$actions_file" | awk -F',' '{print $2}' | sort | uniq -c | sort -nr | head -3 | awk '{print $2}' | tr '\n' ' ')
    
    # Generate course hashtags
    local course_hashtags=""
    for course in $top_courses; do
        if [[ -n "$course" ]]; then
            local course_tag=$(normalize_course_name "$course")
            course_hashtags="$course_hashtags #$course_tag"
        fi
    done
    
    # Generate tweet
    local tweet="📊 $DATE Summary
    
🎯 Total Selections: $total_bets
💰 Total Staked: £$total_staked
✅ Bets Placed: $dry_run_bets
⏭️ Skipped: $skipped_bets

#HorseRacing #Betting #Automation$course_hashtags"
    
    echo "$tweet"
}

# Function to normalize horse name for hashtag
normalize_horse_name() {
    local horse="$1"
    # Remove common suffixes and normalize
    echo "$horse" | sed 's/ (GB)$//g' | sed 's/ (IRE)$//g' | sed 's/ (FR)$//g' | sed 's/ (USA)$//g' | \
    sed 's/ //g' | sed 's/[^a-zA-Z0-9]//g'
}

# Function to normalize course name for hashtag
normalize_course_name() {
    local course="$1"
    echo "$course" | sed 's/ //g' | sed 's/[^a-zA-Z0-9]//g'
}

# Function to generate bet placed tweet
generate_bet_tweet() {
    local horse="$1"
    local course="$2"
    local odds="$3"
    local stake="$4"
    local strategy="$5"
    
    # Normalize names for hashtags
    local horse_tag=$(normalize_horse_name "$horse")
    local course_tag=$(normalize_course_name "$course")
    
    local tweet="🎯 New Bet Placed
    
🏇 $horse @ $course
💰 £$stake @ $odds
📈 Strategy: $strategy

#HorseRacing #Betting #$course_tag #$horse_tag"
    
    echo "$tweet"
}

# Function to generate result tweet
generate_result_tweet() {
    local horse="$1"
    local course="$2"
    local result="$3"
    local pnl="$4"
    
    # Normalize names for hashtags
    local horse_tag=$(normalize_horse_name "$horse")
    local course_tag=$(normalize_course_name "$course")
    
    local emoji="🎉"
    if [[ "$result" == "LOSS" ]]; then
        emoji="😔"
    fi
    
    local tweet="$emoji Bet Result
    
🏇 $horse @ $course
📊 Result: $result
💰 P&L: £$pnl

#HorseRacing #Betting #$course_tag #$horse_tag"
    
    echo "$tweet"
}

# Main execution
case "$TYPE" in
    "summary")
        echo "📊 Generating daily summary for $DATE..."
        tweet=$(generate_summary_tweet)
        if [[ $? -eq 0 ]]; then
            post_tweet "$tweet"
        fi
        ;;
    
    "bet_placed")
        echo "🎯 Posting bet placed notification..."
        # This would be called from the bot when a bet is placed
        # Parameters: horse, course, odds, stake, strategy
        if [[ $# -lt 7 ]]; then
            echo "❌ Usage: $0 $DATE bet_placed <horse> <course> <odds> <stake> <strategy>"
            exit 1
        fi
        tweet=$(generate_bet_tweet "$3" "$4" "$5" "$6" "$7")
        post_tweet "$tweet"
        ;;
    
    "bet_result")
        echo "📊 Posting bet result..."
        # This would be called when a bet result is known
        if [[ $# -lt 6 ]]; then
            echo "❌ Usage: $0 $DATE bet_result <horse> <course> <result> <pnl>"
            exit 1
        fi
        tweet=$(generate_result_tweet "$3" "$4" "$5" "$6")
        post_tweet "$tweet"
        ;;
    
    *)
        echo "❌ Unknown type: $TYPE"
        echo "Valid types: summary, bet_placed, bet_result"
        exit 1
        ;;
esac

echo "✅ Tweet posted successfully!"
