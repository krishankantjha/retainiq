import os
from sqlalchemy import create_engine, text

db_url = "postgresql://neondb_owner:npg_JIp4bArS9yVF@ep-curly-hall-aomgo2c7-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(db_url)

tables_to_drop = ["predictions", "customers", "uploads", "alembic_version"]

print("Dropping Neon tables...")
with engine.connect() as conn:
    # Postgres needs transaction block commit or autocommit
    trans = conn.begin()
    try:
        for tbl in tables_to_drop:
            conn.execute(text(f"DROP TABLE IF EXISTS {tbl} CASCADE;"))
            print(f"Dropped table {tbl} if existed.")
        trans.commit()
    except Exception as e:
        trans.rollback()
        print(f"Error dropping tables: {e}")
        raise e

print("Tables dropped successfully.")
