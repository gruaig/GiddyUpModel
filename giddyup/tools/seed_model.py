"""
Seed a demo model into modeling.models table.

This creates a placeholder model entry that the smoke test can reference.
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import json


def main():
    """Seed demo model."""
    load_dotenv()
    
    dsn = os.getenv("PG_DSN")
    if not dsn:
        raise SystemExit("❌ Error: PG_DSN missing in .env file")
    
    engine = create_engine(dsn, pool_pre_ping=True)
    
    print("🌱 Seeding demo model into modeling.models...")
    
    # Insert a demo model
    insert_sql = text("""
    INSERT INTO modeling.models (
        name, version, stage, artifact_uri, metrics_json
    ) VALUES (
        :name, :version, :stage, :artifact_uri, :metrics_json
    )
    ON CONFLICT (name, version) DO UPDATE
    SET stage = EXCLUDED.stage,
        artifact_uri = EXCLUDED.artifact_uri,
        metrics_json = EXCLUDED.metrics_json
    RETURNING model_id;
    """)
    
    model_data = {
        "name": "hrd_win_prob",
        "version": "0.0.1",
        "stage": "development",
        "artifact_uri": "file:///tmp/demo_model",
        "metrics_json": json.dumps({
            "log_loss": 0.42,
            "accuracy": 0.35,
            "auc_roc": 0.68,
        }),
    }
    
    with engine.begin() as connection:
        result = connection.execute(insert_sql, model_data)
        model_id = result.scalar()
    
    print(f"\n✅ Seeded model:")
    print(f"   Model ID: {model_id}")
    print(f"   Name: {model_data['name']}")
    print(f"   Version: {model_data['version']}")
    print(f"   Stage: {model_data['stage']}")
    print("\n💡 You can now run the smoke test with model_id={model_id}")


if __name__ == "__main__":
    main()

