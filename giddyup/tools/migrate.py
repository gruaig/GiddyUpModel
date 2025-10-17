"""
Migration runner for GiddyUp modeling schema.

Reads and executes SQL migration files in order.
"""

import os
import pathlib
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


def main():
    """Apply database migrations."""
    # Load environment variables from .env
    load_dotenv()
    
    # Get database connection string
    dsn = os.getenv("PG_DSN")
    if not dsn:
        raise SystemExit("❌ Error: PG_DSN missing in .env file")
    
    print(f"📊 Connecting to database...")
    engine = create_engine(dsn, pool_pre_ping=True)
    
    # Path to migrations directory
    migrations_dir = pathlib.Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "001_modeling_schema.sql"
    
    if not migration_file.exists():
        raise SystemExit(f"❌ Error: Migration file not found: {migration_file}")
    
    print(f"📄 Reading migration: {migration_file.name}")
    sql = migration_file.read_text(encoding="utf-8")
    
    # Remove comments and split into statements
    lines = []
    for line in sql.split('\n'):
        # Remove inline comments
        if '--' in line:
            line = line[:line.index('--')]
        line = line.strip()
        if line:
            lines.append(line)
    
    # Join and split by semicolon
    clean_sql = ' '.join(lines)
    statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
    
    print(f"🔧 Executing {len(statements)} SQL statements...")
    
    try:
        with engine.begin() as connection:
            for i, stmt in enumerate(statements, 1):
                # Get first few words for display
                preview = ' '.join(stmt.split()[0:5])
                print(f"   [{i}/{len(statements)}] {preview}...")
                connection.execute(text(stmt))
        
        print("\n✅ Migration completed successfully!")
        print("\nCreated:")
        print("  - modeling schema")
        print("  - modeling.models table")
        print("  - modeling.signals table")
        print("  - modeling.bets table")
        print("  - Indexes and constraints")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()

