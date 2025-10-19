#!/bin/bash
#
# Quick-start script to run HorseBot for today
#
# Usage:
#   ./run_bot_today.sh 5000              # Live betting with £5000 bankroll
#   ./run_bot_today.sh 5000 --dry-run    # Dry run (no real bets)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for bankroll argument
if [ -z "$1" ]; then
    echo "Usage: $0 <bankroll_gbp> [--dry-run]"
    echo ""
    echo "Examples:"
    echo "  $0 5000              # Live betting with £5000"
    echo "  $0 5000 --dry-run    # Dry run mode (no real bets)"
    exit 1
fi

BANKROLL=$1
TODAY=$(date +%Y-%m-%d)
DRY_RUN_FLAG=""

if [ "$2" == "--dry-run" ]; then
    DRY_RUN_FLAG="--dry-run"
    echo "========================================"
    echo "🧪 DRY RUN MODE (NO REAL BETS)"
    echo "========================================"
    echo ""
fi

echo "Starting HorseBot for $TODAY"
echo "Bankroll: £$BANKROLL"
echo ""

# Check config exists
if [ ! -f "HorseBot_config.py" ]; then
    echo "❌ ERROR: HorseBot_config.py not found!"
    echo ""
    echo "Please create your config file first:"
    echo "  1. cp HorseBot_config.template.py HorseBot_config.py"
    echo "  2. Edit HorseBot_config.py with your Betfair credentials"
    echo ""
    echo "See HORSEBOT_README.md for details."
    exit 1
fi

# Check dependencies
if ! python3 -c "import betfairlightweight" 2>/dev/null; then
    echo "❌ ERROR: betfairlightweight not installed"
    echo ""
    echo "Install dependencies:"
    echo "  pip install -r horsebot_requirements.txt"
    echo ""
    exit 1
fi

# Run the bot
echo "🤖 Launching HorseBot..."
echo ""

python3 HorseBot.py --date "$TODAY" --bankroll "$BANKROLL" $DRY_RUN_FLAG

