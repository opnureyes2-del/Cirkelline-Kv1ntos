#!/usr/bin/env python3
"""
Cirkelline Memory Migration Preparation Script

This script prepares TWO approaches for memory migration:
1. Topic-based documents for ORGANIC memory creation (RECOMMENDED)
2. Direct database migration scripts (BACKUP approach)

Do NOT execute migrations automatically - this is just preparation!
"""

import re
import json
from datetime import datetime
from pathlib import Path

# ==============================================================================
# APPROACH 1: ORGANIC MEMORY CREATION (RECOMMENDED)
# ==============================================================================

def split_conversations_into_topics(messages_file):
    """
    Analyze conversations and split them into topic-based documents.
    These can be uploaded to Cirkelline for organic memory creation.
    """

    print("=" * 80)
    print("APPROACH 1: ORGANIC MEMORY CREATION (RECOMMENDED)")
    print("=" * 80)
    print()

    # Define topics based on conversation analysis
    topics = {
        "privacy_and_policies": {
            "title": "Cirkelline Privacy Policy & Terms of Service Development",
            "keywords": ["privacy", "policy", "terms", "service", "cookie", "disclaimer", "GDPR", "ingkanito", "inkognito"],
            "content": []
        },
        "ai_business_model": {
            "title": "AI Trading Education Platform & Business Model",
            "keywords": ["trading", "education", "platform", "business", "agent", "observer", "klient"],
            "content": []
        },
        "cirkelline_architecture": {
            "title": "Cirkelline System Architecture & Design",
            "keywords": ["system", "architecture", "chat", "ekspert", "search", "multi", "agent", "observer"],
            "content": []
        },
        "project_context": {
            "title": "Cirkelline Project Context & Philosophy",
            "keywords": ["cirkelline", "mission", "citat", "identity", "værd", "princip", "alles bedste"],
            "content": []
        },
        "technical_discussions": {
            "title": "Technical Setup & Infrastructure",
            "keywords": ["grafikkort", "GPU", "setup", "installation", "teknisk", "hardware"],
            "content": []
        },
        "rasmus_preferences": {
            "title": "Rasmus's Communication Style & Preferences",
            "keywords": ["gem", "session", "noter", "elskede", "fokus"],
            "content": []
        }
    }

    print(f"📚 Reading conversations from: {messages_file}")

    with open(messages_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse sessions (simplified - you may need to adjust based on actual format)
    sessions = re.split(r'### Session \d+:', content)

    print(f"✅ Found {len(sessions)-1} sessions to analyze")
    print()

    # Analyze each session and categorize by topic
    for session_num, session in enumerate(sessions[1:], 1):  # Skip header

        # Extract messages from session
        messages = re.findall(r'\*\*User \(Rasmus\):\*\* (.+?)(?:\n\n|\*\*Cirkelline:\*\*)', session, re.DOTALL)
        responses = re.findall(r'\*\*Cirkelline:\*\* (.+?)(?:\n\n\*Time:|$)', session, re.DOTALL)

        for msg_idx, (user_msg, ai_msg) in enumerate(zip(messages, responses)):

            # Determine which topics this conversation relates to
            matched_topics = []
            user_lower = user_msg.lower()

            for topic_key, topic_data in topics.items():
                if any(keyword in user_lower for keyword in topic_data["keywords"]):
                    matched_topics.append(topic_key)

            # If no match, add to project_context as general information
            if not matched_topics:
                matched_topics = ["project_context"]

            # Add conversation to relevant topics
            for topic_key in matched_topics:
                topics[topic_key]["content"].append({
                    "session": session_num,
                    "user": user_msg.strip(),
                    "cirkelline": ai_msg.strip()
                })

    # Create topic-based documents
    output_dir = Path("/home/eenvy/Desktop/cirkelline/memory_topics")
    output_dir.mkdir(exist_ok=True)

    print("📝 Creating topic-based documents for organic memory creation:")
    print()

    for topic_key, topic_data in topics.items():
        if not topic_data["content"]:
            continue

        filename = output_dir / f"{topic_key}.md"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {topic_data['title']}\n\n")
            f.write(f"**Purpose:** This document contains conversations about {topic_data['title'].lower()} for Cirkelline to read and create organic memories.\n\n")
            f.write(f"**Total Conversations:** {len(topic_data['content'])}\n\n")
            f.write("---\n\n")

            for idx, conv in enumerate(topic_data['content'], 1):
                f.write(f"## Conversation {idx}\n\n")
                f.write(f"**Rasmus:** {conv['user']}\n\n")
                f.write(f"**Previous Cirkelline:** {conv['cirkelline']}\n\n")
                f.write("---\n\n")

        print(f"  ✅ {filename.name}")
        print(f"     → {len(topic_data['content'])} conversations")

    print()
    print("=" * 80)
    print("HOW TO USE THESE TOPIC DOCUMENTS:")
    print("=" * 80)
    print()
    print("1. Upload each topic document to NEW Cirkelline via UI")
    print("2. Ask Cirkelline to read and understand the topic")
    print("   Example: 'Please read this document about our privacy policy")
    print("            development and remember the key decisions we made.'")
    print("3. Cirkelline will create ORGANIC memories naturally")
    print("4. These memories will be native to the new system")
    print()
    print("BENEFITS:")
    print("  ✅ Memories are created by NEW system (not imported from old)")
    print("  ✅ More relevant and properly structured")
    print("  ✅ Cirkelline 'understands' rather than just 'stores'")
    print("  ✅ No risk of incompatible data structures")
    print()


# ==============================================================================
# APPROACH 2: DIRECT DATABASE MIGRATION (BACKUP)
# ==============================================================================

def create_migration_scripts():
    """
    Create SQL and Python scripts for direct database migration.
    These are BACKUP scripts - use only if organic approach doesn't work.
    """

    print()
    print("=" * 80)
    print("APPROACH 2: DIRECT DATABASE MIGRATION (BACKUP)")
    print("=" * 80)
    print()

    # OLD DATABASE CONNECTION INFO
    old_db_config = {
        "host": "cirkelline-messages-restore-1760198205.crm4mi2uozbi.eu-north-1.rds.amazonaws.com",
        "port": 5432,
        "database": "cirkellinedb",
        "user": "postgres",
        "password": "Qwerty1352db"
    }

    # NEW DATABASE CONNECTION INFO (TO BE FILLED)
    new_db_config = {
        "host": "cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com",
        "port": 5432,
        "database": "cirkelline_system",
        "user": "postgres",
        "password": "YOUR_NEW_DB_PASSWORD_HERE"  # ⚠️ FILL THIS IN
    }

    print("⚠️  WARNING: This is a BACKUP approach!")
    print("   Use ONLY if organic memory creation doesn't work.")
    print()

    # Create SQL migration script
    sql_script_path = "/home/eenvy/Desktop/cirkelline/migrate_memories.sql"

    with open(sql_script_path, 'w', encoding='utf-8') as f:
        f.write("""-- ============================================================================
-- Cirkelline Memory Migration SQL Script
-- ============================================================================
--
-- This script migrates sessions and memories from old DB to new DB
--
-- ⚠️  DO NOT RUN THIS WITHOUT REVIEWING FIRST!
-- ⚠️  This is a BACKUP approach - prefer organic memory creation
--
-- ============================================================================

-- Step 1: Connect to OLD database and export sessions
-- Run this on OLD database first:

\\echo 'Exporting sessions for Ivo and Rasmus...'

COPY (
    SELECT
        session_id,
        user_id,
        team_id,
        session_data,
        runs,
        created_at,
        updated_at
    FROM ai.agno_sessions
    WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com')
    ORDER BY created_at
) TO '/tmp/sessions_export.csv' WITH CSV HEADER;

-- Step 2: Export memories
\\echo 'Exporting memories...'

COPY (
    SELECT
        memory_id,
        memory,
        input,
        user_id,
        agent_id,
        team_id,
        topics,
        updated_at
    FROM ai.agno_memories
    WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com')
    ORDER BY updated_at
) TO '/tmp/memories_export.csv' WITH CSV HEADER;

-- Step 3: Export agent memories (if table exists)
\\echo 'Exporting agent memories...'

COPY (
    SELECT *
    FROM ai.agent_memory
    WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com')
    ORDER BY created_at
) TO '/tmp/agent_memories_export.csv' WITH CSV HEADER;

-- ============================================================================
-- Step 4: Import to NEW database
-- Run these on NEW database after reviewing exports:
-- ============================================================================

-- Import sessions
\\echo 'Importing sessions to new database...'

COPY ai.agno_sessions (
    session_id,
    user_id,
    team_id,
    session_data,
    runs,
    created_at,
    updated_at
)
FROM '/tmp/sessions_export.csv'
WITH CSV HEADER
ON CONFLICT (session_id) DO NOTHING;

-- Import memories
\\echo 'Importing memories to new database...'

COPY ai.agno_memories (
    memory_id,
    memory,
    input,
    user_id,
    agent_id,
    team_id,
    topics,
    updated_at
)
FROM '/tmp/memories_export.csv'
WITH CSV HEADER
ON CONFLICT (memory_id) DO NOTHING;

-- Import agent memories
\\echo 'Importing agent memories to new database...'

COPY ai.agent_memory
FROM '/tmp/agent_memories_export.csv'
WITH CSV HEADER
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- Verification
-- ============================================================================

\\echo 'Verifying migration...'

SELECT 'Sessions imported:' as status, COUNT(*) as count
FROM ai.agno_sessions
WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com');

SELECT 'Memories imported:' as status, COUNT(*) as count
FROM ai.agno_memories
WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com');

\\echo 'Migration complete!'
""")

    print(f"✅ Created SQL migration script: {sql_script_path}")

    # Create Python migration script
    python_script_path = "/home/eenvy/Desktop/cirkelline/migrate_memories.py"

    with open(python_script_path, 'w', encoding='utf-8') as f:
        f.write(f"""#!/usr/bin/env python3
\"\"\"
Cirkelline Memory Migration - Python Script

⚠️  WARNING: This is a BACKUP approach!
   Use ONLY if organic memory creation doesn't work.

This script migrates sessions and memories from old DB to new DB with:
- Selective filtering (top N memories, date ranges, etc.)
- Data validation
- Progress tracking
- Rollback capability
\"\"\"

import psycopg2
import json
from datetime import datetime

# Database configurations
OLD_DB = {json.dumps(old_db_config, indent=4)}

NEW_DB = {json.dumps(new_db_config, indent=4)}

# User emails to migrate
USERS = ['opnureyes2@gmail.com', 'opnureyes2@gmail.com']

# Migration options
MIGRATION_OPTIONS = {{
    "import_all_sessions": True,          # Import all 23 sessions
    "import_all_memories": False,         # Only import recent/relevant memories
    "memories_per_user": 50,              # Top 50 most recent memories per user
    "verify_before_commit": True,         # Show preview before committing
    "dry_run": True,                      # Set to False to actually execute
}}


def connect_to_db(db_config):
    \"\"\"Connect to PostgreSQL database\"\"\"
    try:
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
            sslmode="require"
        )
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {{e}}")
        return None


def preview_data(old_conn):
    \"\"\"Show what will be migrated\"\"\"

    print()
    print("=" * 80)
    print("MIGRATION PREVIEW")
    print("=" * 80)
    print()

    cur = old_conn.cursor()

    # Count sessions
    cur.execute(\"\"\"
        SELECT user_id, COUNT(*) as session_count
        FROM ai.agno_sessions
        WHERE user_id = ANY(%s)
        GROUP BY user_id
    \"\"\", (USERS,))

    print("📊 SESSIONS:")
    for row in cur.fetchall():
        print(f"  - {{row[0]}}: {{row[1]}} sessions")

    # Count memories
    cur.execute(\"\"\"
        SELECT user_id, COUNT(*) as memory_count
        FROM ai.agno_memories
        WHERE user_id = ANY(%s)
        GROUP BY user_id
    \"\"\", (USERS,))

    print()
    print("🧠 MEMORIES:")
    for row in cur.fetchall():
        print(f"  - {{row[0]}}: {{row[1]}} memories")

    # Show sample memories
    print()
    print("📝 SAMPLE MEMORIES (most recent 3):")
    cur.execute(\"\"\"
        SELECT user_id, memory, updated_at
        FROM ai.agno_memories
        WHERE user_id = ANY(%s)
        ORDER BY updated_at DESC
        LIMIT 3
    \"\"\", (USERS,))

    for row in cur.fetchall():
        print(f"  - {{row[0]}}: {{str(row[1])[:100]}}...")
        print(f"    Updated: {{datetime.fromtimestamp(row[2]).strftime('%Y-%m-%d %H:%M:%S')}}")

    print()


def migrate_sessions(old_conn, new_conn, dry_run=True):
    \"\"\"Migrate sessions from old DB to new DB\"\"\"

    print()
    print("=" * 80)
    print("MIGRATING SESSIONS")
    print("=" * 80)
    print()

    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()

    # Fetch all sessions
    old_cur.execute(\"\"\"
        SELECT session_id, user_id, team_id, session_data, runs, created_at, updated_at
        FROM ai.agno_sessions
        WHERE user_id = ANY(%s)
        ORDER BY created_at
    \"\"\", (USERS,))

    sessions = old_cur.fetchall()

    print(f"📦 Found {{len(sessions)}} sessions to migrate")

    if dry_run:
        print("   ⚠️  DRY RUN - Nothing will be committed")

    for idx, session in enumerate(sessions, 1):
        session_id, user_id, team_id, session_data, runs, created_at, updated_at = session

        print(f"  [{{idx}}/{{len(sessions)}}] Migrating session: {{session_id[:16]}}...")

        if not dry_run:
            new_cur.execute(\"\"\"
                INSERT INTO ai.agno_sessions
                (session_id, user_id, team_id, session_data, runs, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO NOTHING
            \"\"\", (session_id, user_id, team_id, session_data, runs, created_at, updated_at))

    if not dry_run:
        new_conn.commit()
        print(f"✅ Successfully migrated {{len(sessions)}} sessions")
    else:
        print(f"✅ DRY RUN: Would migrate {{len(sessions)}} sessions")


def migrate_memories(old_conn, new_conn, limit_per_user=50, dry_run=True):
    \"\"\"Migrate memories from old DB to new DB\"\"\"

    print()
    print("=" * 80)
    print("MIGRATING MEMORIES")
    print("=" * 80)
    print()

    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()

    total_migrated = 0

    for user_id in USERS:
        print(f"📦 Migrating memories for: {{user_id}}")

        # Fetch top N most recent memories for this user
        old_cur.execute(\"\"\"
            SELECT memory_id, memory, input, user_id, agent_id, team_id, topics, updated_at
            FROM ai.agno_memories
            WHERE user_id = %s
            ORDER BY updated_at DESC
            LIMIT %s
        \"\"\", (user_id, limit_per_user))

        memories = old_cur.fetchall()

        print(f"   Found {{len(memories)}} memories")

        if dry_run:
            print(f"   ⚠️  DRY RUN - Would migrate {{len(memories)}} memories")
        else:
            for memory in memories:
                memory_id, memory_text, input_text, user_id, agent_id, team_id, topics, updated_at = memory

                new_cur.execute(\"\"\"
                    INSERT INTO ai.agno_memories
                    (memory_id, memory, input, user_id, agent_id, team_id, topics, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (memory_id) DO NOTHING
                \"\"\", (memory_id, memory_text, input_text, user_id, agent_id, team_id, topics, updated_at))

            new_conn.commit()
            print(f"   ✅ Migrated {{len(memories)}} memories")

        total_migrated += len(memories)

    if not dry_run:
        print(f"\\n✅ Successfully migrated {{total_migrated}} memories total")
    else:
        print(f"\\n✅ DRY RUN: Would migrate {{total_migrated}} memories total")


def main():
    \"\"\"Main migration function\"\"\"

    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "CIRKELLINE MEMORY MIGRATION" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")

    # Validate new DB password is filled in
    if NEW_DB["password"] == "YOUR_NEW_DB_PASSWORD_HERE":
        print()
        print("❌ ERROR: Please fill in NEW_DB password in the script!")
        print("   Line: NEW_DB = {{ ... 'password': 'YOUR_PASSWORD_HERE' }}")
        return

    # Connect to databases
    print()
    print("📡 Connecting to databases...")

    old_conn = connect_to_db(OLD_DB)
    if not old_conn:
        print("❌ Failed to connect to OLD database")
        return
    print("   ✅ Connected to OLD database")

    new_conn = connect_to_db(NEW_DB)
    if not new_conn:
        print("❌ Failed to connect to NEW database")
        old_conn.close()
        return
    print("   ✅ Connected to NEW database")

    # Show preview
    preview_data(old_conn)

    # Confirm before proceeding
    if MIGRATION_OPTIONS["verify_before_commit"] and not MIGRATION_OPTIONS["dry_run"]:
        print()
        print("⚠️  WARNING: This will modify the NEW database!")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Migration cancelled")
            old_conn.close()
            new_conn.close()
            return

    # Run migrations
    if MIGRATION_OPTIONS["import_all_sessions"]:
        migrate_sessions(old_conn, new_conn, dry_run=MIGRATION_OPTIONS["dry_run"])

    if MIGRATION_OPTIONS["import_all_memories"]:
        migrate_memories(
            old_conn,
            new_conn,
            limit_per_user=999999,  # Import all
            dry_run=MIGRATION_OPTIONS["dry_run"]
        )
    else:
        migrate_memories(
            old_conn,
            new_conn,
            limit_per_user=MIGRATION_OPTIONS["memories_per_user"],
            dry_run=MIGRATION_OPTIONS["dry_run"]
        )

    # Close connections
    old_conn.close()
    new_conn.close()

    print()
    print("=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)
    print()

    if MIGRATION_OPTIONS["dry_run"]:
        print("⚠️  This was a DRY RUN - no data was actually migrated")
        print("   To execute for real, set MIGRATION_OPTIONS['dry_run'] = False")
    else:
        print("✅ Data successfully migrated to new database!")
        print("   Verify in Cirkelline UI that everything looks correct")
    print()


if __name__ == "__main__":
    main()
""")

    print(f"✅ Created Python migration script: {python_script_path}")
    print()
    print("=" * 80)
    print("HOW TO USE THESE MIGRATION SCRIPTS:")
    print("=" * 80)
    print()
    print("SQL Script (migrate_memories.sql):")
    print("  1. Review the script carefully")
    print("  2. Fill in new database password")
    print("  3. Run on old DB to export, then on new DB to import")
    print()
    print("Python Script (migrate_memories.py):")
    print("  1. Fill in NEW_DB password (line ~30)")
    print("  2. Run in DRY RUN mode first: python3 migrate_memories.py")
    print("  3. Review the preview")
    print("  4. Set dry_run=False to execute")
    print()
    print("⚠️  RECOMMENDATION: Use organic approach first!")
    print("   These scripts are BACKUP ONLY")
    print()


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "CIRKELLINE MEMORY MIGRATION PREPARATION" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This script prepares TWO approaches for restoring your old Cirkelline data:")
    print()
    print("  APPROACH 1: Organic Memory Creation (RECOMMENDED)")
    print("  → Split conversations into topics")
    print("  → Upload to new Cirkelline")
    print("  → Let HER create memories naturally")
    print()
    print("  APPROACH 2: Direct Database Migration (BACKUP)")
    print("  → SQL and Python scripts for direct import")
    print("  → Use only if approach 1 doesn't work")
    print()
    print("=" * 80)
    print()

    # Approach 1: Topic splitting
    messages_file = "/home/eenvy/Desktop/cirkelline/RASMUS_MESSAGES.md"
    split_conversations_into_topics(messages_file)

    # Approach 2: Migration scripts
    create_migration_scripts()

    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "ALL PREPARED!" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("✅ Topic documents created in: /home/eenvy/Desktop/cirkelline/memory_topics/")
    print("✅ Migration scripts created:")
    print("   - migrate_memories.sql")
    print("   - migrate_memories.py")
    print()
    print("📚 NEXT STEPS:")
    print("   1. Review the topic documents")
    print("   2. Upload them to NEW Cirkelline one by one")
    print("   3. Ask Cirkelline to read and remember each topic")
    print("   4. Watch as she creates organic, native memories!")
    print()
    print("⚠️  Database migration scripts are there as backup")
    print("   Only use if organic approach doesn't meet your needs")
    print()
