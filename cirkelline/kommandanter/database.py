"""
Agent Learning Database Module
==============================

FASE 6: Multi-Bibliotek Arkitektur

Database interface for Historiker og Bibliotekar Kommandanter.
Separate from user data - this is for AI agent learning only.

Tables (in agent schema):
    - learning_domains
    - learning_events
    - learning_patterns
    - learning_content
    - learning_taxonomy
    - learning_relations
    - learning_index
    - learning_evolution_reports
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncpg
import json
import uuid


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5532
    database: str = "cirkelline"
    user: str = "cirkelline"
    password: str = "cirkelline123"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables."""
        db_url = os.getenv("DATABASE_URL", "")
        if db_url:
            # Parse postgresql+psycopg://user:pass@host:port/db
            # For asyncpg we need to strip the +psycopg
            db_url = db_url.replace("postgresql+psycopg://", "")
            try:
                auth, rest = db_url.split("@")
                user, password = auth.split(":")
                host_port, database = rest.split("/")
                host, port = host_port.split(":")
                return cls(
                    host=host,
                    port=int(port),
                    database=database,
                    user=user,
                    password=password
                )
            except ValueError:
                pass
        return cls()


class AgentLearningDB:
    """
    Database interface for Agent Learning System.

    Provides async methods for Historiker and Bibliotekar
    to persist and query learning data.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Connect to database."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=2,
                max_size=10
            )

    async def disconnect(self) -> None:
        """Disconnect from database."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def connection(self):
        """Get a database connection from the pool."""
        if not self._pool:
            await self.connect()
        async with self._pool.acquire() as conn:
            yield conn

    # ============================================
    # DOMAIN MANAGEMENT
    # ============================================

    async def get_domain(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """Get domain by name."""
        async with self.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM agent.learning_domains
                WHERE domain_name = $1
                """,
                domain_name
            )
            return dict(row) if row else None

    async def list_domains(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all registered domains."""
        async with self.connection() as conn:
            query = "SELECT * FROM agent.learning_domains"
            if active_only:
                query += " WHERE is_active = true"
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def initialize_domain(self, domain_name: str) -> None:
        """Mark a domain as initialized."""
        async with self.connection() as conn:
            await conn.execute(
                """
                UPDATE agent.learning_domains
                SET initialized_at = NOW(), updated_at = NOW()
                WHERE domain_name = $1
                """,
                domain_name
            )

    # ============================================
    # HISTORIKER: EVENTS
    # ============================================

    async def record_event(
        self,
        domain: str,
        topic: str,
        event_type: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        significance: float = 0.5,
        occurred_at: Optional[datetime] = None
    ) -> str:
        """Record a knowledge event."""
        event_id = str(uuid.uuid4())
        async with self.connection() as conn:
            await conn.execute(
                """
                INSERT INTO agent.learning_events
                (id, domain, topic, event_type, data, context, source, significance, occurred_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                uuid.UUID(event_id),
                domain,
                topic,
                event_type,
                json.dumps(data),
                json.dumps(context or {}),
                source,
                significance,
                occurred_at or datetime.utcnow()
            )
        return event_id

    async def get_events(
        self,
        domain: str,
        topic: Optional[str] = None,
        event_type: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get events with optional filters."""
        async with self.connection() as conn:
            query = """
                SELECT * FROM agent.learning_events
                WHERE domain = $1
            """
            params = [domain]
            param_idx = 2

            if topic and topic != "*":
                query += f" AND topic = ${param_idx}"
                params.append(topic)
                param_idx += 1

            if event_type:
                query += f" AND event_type = ${param_idx}"
                params.append(event_type)
                param_idx += 1

            if start:
                query += f" AND occurred_at >= ${param_idx}"
                params.append(start)
                param_idx += 1

            if end:
                query += f" AND occurred_at <= ${param_idx}"
                params.append(end)
                param_idx += 1

            query += f" ORDER BY occurred_at DESC LIMIT ${param_idx}"
            params.append(limit)

            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    # ============================================
    # HISTORIKER: PATTERNS
    # ============================================

    async def save_pattern(
        self,
        domain: str,
        pattern_name: str,
        description: str,
        strength: str,
        first_seen: datetime,
        last_seen: datetime,
        occurrences: int = 1,
        related_topics: Optional[List[str]] = None,
        related_events: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save or update a pattern."""
        pattern_id = str(uuid.uuid4())
        async with self.connection() as conn:
            # Try to update existing pattern
            result = await conn.execute(
                """
                UPDATE agent.learning_patterns
                SET description = $3,
                    strength = $4,
                    occurrences = occurrences + 1,
                    last_seen = $5,
                    related_topics = $6,
                    related_events = $7,
                    metadata = $8,
                    updated_at = NOW()
                WHERE domain = $1 AND pattern_name = $2
                """,
                domain,
                pattern_name,
                description,
                strength,
                last_seen,
                json.dumps(related_topics or []),
                json.dumps(related_events or []),
                json.dumps(metadata or {})
            )

            if result == "UPDATE 0":
                # Insert new pattern
                await conn.execute(
                    """
                    INSERT INTO agent.learning_patterns
                    (id, domain, pattern_name, description, strength, occurrences,
                     first_seen, last_seen, related_topics, related_events, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    uuid.UUID(pattern_id),
                    domain,
                    pattern_name,
                    description,
                    strength,
                    occurrences,
                    first_seen,
                    last_seen,
                    json.dumps(related_topics or []),
                    json.dumps(related_events or []),
                    json.dumps(metadata or {})
                )
        return pattern_id

    async def get_patterns(
        self,
        domain: str,
        window: Optional[timedelta] = None,
        min_strength: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get patterns for a domain."""
        async with self.connection() as conn:
            query = "SELECT * FROM agent.learning_patterns WHERE domain = $1"
            params = [domain]
            param_idx = 2

            if window:
                cutoff = datetime.utcnow() - window
                query += f" AND last_seen >= ${param_idx}"
                params.append(cutoff)
                param_idx += 1

            if min_strength:
                strength_order = {"weak": 1, "moderate": 2, "strong": 3, "dominant": 4}
                min_val = strength_order.get(min_strength, 1)
                strengths = [k for k, v in strength_order.items() if v >= min_val]
                query += f" AND strength = ANY(${param_idx})"
                params.append(strengths)

            query += " ORDER BY last_seen DESC"
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    # ============================================
    # BIBLIOTEKAR: TAXONOMY
    # ============================================

    async def get_taxonomy(self, domain: str) -> List[Dict[str, Any]]:
        """Get full taxonomy for a domain."""
        async with self.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM agent.learning_taxonomy
                WHERE domain = $1
                ORDER BY path
                """,
                domain
            )
            return [dict(row) for row in rows]

    async def add_taxonomy_category(
        self,
        domain: str,
        category_name: str,
        description: Optional[str] = None,
        parent_category: Optional[str] = None
    ) -> str:
        """Add a category to the taxonomy."""
        category_id = str(uuid.uuid4())
        async with self.connection() as conn:
            parent_id = None
            parent_path = ""
            depth = 0

            if parent_category:
                parent = await conn.fetchrow(
                    """
                    SELECT id, path, depth FROM agent.learning_taxonomy
                    WHERE domain = $1 AND category_name = $2
                    """,
                    domain,
                    parent_category
                )
                if parent:
                    parent_id = parent["id"]
                    parent_path = parent["path"]
                    depth = parent["depth"] + 1

            path = f"{parent_path}/{category_name}"

            await conn.execute(
                """
                INSERT INTO agent.learning_taxonomy
                (id, domain, category_name, description, parent_id, depth, path)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (domain, category_name) DO UPDATE
                SET description = EXCLUDED.description,
                    updated_at = NOW()
                """,
                uuid.UUID(category_id),
                domain,
                category_name,
                description,
                parent_id,
                depth,
                path
            )
        return category_id

    # ============================================
    # BIBLIOTEKAR: CONTENT
    # ============================================

    async def save_content(
        self,
        domain: str,
        title: str,
        body: str,
        content_type: str,
        source: Optional[str] = None,
        primary_category: Optional[str] = None,
        secondary_categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        classification_confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save content to the library."""
        content_id = str(uuid.uuid4())
        async with self.connection() as conn:
            # Get category ID if provided
            primary_category_id = None
            if primary_category:
                cat = await conn.fetchrow(
                    """
                    SELECT id FROM agent.learning_taxonomy
                    WHERE domain = $1 AND category_name = $2
                    """,
                    domain,
                    primary_category
                )
                if cat:
                    primary_category_id = cat["id"]

            await conn.execute(
                """
                INSERT INTO agent.learning_content
                (id, domain, title, body, content_type, source,
                 primary_category_id, primary_category, secondary_categories,
                 tags, classification_confidence, metadata, classified_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
                """,
                uuid.UUID(content_id),
                domain,
                title,
                body,
                content_type,
                source,
                primary_category_id,
                primary_category,
                json.dumps(secondary_categories or []),
                json.dumps(tags or []),
                classification_confidence,
                json.dumps(metadata or {})
            )
        return content_id

    async def search_content(
        self,
        domain: str,
        query: str,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        content_types: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search content with full-text search and filters."""
        async with self.connection() as conn:
            if query == "*":
                # List all content
                base_query = """
                    SELECT *, 1.0 as relevance_score
                    FROM agent.learning_content
                    WHERE domain = $1
                """
            else:
                # Full-text search
                base_query = """
                    SELECT *,
                           ts_rank(search_vector, websearch_to_tsquery('english', $2)) as relevance_score
                    FROM agent.learning_content
                    WHERE domain = $1
                    AND search_vector @@ websearch_to_tsquery('english', $2)
                """

            params = [domain]
            param_idx = 2

            if query != "*":
                params.append(query)
                param_idx += 1

            if categories:
                base_query += f" AND primary_category = ANY(${param_idx})"
                params.append(categories)
                param_idx += 1

            if tags:
                base_query += f" AND tags ?| ${param_idx}"
                params.append(tags)
                param_idx += 1

            if content_types:
                base_query += f" AND content_type = ANY(${param_idx})"
                params.append(content_types)
                param_idx += 1

            base_query += f" ORDER BY relevance_score DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.extend([limit, offset])

            rows = await conn.fetch(base_query, *params)
            return [dict(row) for row in rows]

    async def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Get content by ID."""
        async with self.connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agent.learning_content WHERE id = $1",
                uuid.UUID(content_id)
            )
            return dict(row) if row else None

    # ============================================
    # BIBLIOTEKAR: RELATIONS
    # ============================================

    async def add_relation(
        self,
        source_content_id: str,
        target_content_id: str,
        relationship_type: str,
        strength: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a relation between content items."""
        relation_id = str(uuid.uuid4())
        async with self.connection() as conn:
            await conn.execute(
                """
                INSERT INTO agent.learning_relations
                (id, source_content_id, target_content_id, relationship_type, strength, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (source_content_id, target_content_id, relationship_type)
                DO UPDATE SET strength = EXCLUDED.strength,
                              metadata = EXCLUDED.metadata
                """,
                uuid.UUID(relation_id),
                uuid.UUID(source_content_id),
                uuid.UUID(target_content_id),
                relationship_type,
                strength,
                json.dumps(metadata or {})
            )
        return relation_id

    async def get_related_content(
        self,
        content_id: str,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """Get related content with optional transitive relations."""
        async with self.connection() as conn:
            if depth == 1:
                # Direct relations only
                rows = await conn.fetch(
                    """
                    SELECT
                        r.relationship_type,
                        r.strength,
                        c.id, c.title, c.primary_category
                    FROM agent.learning_relations r
                    JOIN agent.learning_content c ON r.target_content_id = c.id
                    WHERE r.source_content_id = $1
                    ORDER BY r.strength DESC
                    """,
                    uuid.UUID(content_id)
                )
            else:
                # Recursive CTE for transitive relations
                rows = await conn.fetch(
                    """
                    WITH RECURSIVE related AS (
                        SELECT
                            target_content_id,
                            relationship_type,
                            strength,
                            1 as depth
                        FROM agent.learning_relations
                        WHERE source_content_id = $1

                        UNION ALL

                        SELECT
                            r.target_content_id,
                            r.relationship_type,
                            r.strength * 0.8,  -- Decay strength for transitive relations
                            rel.depth + 1
                        FROM agent.learning_relations r
                        JOIN related rel ON r.source_content_id = rel.target_content_id
                        WHERE rel.depth < $2
                    )
                    SELECT DISTINCT
                        rel.relationship_type,
                        rel.strength,
                        rel.depth,
                        c.id, c.title, c.primary_category
                    FROM related rel
                    JOIN agent.learning_content c ON rel.target_content_id = c.id
                    ORDER BY rel.depth, rel.strength DESC
                    """,
                    uuid.UUID(content_id),
                    depth
                )
            return [dict(row) for row in rows]

    # ============================================
    # BIBLIOTEKAR: INDEX
    # ============================================

    async def index_content(
        self,
        content_id: str,
        domain: str,
        terms: List[str],
        term_type: str = "keyword",
        weight: float = 1.0
    ) -> None:
        """Index content with specific terms."""
        async with self.connection() as conn:
            for term in terms:
                await conn.execute(
                    """
                    INSERT INTO agent.learning_index
                    (content_id, domain, term, term_type, weight)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (content_id, term, term_type) DO UPDATE
                    SET weight = EXCLUDED.weight,
                        indexed_at = NOW()
                    """,
                    uuid.UUID(content_id),
                    domain,
                    term.lower(),
                    term_type,
                    weight
                )

    async def update_content_indexed(self, content_id: str) -> None:
        """Mark content as indexed."""
        async with self.connection() as conn:
            await conn.execute(
                """
                UPDATE agent.learning_content
                SET indexed_at = NOW()
                WHERE id = $1
                """,
                uuid.UUID(content_id)
            )

    # ============================================
    # EVOLUTION REPORTS (Cached)
    # ============================================

    async def cache_evolution_report(
        self,
        domain: str,
        topic: str,
        period_days: int,
        key_milestones: List[Dict[str, Any]],
        trends: List[str],
        predictions: List[str],
        confidence: float,
        cache_hours: int = 24
    ) -> str:
        """Cache an evolution report."""
        report_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=cache_hours)

        async with self.connection() as conn:
            await conn.execute(
                """
                INSERT INTO agent.learning_evolution_reports
                (id, domain, topic, period_days, key_milestones, trends,
                 predictions, confidence, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (domain, topic, period_days) DO UPDATE
                SET key_milestones = EXCLUDED.key_milestones,
                    trends = EXCLUDED.trends,
                    predictions = EXCLUDED.predictions,
                    confidence = EXCLUDED.confidence,
                    generated_at = NOW(),
                    expires_at = EXCLUDED.expires_at
                """,
                uuid.UUID(report_id),
                domain,
                topic,
                period_days,
                json.dumps(key_milestones),
                json.dumps(trends),
                json.dumps(predictions),
                confidence,
                expires_at
            )
        return report_id

    async def get_cached_evolution_report(
        self,
        domain: str,
        topic: str,
        period_days: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached evolution report if not expired."""
        async with self.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM agent.learning_evolution_reports
                WHERE domain = $1 AND topic = $2 AND period_days = $3
                AND expires_at > NOW()
                """,
                domain,
                topic,
                period_days
            )
            return dict(row) if row else None


# Singleton instance
_db_instance: Optional[AgentLearningDB] = None


def get_agent_learning_db() -> AgentLearningDB:
    """Get the singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = AgentLearningDB()
    return _db_instance


async def initialize_agent_learning_db() -> AgentLearningDB:
    """Initialize and connect the database."""
    db = get_agent_learning_db()
    await db.connect()
    return db
