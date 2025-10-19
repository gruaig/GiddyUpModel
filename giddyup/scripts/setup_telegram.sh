#!/bin/bash
#
# Telegram Setup Helper
# Helps you get your chat ID and configure Telegram
#
# Usage: ./setup_telegram.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
BOT_TOKEN="8419851120:AAHTWE5k67fR7_wuyS5Lv9JFjKJ30ODClHI"

echo "================================================================================"
echo "📱 TELEGRAM SETUP HELPER"
echo "================================================================================"
echo ""
echo "Bot Token: ${BOT_TOKEN:0:20}..."
echo ""

# Step 1: Check bot status
echo "Step 1: Checking bot status..."
RESPONSE=$(curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    BOT_NAME=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['username'])")
    echo "✅ Bot is active: @$BOT_NAME"
else
    echo "❌ Bot token is invalid or bot is not active"
    exit 1
fi

echo ""

# Step 2: Get chat ID
echo "Step 2: Getting your chat ID..."
echo ""
echo "To get your chat ID:"
echo "  1. Open Telegram"
echo "  2. Search for: @$BOT_NAME"
echo "  3. Send a message to the bot: /start"
echo "  4. OR add the bot to a group and send any message"
echo ""
read -p "Press ENTER after you've sent a message to the bot..."
echo ""

# Fetch updates
echo "Fetching latest messages..."
UPDATES=$(curl -s "https://api.telegram.org/bot$BOT_TOKEN/getUpdates")

# Extract chat IDs
CHAT_IDS=$(echo "$UPDATES" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('ok') and data.get('result'):
        chats = set()
        for update in data['result']:
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                chat_type = update['message']['chat']['type']
                chat_title = update['message']['chat'].get('title', update['message']['chat'].get('first_name', 'Unknown'))
                chats.add((chat_id, chat_type, chat_title))
        
        if chats:
            print('Found chat ID(s):')
            for chat_id, chat_type, title in chats:
                print(f'  Chat ID: {chat_id}')
                print(f'  Type: {chat_type}')
                print(f'  Name: {title}')
                print()
        else:
            print('No messages found. Make sure you sent a message to the bot!')
    else:
        print('No updates available')
except Exception as e:
    print(f'Error: {e}')
")

echo ""
echo "$CHAT_IDS"
echo ""

# Step 3: Configure
echo "Step 3: Update configuration..."
echo ""

# Get the first chat ID from output
CHAT_ID=$(echo "$CHAT_IDS" | grep "Chat ID:" | head -1 | awk '{print $3}')

if [ -n "$CHAT_ID" ]; then
    echo "Found Chat ID: $CHAT_ID"
    echo ""
    read -p "Use this chat ID? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Update config file
        CONFIG_FILE="$SCRIPT_DIR/telegram_config.py"
        
        if [ -f "$CONFIG_FILE" ]; then
            # Update existing file
            sed -i "s/TELEGRAM_CHAT_ID = .*/TELEGRAM_CHAT_ID = \"$CHAT_ID\"/" "$CONFIG_FILE"
            echo "✅ Updated $CONFIG_FILE"
        else
            echo "❌ Config file not found: $CONFIG_FILE"
            echo "   Copy template first: cp telegram_config.template.py telegram_config.py"
            exit 1
        fi
        
        echo ""
        echo "Testing connection..."
        python3 "$SCRIPT_DIR/telegram_bot.py"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "=" * 80
            echo "✅ TELEGRAM SETUP COMPLETE!"
            echo "=" * 80
            echo ""
            echo "You should have received a test message in Telegram!"
            echo ""
            echo "Next steps:"
            echo "  - Run bot: python3 HorseBot_Simple.py start \$(date +%Y-%m-%d) 5000 --stream"
            echo "  - Get notifications automatically!"
            echo ""
        fi
    fi
else
    echo "⚠️  Could not extract chat ID automatically"
    echo ""
    echo "Manual setup:"
    echo "  1. Visit: https://api.telegram.org/bot$BOT_TOKEN/getUpdates"
    echo "  2. Find: \"chat\":{\"id\":YOUR_NUMBER}"
    echo "  3. Copy that number"
    echo "  4. Edit telegram_config.py and set TELEGRAM_CHAT_ID to that number"
    echo ""
fi

echo "================================================================================"
echo ""

