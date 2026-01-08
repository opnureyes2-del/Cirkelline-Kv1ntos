"""
Manually create contents table if Agno doesn't provide initialization
Based on Agno's expected schema from documentation
"""
from my_os import db
from sqlalchemy import text

print("\n🔧 MANUALLY CREATING CONTENTS TABLE\n")

# Agno's standard contents table schema
create_table_sql = """
CREATE TABLE IF NOT EXISTS knowledge_contents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    metadata JSONB,
    type VARCHAR(50),
    size INTEGER,
    linked_to VARCHAR(255),
    access_count INTEGER DEFAULT 0,
    status VARCHAR(50),
    status_message TEXT,
    created_at BIGINT,
    updated_at BIGINT,
    external_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_metadata ON knowledge_contents USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_created_at ON knowledge_contents (created_at);
"""

try:
    with db.db_engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()

    print("✅ knowledge_contents table created")

    # Verify
    with db.db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'knowledge_contents'
        """))

        print("\nTable schema:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")

    print("\n✅ CONTENTS TABLE READY")

except Exception as e:
    print(f"❌ Error creating table: {e}")
    import traceback
    traceback.print_exc()
