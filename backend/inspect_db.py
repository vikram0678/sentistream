import os
from sqlalchemy import create_engine, inspect, text

# Load database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentiment_user:your_secure_password@localhost:5432/sentiment_db")

def verify_schema():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("--- 1. Schema Structure (4 Points) ---")
    tables = inspector.get_table_names()
    required_tables = ["social_media_posts", "sentiment_analysis", "sentiment_alerts"]
    
    for table in required_tables:
        if table in tables:
            print(f"✅ Table '{table}' exists.")
            columns = {c['name']: str(c['type']) for c in inspector.get_columns(table)}
            print(f"   Columns: {columns}")
        else:
            print(f"❌ Table '{table}' is MISSING.")

    print("\n--- 2. Relationships (2 Points) ---")
    fk_analysis = inspector.get_foreign_keys("sentiment_analysis")
    if any(fk['referred_table'] == 'social_media_posts' for fk in fk_analysis):
        print("✅ Foreign Key: sentiment_analysis -> social_media_posts verified.")
    else:
        print("❌ Foreign Key MISSING in sentiment_analysis.")

    print("\n--- 3. Indexes (2 Points) ---")
    required_indexes = {
        "social_media_posts": ["post_id", "source", "created_at"],
        "sentiment_analysis": ["analyzed_at"],
        "sentiment_alerts": ["triggered_at"]
    }
    
    for table, req_cols in required_indexes.items():
        indexes = [idx['column_names'][0] for idx in inspector.get_indexes(table) if idx['column_names']]
        for col in req_cols:
            if col in indexes or any(c['name'] == col and c.get('primary_key') for c in inspector.get_columns(table)):
                print(f"✅ Index/PK on {table}.{col} verified.")
            else:
                print(f"❌ MISSING Index on {table}.{col}")

    print("\n--- 4. Data Insertion (1 Point) ---")
    try:
        with engine.connect() as conn:
            # Clear previous test data
            conn.execute(text("DELETE FROM social_media_posts WHERE post_id='test_schema_1'"))
            # Insert test
            conn.execute(text("""
                INSERT INTO social_media_posts (post_id, source, content, author, created_at, ingested_at) 
                VALUES ('test_schema_1', 'test', 'Verifying schema', 'bot', NOW(), NOW())
            """))
            conn.commit()
            print("✅ Test data insertion successful.")
    except Exception as e:
        print(f"❌ Data insertion FAILED: {e}")

if __name__ == "__main__":
    verify_schema()