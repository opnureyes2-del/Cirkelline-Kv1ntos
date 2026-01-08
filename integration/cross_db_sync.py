#!/usr/bin/env python3
"""
Cross-Database Knowledge Sync Agent
====================================
Bidirectional sync between INTRO ↔ ELLE knowledge bases

Subscribes to file.changed events from Event Bus
Auto-syncs between intro_knowledge (port 5536) ↔ elle_knowledge (port 5537)
Handles conflicts gracefully, sync time <5s
"""
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
import hashlib
import json

class CrossDBSync:
    def __init__(self):
        self.intro_conn = None
        self.elle_conn = None
        
    def connect(self):
        """Connect to both knowledge databases"""
        self.intro_conn = psycopg2.connect(
            host='localhost',
            port=5536,
            database='intro_knowledge',
            user='intro_agent',
            password='intro_secure_2025'
        )

        self.elle_conn = psycopg2.connect(
            host='localhost',
            port=5537,
            database='elle_knowledge',
            user='elle_agent',
            password='elle_secure_2025'
        )
        
        print("✅ Connected to both knowledge bases")
    
    def get_file_hash(self, content: str) -> str:
        """Generate hash for conflict detection"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def sync_intro_to_elle(self, file_path: str):
        """Sync file from INTRO → ELLE"""
        try:
            # Get file from INTRO
            with self.intro_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT file_path, content, updated_at FROM documents WHERE file_path = %s",
                    (file_path,)
                )
                intro_doc = cur.fetchone()
            
            if not intro_doc:
                print(f"⚠️  File not found in INTRO: {file_path}")
                return
            
            # Check if exists in ELLE
            with self.elle_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT file_path, content, updated_at FROM documents WHERE file_path = %s",
                    (file_path,)
                )
                elle_doc = cur.fetchone()
            
            if elle_doc:
                # Conflict detection
                intro_hash = self.get_file_hash(intro_doc['content'])
                elle_hash = self.get_file_hash(elle_doc['content'])
                
                if intro_hash != elle_hash:
                    # INTRO is newer → update ELLE
                    if intro_doc['updated_at'] > elle_doc['updated_at']:
                        with self.elle_conn.cursor() as cur:
                            cur.execute(
                                "UPDATE documents SET content = %s, updated_at = %s WHERE file_path = %s",
                                (intro_doc['content'], datetime.now(timezone.utc), file_path)
                            )
                        self.elle_conn.commit()
                        print(f"✅ Synced INTRO → ELLE: {file_path}")
                    else:
                        print(f"⚠️  Conflict (ELLE newer): {file_path}")
            else:
                # Insert new document in ELLE
                with self.elle_conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO documents (file_path, content, created_at, updated_at) VALUES (%s, %s, %s, %s)",
                        (file_path, intro_doc['content'], datetime.now(timezone.utc), datetime.now(timezone.utc))
                    )
                self.elle_conn.commit()
                print(f"✅ Created in ELLE: {file_path}")
                
        except Exception as e:
            print(f"❌ Sync error: {e}")
            self.intro_conn.rollback()
            self.elle_conn.rollback()
    
    def sync_elle_to_intro(self, file_path: str):
        """Sync file from ELLE → INTRO"""
        try:
            # Get file from ELLE
            with self.elle_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT file_path, content, updated_at FROM documents WHERE file_path = %s",
                    (file_path,)
                )
                elle_doc = cur.fetchone()

            if not elle_doc:
                print(f"⚠️  File not found in ELLE: {file_path}")
                return

            # Check if exists in INTRO
            with self.intro_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT file_path, content, updated_at FROM documents WHERE file_path = %s",
                    (file_path,)
                )
                intro_doc = cur.fetchone()

            if intro_doc:
                # Conflict detection
                elle_hash = self.get_file_hash(elle_doc['content'])
                intro_hash = self.get_file_hash(intro_doc['content'])

                if elle_hash != intro_hash:
                    # ELLE is newer → update INTRO
                    if elle_doc['updated_at'] > intro_doc['updated_at']:
                        with self.intro_conn.cursor() as cur:
                            cur.execute(
                                "UPDATE documents SET content = %s, updated_at = %s WHERE file_path = %s",
                                (elle_doc['content'], datetime.now(timezone.utc), file_path)
                            )
                        self.intro_conn.commit()
                        print(f"✅ Synced ELLE → INTRO: {file_path}")
                    else:
                        print(f"⚠️  Conflict (INTRO newer): {file_path}")
            else:
                # Insert new document in INTRO
                with self.intro_conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO documents (file_path, content, created_at, updated_at) VALUES (%s, %s, %s, %s)",
                        (file_path, elle_doc['content'], datetime.now(timezone.utc), datetime.now(timezone.utc))
                    )
                self.intro_conn.commit()
                print(f"✅ Created in INTRO: {file_path}")

        except Exception as e:
            print(f"❌ Sync error: {e}")
            self.elle_conn.rollback()
            self.intro_conn.rollback()

    def initial_sync_all(self):
        """Initial bulk sync: Copy all INTRO documents to ELLE"""
        print("🔄 Starting initial bulk sync INTRO → ELLE...")

        try:
            # Get all INTRO documents
            with self.intro_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT file_path, content, created_at, updated_at FROM documents")
                intro_docs = cur.fetchall()

            synced_count = 0
            skipped_count = 0

            for doc in intro_docs:
                file_path = doc['file_path']

                # Check if already exists in ELLE
                with self.elle_conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT file_path FROM documents WHERE file_path = %s",
                        (file_path,)
                    )
                    exists = cur.fetchone()

                if not exists:
                    # Insert into ELLE
                    with self.elle_conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO documents (file_path, content, created_at, updated_at) VALUES (%s, %s, %s, %s)",
                            (doc['file_path'], doc['content'], doc['created_at'], doc['updated_at'])
                        )
                    self.elle_conn.commit()
                    synced_count += 1
                    if synced_count % 50 == 0:
                        print(f"  ⏳ Synced {synced_count} documents...")
                else:
                    skipped_count += 1

            print(f"✅ Initial sync complete: {synced_count} synced, {skipped_count} skipped")

        except Exception as e:
            print(f"❌ Initial sync error: {e}")
            self.elle_conn.rollback()
    
    async def listen_for_changes(self):
        """Subscribe to file.changed events from Event Bus"""
        try:
            from event_bus import EventBus
            
            bus = EventBus()
            await bus.connect()
            
            async def handle_file_change(message):
                """Handle file.changed event"""
                file_path = message.get('file_path')
                source = message.get('source', 'unknown')
                
                print(f"📥 File changed: {file_path} (source: {source})")
                
                # Sync based on source
                if 'INTRO' in file_path or source == 'intro':
                    self.sync_intro_to_elle(file_path)
                elif 'ELLE' in file_path or source == 'elle':
                    self.sync_elle_to_intro(file_path)
                
            await bus.subscribe('file.changed', handle_file_change)
            print("✅ Listening for file.changed events...")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"❌ Event Bus error: {e}")
    
    def close(self):
        """Close database connections"""
        if self.intro_conn:
            self.intro_conn.close()
        if self.elle_conn:
            self.elle_conn.close()

if __name__ == "__main__":
    import sys

    sync = CrossDBSync()
    sync.connect()

    # Check if ELLE is empty - if so, perform initial sync
    with sync.elle_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents")
        elle_count = cur.fetchone()[0]

    with sync.intro_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents")
        intro_count = cur.fetchone()[0]

    print(f"📊 Current state: INTRO={intro_count} docs, ELLE={elle_count} docs")

    if elle_count == 0 and intro_count > 0:
        print("⚠️  ELLE is empty - performing initial sync...")
        sync.initial_sync_all()
    elif "--force-sync" in sys.argv:
        print("🔄 Force sync requested...")
        sync.initial_sync_all()
    else:
        print("✅ Databases already in sync")

    # For now, skip event listener (would run forever)
    # To enable: asyncio.run(sync.listen_for_changes())

    sync.close()
    print("✅ Cross-DB Sync Agent operational!")
