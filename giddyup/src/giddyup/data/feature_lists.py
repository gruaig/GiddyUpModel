"""
Feature lists for training vs scoring.

CRITICAL: Training uses ABILITY_FEATURES only (no market data).
Market features are joined at SCORING time only.
"""

# ===== ABILITY FEATURES (Path A - Pure Ability, NO Market Proxies) =====
# CRITICAL: NO official_rating, NO racing_post_rating, NO market features
# This model must be INDEPENDENT of expert opinions and market
ABILITY_FEATURES = [
    # GiddyUp Performance Rating (our own independent rating)
    "gpr",
    "gpr_sigma",
    # NOTE: gpr_minus_or removed (no OR in training)
    # NOTE: gpr_minus_rpr removed (no RPR in training)
    
    # Recent form (raw performance)
    "days_since_run",
    "last_pos",
    "avg_btn_last_3",
    
    # Career history (objective stats)
    "career_runs",
    "career_strike_rate",
    
    # Trainer long-term stats (objective)
    "trainer_sr_total",
    "trainer_wins_total",
    "trainer_runs_total",
    
    # Jockey long-term stats (objective)
    "jockey_sr_total",
    "jockey_wins_total",
    "jockey_runs_total",
    
    # Course/distance proficiency
    "runs_at_course",
    "wins_at_course",
    
    # Race context
    "field_size",
    "class_numeric",
    "is_flat",
    "is_aw",
    "dist_f",
    "draw",
    "age",
    "lbs",
]


# ===== MARKET FEATURES (for scoring only) =====
# These are NEVER used in training - only at prediction/betting time
MARKET_FEATURES = [
    "decimal_odds",
    "market_rank",
    "is_fav",
    "is_morning_fav",
    "price_drift_ratio",
    "price_movement",
    "price_spread",
    "volume_traded",
    "volume_per_runner",
]


def guard_no_market(cols: list[str]) -> None:
    """
    Ensure no market features leak into training.
    
    Uses both explicit list matching AND regex pattern matching to catch:
    - Official Rating (OR)
    - Racing Post Rating (RPR)
    - Odds, prices, rankings
    - Volume, trading data
    
    Raises:
        AssertionError: If any market features found in cols
        
    Example:
        >>> guard_no_market(["gpr", "trainer_sr_total"])  # OK
        >>> guard_no_market(["official_rating", "decimal_odds"])  # FAILS!
    """
    from giddyup.data.guards import assert_no_market_features
    
    # Use regex pattern matching (catches OR, RPR, odds, etc.)
    assert_no_market_features(df_cols=cols, feature_cols=cols)
    
    # Also check explicit MARKET_FEATURES list
    bad = set(cols) & set(MARKET_FEATURES)
    if bad:
        raise AssertionError(
            f"🚨 LEAKAGE GUARD: Training features include market columns: {sorted(bad)}\n"
            f"   Market features should ONLY be used at scoring time, not training!"
        )


# For clarity, export what should be used when
__all__ = [
    "ABILITY_FEATURES",
    "MARKET_FEATURES", 
    "guard_no_market",
]

