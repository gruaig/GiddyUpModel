#!/bin/bash
# tweet_manager.sh - Manage your .tweet files
# Usage: ./tweet_manager.sh [command]

TWEET_DIR="/home/smonaghan/GiddyUpModel/giddyup/strategies/logs/tweets"

case "$1" in
    "list")
        echo "📁 Tweet files ready for posting:"
        echo "=================================="
        ls -la "$TWEET_DIR"/*.tweet 2>/dev/null | while read line; do
            filename=$(echo "$line" | awk '{print $9}' | xargs basename)
            size=$(echo "$line" | awk '{print $5}')
            echo "📄 $filename ($size bytes)"
        done
        ;;
    
    "show")
        if [[ -z "$2" ]]; then
            echo "❌ Usage: ./tweet_manager.sh show <filename>"
            echo "Available files:"
            ls "$TWEET_DIR"/*.tweet 2>/dev/null | xargs -n1 basename
            exit 1
        fi
        echo "🐦 Tweet content for $2:"
        echo "========================"
        cat "$TWEET_DIR/$2"
        ;;
    
    "post")
        if [[ -z "$2" ]]; then
            echo "❌ Usage: ./tweet_manager.sh post <filename>"
            echo "Available files:"
            ls "$TWEET_DIR"/*.tweet 2>/dev/null | xargs -n1 basename
            exit 1
        fi
        echo "🐦 Tweet content for $2:"
        echo "========================"
        cat "$TWEET_DIR/$2"
        echo ""
        echo "📋 Copy the above content and paste into Twitter"
        echo "✅ After posting, run: ./tweet_manager.sh archive $2"
        ;;
    
    "archive")
        if [[ -z "$2" ]]; then
            echo "❌ Usage: ./tweet_manager.sh archive <filename>"
            exit 1
        fi
        mkdir -p "$TWEET_DIR/archived"
        mv "$TWEET_DIR/$2" "$TWEET_DIR/archived/"
        echo "✅ Archived $2"
        ;;
    
    "clean")
        echo "🧹 Cleaning up old tweet files..."
        find "$TWEET_DIR" -name "*.tweet" -mtime +7 -delete
        echo "✅ Cleaned up tweet files older than 7 days"
        ;;
    
    *)
        echo "🐦 Tweet Manager"
        echo "==============="
        echo ""
        echo "Commands:"
        echo "  list     - List all tweet files"
        echo "  show     - Show tweet content"
        echo "  post     - Show tweet for posting"
        echo "  archive  - Archive posted tweet"
        echo "  clean    - Clean up old files"
        echo ""
        echo "Examples:"
        echo "  ./tweet_manager.sh list"
        echo "  ./tweet_manager.sh show 2025-10-18_summary.tweet"
        echo "  ./tweet_manager.sh post 11:56_Catterick_ArcticFox.tweet"
        echo "  ./tweet_manager.sh archive 11:56_Catterick_ArcticFox.tweet"
        ;;
esac


