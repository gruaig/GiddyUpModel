#!/bin/bash
# generate_tweet.sh - Generate tweet text for manual posting
# Usage: ./generate_tweet.sh [date] [type] [params...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/strategies/logs/automated_bets"

DATE=${1:-$(date +%Y-%m-%d)}
TYPE=${2:-"summary"}

# Function to normalize horse name for hashtag
normalize_horse_name() {
    local horse="$1"
    echo "$horse" | sed 's/ (GB)$//g' | sed 's/ (IRE)$//g' | sed 's/ (FR)$//g' | sed 's/ (USA)$//g' | \
    sed 's/ //g' | sed 's/[^a-zA-Z0-9]//g'
}

# Function to normalize course name for hashtag
normalize_course_name() {
    local course="$1"
    echo "$course" | sed 's/ //g' | sed 's/[^a-zA-Z0-9]//g'
}

# Function to generate daily summary tweet
generate_summary_tweet() {
    local actions_file="$LOG_DIR/bot_actions_$DATE.csv"
    
    if [[ ! -f "$actions_file" ]]; then
        echo "❌ No actions file found for $DATE"
        return 1
    fi
    
    local total_bets=$(tail -n +2 "$actions_file" | wc -l)
    local dry_run_bets=$(grep -c "DRY_RUN" "$actions_file" || echo "0")
    local skipped_bets=$(grep -c "NO" "$actions_file" || echo "0")
    local total_staked=$(tail -n +2 "$actions_file" | awk -F',' '{sum += $8} END {printf "%.2f", sum}')
    
    # Get top courses for hashtags
    local top_courses=$(tail -n +2 "$actions_file" | awk -F',' '{print $2}' | sort | uniq -c | sort -nr | head -3 | awk '{print $2}' | tr '\n' ' ')
    
    local course_hashtags=""
    for course in $top_courses; do
        if [[ -n "$course" ]]; then
            local course_tag=$(normalize_course_name "$course")
            course_hashtags="$course_hashtags #$course_tag"
        fi
    done
    
    echo "📊 $DATE Summary

🎯 Total Selections: $total_bets
💰 Total Staked: £$total_staked
✅ Bets Placed: $dry_run_bets
⏭️ Skipped: $skipped_bets

#HorseRacing #Betting #Automation$course_hashtags"
}

# Function to generate bet placed tweet
generate_bet_tweet() {
    local race_time="$1"
    local horse="$2"
    local course="$3"
    local odds="$4"
    local stake="$5"
    local strategy="$6"
    
    local horse_tag=$(normalize_horse_name "$horse")
    local course_tag=$(normalize_course_name "$course")
    
    echo "🎯 New Bet Placed

🏇 $horse @ $course
⏰ Race: $race_time
💰 £$stake @ $odds
📈 Strategy: $strategy

#HorseRacing #Betting #$course_tag #$horse_tag"
}

# Main execution
case "$TYPE" in
    "summary")
        generate_summary_tweet
        ;;
    "bet_placed")
        if [[ $# -lt 8 ]]; then
            echo "❌ Usage: $0 $DATE bet_placed <race_time> <horse> <course> <odds> <stake> <strategy>"
            exit 1
        fi
        generate_bet_tweet "$3" "$4" "$5" "$6" "$7" "$8"
        ;;
    *)
        echo "❌ Unknown type: $TYPE"
        echo "Valid types: summary, bet_placed"
        exit 1
        ;;
esac

