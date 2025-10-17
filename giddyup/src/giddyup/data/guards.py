"""
Data leakage prevention guards.

Ensures no market features leak into ability-only model training.
"""

import re
from typing import List

# Banned pattern - matches any market-related field names
BANNED = re.compile(
    r"(odds|price|rank|fav|bsp|sp|ip|wap|traded|overround|market|"
    r"official_rating|racing_post_rating|rpr|or\b)",
    re.IGNORECASE
)


def assert_no_market_features(df_cols: List[str], feature_cols: List[str]) -> None:
    """
    Assert that neither the dataframe nor feature list contains market-related columns.
    
    This is a critical guard against data leakage. Market features include:
    - Odds (decimal_odds, bsp, sp, ip, wap, etc.)
    - Rankings (market_rank, is_fav, etc.)
    - Expert ratings (official_rating, racing_post_rating)
    - Volume/trading data
    
    Args:
        df_cols: Columns in the dataframe
        feature_cols: Columns selected as features
        
    Raises:
        AssertionError: If market features found
    """
    bad_df = [c for c in df_cols if BANNED.search(c)]
    bad_fx = [c for c in feature_cols if BANNED.search(c)]
    
    if bad_df:
        raise AssertionError(
            f"🚫 DataFrame contains market-ish columns: {bad_df}\n"
            f"   These must be removed before training an ability-only model.\n"
            f"   Market features can only be used at SCORING time, not training."
        )
    
    if bad_fx:
        raise AssertionError(
            f"🚫 Feature list contains market-ish columns: {bad_fx}\n"
            f"   Remove these from ABILITY_FEATURES.\n"
            f"   For Path A, we train ONLY on ability features."
        )
    
    print("✅ Guard passed: No market features detected")


def check_feature_safety(feature_name: str) -> tuple[bool, str]:
    """
    Check if a single feature name is safe (not market-related).
    
    Args:
        feature_name: Feature column name
        
    Returns:
        (is_safe, reason) tuple
    """
    if BANNED.search(feature_name):
        return False, f"Matches banned pattern: {BANNED.pattern}"
    return True, "OK"


def get_safe_features(all_features: List[str]) -> List[str]:
    """
    Filter feature list to only safe (non-market) features.
    
    Args:
        all_features: Complete list of feature names
        
    Returns:
        Filtered list with only safe features
    """
    safe = []
    removed = []
    
    for feat in all_features:
        is_safe, reason = check_feature_safety(feat)
        if is_safe:
            safe.append(feat)
        else:
            removed.append((feat, reason))
    
    if removed:
        print(f"⚠️  Removed {len(removed)} unsafe features:")
        for feat, reason in removed:
            print(f"   - {feat}: {reason}")
    
    return safe

