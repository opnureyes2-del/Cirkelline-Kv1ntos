"""Check what table name Agno is using for knowledge"""
from my_os import knowledge, db

print(f"\n🔍 Agno Configuration:\n")
print(f"Contents DB table name: {db.knowledge_table_name}")
print(f"Database URL: {db.db_url}")
print(f"Schema: {db.db_schema}")

print(f"\nKnowledge object:")
print(f"  Type: {type(knowledge)}")
print(f"  Has contents_db: {hasattr(knowledge, 'contents_db')}")
if hasattr(knowledge, 'contents_db'):
    print(f"  Contents DB: {knowledge.contents_db}")
    print(f"  Contents DB table: {knowledge.contents_db.knowledge_table_name}")
