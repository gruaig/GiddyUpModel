"""
Quick test of GPR computation on a small dataset.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
from giddyup.ratings.gpr import compute_gpr, make_distance_band, lbs_per_length

def test_distance_bands():
    """Test distance band logic."""
    print("Testing distance bands...")
    assert make_distance_band(5.5) == '5-6f'
    assert make_distance_band(8.0) == '7-9f'
    assert make_distance_band(11.0) == '10-12f'
    assert make_distance_band(14.0) == '12f+'
    print("   ✅ Distance bands OK")

def test_lbs_per_length():
    """Test lbs per length logic."""
    print("Testing lbs per length...")
    assert lbs_per_length('5-6f') == 3.8
    assert lbs_per_length('7-9f') == 3.0
    assert lbs_per_length('12f+') == 2.0
    print("   ✅ Lbs per length OK")

def test_gpr_computation():
    """Test GPR computation on synthetic data."""
    print("Testing GPR computation...")
    
    # Create synthetic runs
    df = pl.DataFrame({
        'horse_id': [1, 1, 1, 2, 2, 3],
        'race_id': [100, 101, 102, 103, 104, 105],
        'race_date': ['2023-01-01', '2023-02-01', '2023-03-01', 
                      '2023-01-15', '2023-02-15', '2023-01-20'],
        'dist_f': [8.0, 8.0, 10.0, 6.0, 6.0, 12.0],
        'btn': [0.0, 2.0, 1.0, 0.0, 5.0, 3.0],
        'lbs': [130, 132, 128, 125, 126, 135],
        'course_id': [1, 1, 2, 1, 1, 3],
        'going': ['Good', 'Soft', 'Good', 'Firm', 'Good', 'Heavy'],
        'class': ['Class 3', 'Class 2', 'Class 3', 'Class 4', 'Class 3', 'Class 2'],
        'pos_num': [1, 3, 2, 1, 8, 4],
    })
    
    # Convert date to Date type
    df = df.with_columns(pl.col('race_date').str.strptime(pl.Date, "%Y-%m-%d"))
    
    # Compute GPR
    gpr_df = compute_gpr(df, half_life_days=120.0, shrinkage_k=4.0, prior_rating=75.0)
    
    print(f"   Computed GPR for {len(gpr_df)} horses")
    print(gpr_df)
    
    # Verify output structure
    assert 'horse_id' in gpr_df.columns
    assert 'gpr' in gpr_df.columns
    assert 'gpr_sigma' in gpr_df.columns
    assert 'n_runs' in gpr_df.columns
    
    print("   ✅ GPR computation OK")

if __name__ == "__main__":
    print("🧪 Testing GPR Module")
    print("=" * 60)
    
    test_distance_bands()
    test_lbs_per_length()
    test_gpr_computation()
    
    print("\n✅ All tests passed!")

