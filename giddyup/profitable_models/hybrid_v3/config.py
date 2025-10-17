"""
Hybrid Model V3 - Production Configuration

This model is PROFITABLE: +3.1% ROI on 1,794 bets
"""

# ===== Selection Gates =====
MIN_DISAGREEMENT_RATIO = 2.50  # Model must be 150%+ higher than market
MIN_EDGE_ABSOLUTE = 0.08       # Minimum 8pp edge
MIN_RANK = 3                   # Skip favorites
MAX_RANK = 6                   # Mid-field only
ODDS_MIN = 7.0                 # Sweet spot
ODDS_MAX = 12.0
MAX_OVERROUND = 1.18           # Competitive markets only
MIN_EV_ADJUSTED = 0.05         # 5% EV minimum

# ===== Staking =====
KELLY_FRACTION = 0.10          # 1/10 Kelly
MAX_STAKE = 0.3                # Cap per bet
COMMISSION = 0.02              # Betfair commission

# ===== Risk Controls =====
MAX_BETS_PER_RACE = 1
MAX_DAILY_STAKE = 15.0
MAX_DAILY_LOSS = 5.0

# ===== Training =====
TRAIN_DATE_FROM = "2006-01-01"
TRAIN_DATE_TO = "2023-12-31"  # Retrain Jan 1, 2026 with 2024 data
TEST_DATE_FROM = "2024-01-01"
TEST_DATE_TO = "2025-10-16"

# ===== Features (23 ability-only) =====
# NO official_rating, NO racing_post_rating
# See: src/giddyup/data/feature_lists.py

# ===== Performance =====
BACKTEST_ROI = 0.031          # +3.1%
BACKTEST_BETS = 1794
BACKTEST_WINS = 203
BACKTEST_AVG_ODDS = 9.96

