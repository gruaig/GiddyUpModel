#!/bin/bash
# generate_tweet_files.sh - Generate .tweet files for manual posting
# Usage: ./generate_tweet_files.sh [date] [type] [params...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/strategies/logs/automated_bets"
TWEET_DIR="$SCRIPT_DIR/strategies/logs/tweets"

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

# Function to generate bet placed tweet file
generate_bet_tweet_file() {
    local race_time="$1"
    local course="$2"
    local horse="$3"
    local odds="$4"
    local stake="$5"
    local strategy="$6"
    
    # Normalize names for hashtags
    local horse_tag=$(normalize_horse_name "$horse")
    local course_tag=$(normalize_course_name "$course")
    
    # Create filename: <race_time><course><horse>.tweet
    local filename="${race_time}_${course}_${horse_tag}.tweet"
    local filepath="$TWEET_DIR/$filename"
    
    # Generate tweet content
    cat > "$filepath" << EOF
🎯 New Bet Placed

🏇 $horse @ $course
⏰ Race: $race_time
💰 £$stake @ $odds
📈 Strategy: $strategy

#HorseRacing #Betting #$course_tag #$horse_tag
EOF
    
    echo "✅ Generated bet tweet: $filename"
}

# Function to generate daily summary tweet file
generate_summary_tweet_file() {
    local actions_file="$LOG_DIR/bot_actions_$DATE.csv"
    local report_file="$LOG_DIR/betting_report_$DATE.xlsx"
    
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
    
    # Create filename: <date>_summary.tweet
    local filename="${DATE}_summary.tweet"
    local filepath="$TWEET_DIR/$filename"
    
    # Generate tweet content
    cat > "$filepath" << EOF
📊 $DATE Summary

🎯 Total Selections: $total_bets
💰 Total Staked: £$total_staked
✅ Bets Placed: $dry_run_bets
⏭️ Skipped: $skipped_bets

#HorseRacing #Betting #Automation$course_hashtags
EOF
    
    echo "✅ Generated summary tweet: $filename"
}

# Function to generate bet result tweet file
generate_result_tweet_file() {
    local race_time="$1"
    local course="$2"
    local horse="$3"
    local result="$4"
    local pnl="$5"
    
    # Normalize names for hashtags
    local horse_tag=$(normalize_horse_name "$horse")
    local course_tag=$(normalize_course_name "$course")
    
    # Create filename: <race_time><course><horse>_result.tweet
    local filename="${race_time}_${course}_${horse_tag}_result.tweet"
    local filepath="$TWEET_DIR/$filename"
    
    # Choose emoji based on result
    local emoji="🎉"
    if [[ "$result" == "LOSS" ]]; then
        emoji="😔"
    fi
    
    # Generate tweet content
    cat > "$filepath" << EOF
$emoji Bet Result

🏇 $horse @ $course
📊 Result: $result
💰 P&L: £$pnl

#HorseRacing #Betting #$course_tag #$horse_tag
EOF
    
    echo "✅ Generated result tweet: $filename"
}

# Main execution
case "$TYPE" in
    "summary")
        echo "📊 Generating daily summary tweet file for $DATE..."
        generate_summary_tweet_file
        ;;
    
    "bet_placed")
        echo "🎯 Generating bet placed tweet file..."
        if [[ $# -lt 8 ]]; then
            echo "❌ Usage: $0 $DATE bet_placed <race_time> <course> <horse> <odds> <stake> <strategy>"
            exit 1
        fi
        generate_bet_tweet_file "$3" "$4" "$5" "$6" "$7" "$8"
        ;;
    
    "bet_result")
        echo "📊 Generating bet result tweet file..."
        if [[ $# -lt 7 ]]; then
            echo "❌ Usage: $0 $DATE bet_result <race_time> <course> <horse> <result> <pnl>"
            exit 1
        fi
        generate_result_tweet_file "$3" "$4" "$5" "$6" "$7"
        ;;
    
    *)
        echo "❌ Unknown type: $TYPE"
        echo "Valid types: summary, bet_placed, bet_result"
        exit 1
        ;;
esac

echo "📁 Tweet files saved to: $TWEET_DIR"
echo "💡 Copy the content and paste into Twitter manually"

