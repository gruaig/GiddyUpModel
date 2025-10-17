"""
Smoke test for signal publishing.

Creates a demo signal row and publishes it to modeling.signals
to verify the entire pipeline works end-to-end.
"""

import datetime as dt
from giddyup.publish.signals import publish


def main():
    """Run smoke test."""
    print("🧪 Running smoke test for signal publishing...")
    
    # Create a demo signal row
    demo_signal = {
        "race_id": 123456,
        "horse_id": 42,
        "model_id": 1,                 # Temporary - will create proper model later
        "p_win": 0.12,
        "p_place": None,
        "fair_odds_win": 1 / 0.12,     # ~8.33
        "fair_odds_place": None,
        "best_odds_win": 10.0,
        "best_odds_src": "exchange",
        "ew_places": 4,
        "ew_fraction": "1/5",
        "edge_win": 0.12 * (10 - 1) - (1 - 0.12),  # EV calculation
        "edge_ew": None,
        "kelly_fraction": 0.04,
        "stake_units": 0.20,
        "liquidity_ok": True,
        "reasons": [
            {"feature": "speed_fig", "impact": 0.7},
            {"feature": "trainer_14d", "impact": 0.2},
            {"feature": "draw_bias", "impact": 0.1},
        ],
        "as_of": dt.datetime.utcnow(),
    }
    
    print(f"\n📊 Demo signal:")
    print(f"   Race ID: {demo_signal['race_id']}")
    print(f"   Horse ID: {demo_signal['horse_id']}")
    print(f"   Win Probability: {demo_signal['p_win']:.1%}")
    print(f"   Fair Odds: {demo_signal['fair_odds_win']:.2f}")
    print(f"   Best Market Odds: {demo_signal['best_odds_win']:.2f}")
    print(f"   Edge: {demo_signal['edge_win']:.3f}")
    print(f"   Kelly Fraction: {demo_signal['kelly_fraction']:.1%}")
    print(f"   Recommended Stake: {demo_signal['stake_units']:.2f} units")
    
    # Publish to database
    print(f"\n💾 Publishing to modeling.signals...")
    rows_written = publish([demo_signal])
    
    print(f"\n✅ Success! Wrote {rows_written} row(s) to modeling.signals")
    print("\n🔍 Verify with SQL:")
    print("   SELECT race_id, horse_id, p_win, best_odds_win, edge_win")
    print("   FROM modeling.signals")
    print("   ORDER BY signal_id DESC")
    print("   LIMIT 1;")


if __name__ == "__main__":
    main()

