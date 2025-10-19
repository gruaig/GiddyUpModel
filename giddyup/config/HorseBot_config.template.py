"""
HorseBot Configuration Template

Copy this file to 'HorseBot_config.py' and fill in your Betfair credentials.
NEVER commit HorseBot_config.py to git (it's in .gitignore)
"""

# ══════════════════════════════════════════════════════════════════════════════
# BETFAIR CREDENTIALS
# ══════════════════════════════════════════════════════════════════════════════

BETFAIR_USERNAME = "your_username_here"
BETFAIR_PASSWORD = "your_password_here"
BETFAIR_APP_KEY = "your_app_key_here"  # Get from: https://developer.betfair.com/get-started/

# ══════════════════════════════════════════════════════════════════════════════
# BETTING PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

# When to check odds before race
T_MINUS_WINDOW = 60  # Minutes before race to start checking

# How often to re-check odds
RECHECK_INTERVAL = 300  # Seconds (5 minutes)

# Minimum market liquidity (£ matched)
MIN_MARKET_LIQUIDITY = 1000

# Maximum price drift from expected odds (as decimal %)
MAX_PRICE_DRIFT = 0.15  # 15%

# ══════════════════════════════════════════════════════════════════════════════
# ADVANCED OPTIONS
# ══════════════════════════════════════════════════════════════════════════════

# Enable/disable specific strategies
ENABLE_STRATEGY_A = True  # Hybrid V3
ENABLE_STRATEGY_B = True  # Path B

# Slack/Discord notifications (optional)
SLACK_WEBHOOK_URL = None  # "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
DISCORD_WEBHOOK_URL = None  # "https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"

# Email notifications (optional)
EMAIL_ENABLED = False
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_FROM = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EMAIL_TO = "your_email@gmail.com"


