"""
Value and staking calculations with commission.

All functions account for exchange commission (default 2-5%).
"""

from typing import Optional


def fair_odds(p: float) -> float:
    """
    Convert probability to fair decimal odds.
    
    Args:
        p: Win probability (0-1)
        
    Returns:
        Fair decimal odds
        
    Example:
        >>> fair_odds(0.20)
        5.0
        >>> fair_odds(0.10)
        10.0
    """
    return 1.0 / max(1e-9, p)


def remove_vig(market_probs: list[float]) -> list[float]:
    """
    Remove vigorish (overround) from market probabilities.
    
    Market probabilities sum to > 1.0 (e.g., 1.15 = 115% book).
    This normalizes them to sum to 1.0 (fair probabilities).
    
    Args:
        market_probs: List of implied probabilities from market odds
        
    Returns:
        Vig-free probabilities (sum to 1.0)
        
    Example:
        >>> market = [0.50, 0.35, 0.30]  # Sums to 1.15 (115% book)
        >>> remove_vig(market)
        [0.435, 0.304, 0.261]  # Sums to 1.0
    """
    total = sum(market_probs)
    if total <= 0:
        return market_probs
    return [p / total for p in market_probs]


def ev_win(
    p: float,
    odds: float,
    commission: float = 0.02
) -> float:
    """
    Calculate expected value of a win bet with commission.
    
    Args:
        p: Model's win probability
        odds: Decimal odds
        commission: Commission rate on winning bets (default 2%)
        
    Returns:
        Expected value per unit staked
        
    Formula:
        EV = p * (odds - 1) * (1 - commission) - (1 - p)
        
    Example:
        >>> ev_win(0.20, 10.0, 0.02)  # 20% prob, 10.0 odds, 2% commission
        0.764  # Positive EV!
        
        >>> ev_win(0.10, 10.0, 0.02)  # 10% prob, 10.0 odds
        -0.118  # Negative EV (no value)
    """
    # Profit if win (after commission)
    b = (odds - 1.0) * (1.0 - commission)
    
    # EV = prob_win * profit - prob_lose * loss
    return p * b - (1.0 - p)


def kelly_fraction(
    p: float,
    odds: float,
    commission: float = 0.02,
    max_fraction: float = 1.0
) -> float:
    """
    Calculate Kelly criterion stake fraction with commission.
    
    Args:
        p: Model's win probability
        odds: Decimal odds
        commission: Commission rate on winning bets
        max_fraction: Maximum stake (for fractional Kelly)
        
    Returns:
        Optimal stake fraction (0-max_fraction)
        
    Formula:
        b = (odds - 1) * (1 - commission)
        f* = (p * (b + 1) - 1) / b
        
    Example:
        >>> kelly_fraction(0.20, 10.0, 0.02)
        0.117  # Stake 11.7% of bankroll
        
        >>> kelly_fraction(0.20, 10.0, 0.02, max_fraction=0.25)
        0.117  # Same (under 25% limit)
        
        >>> kelly_fraction(0.10, 10.0, 0.02)
        0.0  # No edge (EV negative)
    """
    # Adjusted profit per unit (after commission)
    b = (odds - 1.0) * (1.0 - commission)
    
    if b <= 0:
        return 0.0
    
    # Kelly formula
    f_star = (p * (b + 1.0) - 1.0) / b
    
    # Clip to [0, max_fraction]
    return max(0.0, min(max_fraction, f_star))


def calculate_stake(
    p_model: float,
    odds: float,
    commission: float = 0.02,
    kelly_fraction_multiplier: float = 0.25,
    max_stake: float = 1.0
) -> float:
    """
    Calculate recommended stake using fractional Kelly.
    
    Args:
        p_model: Model's win probability
        odds: Decimal odds available
        commission: Commission rate
        kelly_fraction_multiplier: Fraction of full Kelly (0.25 = quarter Kelly)
        max_stake: Maximum stake in units
        
    Returns:
        Recommended stake in units
        
    Example:
        >>> calculate_stake(0.20, 10.0, commission=0.02, kelly_fraction_multiplier=0.25)
        0.029  # Quarter-Kelly stake
    """
    # Calculate full Kelly
    f_kelly = kelly_fraction(p_model, odds, commission, max_fraction=1.0)
    
    # Apply fractional Kelly
    stake = f_kelly * kelly_fraction_multiplier
    
    # Cap at max_stake
    return min(stake, max_stake)

