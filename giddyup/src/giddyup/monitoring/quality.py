"""
Data Quality Monitoring

Basic data quality checks for the modeling pipeline.
Can be extended with Great Expectations for comprehensive validation.
"""

import polars as pl
from typing import Dict, List
from datetime import datetime


class DataQualityChecker:
    """
    Simple data quality validator.
    
    To be extended with Great Expectations for production.
    """
    
    def __init__(self, strict: bool = False):
        """
        Initialize checker.
        
        Args:
            strict: If True, raise errors on failures. If False, just warn.
        """
        self.strict = strict
        self.checks_passed = []
        self.checks_failed = []
    
    def check_gpr_coverage(self, df: pl.DataFrame, min_coverage: float = 0.95) -> bool:
        """
        Check that GPR is present for most runners.
        
        Args:
            df: DataFrame with GPR column
            min_coverage: Minimum fraction of non-null GPR values
            
        Returns:
            True if check passes
        """
        if "gpr" not in df.columns:
            self._record_failure("GPR column missing")
            return False
        
        total = len(df)
        non_null = df.filter(pl.col("gpr").is_not_null()).height
        coverage = non_null / max(1, total)
        
        if coverage >= min_coverage:
            self._record_pass(f"GPR coverage: {coverage:.1%} >= {min_coverage:.1%}")
            return True
        else:
            self._record_failure(f"GPR coverage too low: {coverage:.1%} < {min_coverage:.1%}")
            return False
    
    def check_market_snapshot_timing(
        self,
        df: pl.DataFrame,
        off_time_col: str = "off_time",
        snapshot_col: str = "snapshot_ts",
        min_minutes: int = 30,
        max_minutes: int = 90
    ) -> bool:
        """
        Check that market snapshot is within reasonable window before off time.
        
        Args:
            df: DataFrame with off_time and snapshot_ts
            off_time_col: Column name for race off time
            snapshot_col: Column name for snapshot timestamp
            min_minutes: Min minutes before off (default 30)
            max_minutes: Max minutes before off (default 90)
            
        Returns:
            True if check passes
        """
        if off_time_col not in df.columns or snapshot_col not in df.columns:
            self._record_failure(f"Missing columns: {off_time_col} or {snapshot_col}")
            return False
        
        df = df.with_columns([
            ((pl.col(off_time_col) - pl.col(snapshot_col)).dt.total_minutes()).alias("minutes_before_off")
        ])
        
        valid = df.filter(
            (pl.col("minutes_before_off") >= min_minutes) &
            (pl.col("minutes_before_off") <= max_minutes)
        ).height
        
        coverage = valid / max(1, len(df))
        
        if coverage >= 0.90:
            self._record_pass(f"Snapshot timing: {coverage:.1%} within {min_minutes}-{max_minutes} min window")
            return True
        else:
            self._record_failure(f"Snapshot timing poor: only {coverage:.1%} within window")
            return False
    
    def check_overround_range(
        self,
        df: pl.DataFrame,
        overround_col: str = "overround",
        min_overround: float = 1.00,
        max_overround: float = 1.40
    ) -> bool:
        """
        Check that race overround is in sensible range.
        
        Args:
            df: DataFrame with overround per race
            overround_col: Column name for overround
            min_overround: Min valid overround (default 1.0)
            max_overround: Max valid overround (default 1.4)
            
        Returns:
            True if check passes
        """
        if overround_col not in df.columns:
            self._record_failure(f"Missing column: {overround_col}")
            return False
        
        # Get unique race overrounds
        overrounds = df.select(["race_id", overround_col]).unique()[overround_col]
        
        valid = ((overrounds >= min_overround) & (overrounds <= max_overround)).sum()
        total = len(overrounds)
        coverage = valid / max(1, total)
        
        if coverage >= 0.95:
            self._record_pass(f"Overround range: {coverage:.1%} in [{min_overround:.2f}, {max_overround:.2f}]")
            return True
        else:
            self._record_failure(f"Overround range: only {coverage:.1%} in valid range")
            return False
    
    def check_feature_completeness(
        self,
        df: pl.DataFrame,
        required_features: List[str],
        max_null_fraction: float = 0.10
    ) -> bool:
        """
        Check that required features are mostly complete.
        
        Args:
            df: DataFrame with features
            required_features: List of required column names
            max_null_fraction: Max allowed null fraction (default 10%)
            
        Returns:
            True if all features pass
        """
        all_pass = True
        
        for feat in required_features:
            if feat not in df.columns:
                self._record_failure(f"Feature missing: {feat}")
                all_pass = False
                continue
            
            null_count = df.filter(pl.col(feat).is_null()).height
            null_frac = null_count / max(1, len(df))
            
            if null_frac <= max_null_fraction:
                self._record_pass(f"Feature {feat}: {null_frac:.1%} null <= {max_null_fraction:.1%}")
            else:
                self._record_failure(f"Feature {feat}: {null_frac:.1%} null > {max_null_fraction:.1%}")
                all_pass = False
        
        return all_pass
    
    def run_all_checks(self, df: pl.DataFrame, required_features: List[str] = None) -> Dict:
        """
        Run all quality checks.
        
        Args:
            df: DataFrame to validate
            required_features: List of required features (optional)
            
        Returns:
            dict with summary of results
        """
        print(f"\n🔍 Running Data Quality Checks on {len(df)} rows...")
        
        self.checks_passed = []
        self.checks_failed = []
        
        # Run checks
        self.check_gpr_coverage(df)
        
        if "snapshot_ts" in df.columns and "off_time" in df.columns:
            self.check_market_snapshot_timing(df)
        
        if "overround" in df.columns:
            self.check_overround_range(df)
        
        if required_features:
            self.check_feature_completeness(df, required_features)
        
        # Summary
        total_checks = len(self.checks_passed) + len(self.checks_failed)
        pass_rate = len(self.checks_passed) / max(1, total_checks)
        
        print(f"\n📊 Quality Check Summary:")
        print(f"   Passed: {len(self.checks_passed)}/{total_checks} ({pass_rate:.1%})")
        
        if self.checks_failed:
            print(f"\n❌ Failed Checks:")
            for fail in self.checks_failed:
                print(f"   - {fail}")
        
        if self.checks_passed:
            print(f"\n✅ Passed Checks:")
            for check in self.checks_passed:
                print(f"   - {check}")
        
        if self.strict and self.checks_failed:
            raise ValueError(f"Data quality checks failed: {len(self.checks_failed)} failures")
        
        return {
            "total_checks": total_checks,
            "passed": len(self.checks_passed),
            "failed": len(self.checks_failed),
            "pass_rate": pass_rate,
            "passed_checks": self.checks_passed,
            "failed_checks": self.checks_failed,
        }
    
    def _record_pass(self, message: str):
        """Record a passing check."""
        self.checks_passed.append(message)
    
    def _record_failure(self, message: str):
        """Record a failing check."""
        self.checks_failed.append(message)


def quick_check(df: pl.DataFrame, required_features: List[str] = None, strict: bool = False) -> bool:
    """
    Quick data quality check.
    
    Args:
        df: DataFrame to check
        required_features: Required feature columns
        strict: Raise error on failure
        
    Returns:
        True if all checks pass
    """
    checker = DataQualityChecker(strict=strict)
    results = checker.run_all_checks(df, required_features)
    return results["failed"] == 0

