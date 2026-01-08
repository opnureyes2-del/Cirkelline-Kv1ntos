"""Check what's actually in the database"""
from my_os import db
from sqlalchemy import text
import json

print("\n🔍 CHECKING UPLOADED FILES\n")

with db.db_engine.connect() as conn:
    result = conn.execute(text("""
        SELECT name, metadata
        FROM ai.agno_knowledge
        ORDER BY created_at DESC
        LIMIT 10
    """))

    for row in result:
        name = row[0]
        metadata = row[1]

        print(f"📄 {name}")
        print(f"   user_id: {metadata.get('user_id', 'MISSING!')}")
        print(f"   access_level: {metadata.get('access_level', 'MISSING!')}")
        print(f"   Full metadata: {json.dumps(metadata, indent=4)}")
        print()
