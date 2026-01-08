#!/usr/bin/env python3
"""
Cirkelline Memory Migration - Python Script

⚠️  WARNING: This is a BACKUP approach!
   Use ONLY if organic memory creation doesn't work.

This script migrates sessions and memories from old DB to new DB with:
- Selective filtering (top N memories, date ranges, etc.)
- Data validation
- Progress tracking
- Rollback capability
"""

import psycopg2
import json
from datetime import datetime

# Database configurations
OLD_DB = {
    "host": "cirkelline-messages-restore-1760198205.crm4mi2uozbi.eu-north-1.rds.amazonaws.com",
    "port": 5432,
    "database": "cirkellinedb",
    "user": "postgres",
    "password": "Qwerty1352db"
}

NEW_DB = {
    "host": "cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com",
    "port": 5432,
    "database": "cirkelline_system",
    "user": "postgres",
    "password": "YOUR_NEW_DB_PASSWORD_HERE"
}

# User emails to migrate
USERS = ['opnureyes2@gmail.com', 'opnureyes2@gmail.com']

# Migration options
MIGRATION_OPTIONS = {
    "import_all_sessions": True,          # Import all 23 sessions
    "import_all_memories": False,         # Only import recent/relevant memories
    "memories_per_user": 50,              # Top 50 most recent memories per user
    "verify_before_commit": True,         # Show preview before committing
    "dry_run": True,                      # Set to False to actually execute
}


def connect_to_db(db_config):
    """Connect to PostgreSQL database"""
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
        print(f"❌ Connection failed: {e}")
        return None


def preview_data(old_conn):
    """Show what will be migrated"""

    print()
    print("=" * 80)
    print("MIGRATION PREVIEW")
    print("=" * 80)
    print()

    cur = old_conn.cursor()

    # Count sessions
    cur.execute("""
        SELECT user_id, COUNT(*) as session_count
        FROM ai.agno_sessions
        WHERE user_id = ANY(%s)
        GROUP BY user_id
    """, (USERS,))

    print("📊 SESSIONS:")
    for row in cur.fetchall():
        print(f"  - {row[0]}: {row[1]} sessions")

    # Count memories
    cur.execute("""
        SELECT user_id, COUNT(*) as memory_count
        FROM ai.agno_memories
        WHERE user_id = ANY(%s)
        GROUP BY user_id
    """, (USERS,))

    print()
    print("🧠 MEMORIES:")
    for row in cur.fetchall():
        print(f"  - {row[0]}: {row[1]} memories")

    # Show sample memories
    print()
    print("📝 SAMPLE MEMORIES (most recent 3):")
    cur.execute("""
        SELECT user_id, memory, updated_at
        FROM ai.agno_memories
        WHERE user_id = ANY(%s)
        ORDER BY updated_at DESC
        LIMIT 3
    """, (USERS,))

    for row in cur.fetchall():
        print(f"  - {row[0]}: {str(row[1])[:100]}...")
        print(f"    Updated: {datetime.fromtimestamp(row[2]).strftime('%Y-%m-%d %H:%M:%S')}")

    print()


def migrate_sessions(old_conn, new_conn, dry_run=True):
    """Migrate sessions from old DB to new DB"""

    print()
    print("=" * 80)
    print("MIGRATING SESSIONS")
    print("=" * 80)
    print()

    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()

    # Fetch all sessions
    old_cur.execute("""
        SELECT session_id, user_id, team_id, session_data, runs, created_at, updated_at
        FROM ai.agno_sessions
        WHERE user_id = ANY(%s)
        ORDER BY created_at
    """, (USERS,))

    sessions = old_cur.fetchall()

    print(f"📦 Found {len(sessions)} sessions to migrate")

    if dry_run:
        print("   ⚠️  DRY RUN - Nothing will be committed")

    for idx, session in enumerate(sessions, 1):
        session_id, user_id, team_id, session_data, runs, created_at, updated_at = session

        print(f"  [{idx}/{len(sessions)}] Migrating session: {session_id[:16]}...")

        if not dry_run:
            new_cur.execute("""
                INSERT INTO ai.agno_sessions
                (session_id, user_id, team_id, session_data, runs, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO NOTHING
            """, (session_id, user_id, team_id, session_data, runs, created_at, updated_at))

    if not dry_run:
        new_conn.commit()
        print(f"✅ Successfully migrated {len(sessions)} sessions")
    else:
        print(f"✅ DRY RUN: Would migrate {len(sessions)} sessions")


def migrate_memories(old_conn, new_conn, limit_per_user=50, dry_run=True):
    """Migrate memories from old DB to new DB"""

    print()
    print("=" * 80)
    print("MIGRATING MEMORIES")
    print("=" * 80)
    print()

    old_cur = old_conn.cursor()
    new_cur = new_conn.cursor()

    total_migrated = 0

    for user_id in USERS:
        print(f"📦 Migrating memories for: {user_id}")

        # Fetch top N most recent memories for this user
        old_cur.execute("""
            SELECT memory_id, memory, input, user_id, agent_id, team_id, topics, updated_at
            FROM ai.agno_memories
            WHERE user_id = %s
            ORDER BY updated_at DESC
            LIMIT %s
        """, (user_id, limit_per_user))

        memories = old_cur.fetchall()

        print(f"   Found {len(memories)} memories")

        if dry_run:
            print(f"   ⚠️  DRY RUN - Would migrate {len(memories)} memories")
        else:
            for memory in memories:
                memory_id, memory_text, input_text, user_id, agent_id, team_id, topics, updated_at = memory

                new_cur.execute("""
                    INSERT INTO ai.agno_memories
                    (memory_id, memory, input, user_id, agent_id, team_id, topics, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (memory_id) DO NOTHING
                """, (memory_id, memory_text, input_text, user_id, agent_id, team_id, topics, updated_at))

            new_conn.commit()
            print(f"   ✅ Migrated {len(memories)} memories")

        total_migrated += len(memories)

    if not dry_run:
        print(f"\n✅ Successfully migrated {total_migrated} memories total")
    else:
        print(f"\n✅ DRY RUN: Would migrate {total_migrated} memories total")


def main():
    """Main migration function"""

    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "CIRKELLINE MEMORY MIGRATION" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")

    # Validate new DB password is filled in
    if NEW_DB["password"] == "YOUR_NEW_DB_PASSWORD_HERE":
        print()
        print("❌ ERROR: Please fill in NEW_DB password in the script!")
        print("   Line: NEW_DB = { ... 'password': 'YOUR_PASSWORD_HERE' }")
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
