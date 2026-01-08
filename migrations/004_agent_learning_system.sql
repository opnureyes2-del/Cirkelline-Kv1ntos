-- Migration: 004 Agent Learning System
-- FASE 6: Multi-Bibliotek Arkitektur
--
-- Agent Learning Database Schema
-- IMPORTANT: Separate from user data - this is for AI agent learning only
--
-- Tabeller:
--   agent_learning_domains    - Registrerede videndomæner
--   agent_learning_events     - Historiker knowledge events
--   agent_learning_patterns   - Identificerede patterns i viden
--   agent_learning_content    - Bibliotekar content storage
--   agent_learning_taxonomy   - Kategori-hierarki per domæne
--   agent_learning_relations  - Relationer mellem indhold
--   agent_learning_index      - Søgeindeks for effektiv retrieval
--
-- Run: psql -U cirkelline -d cirkelline -f 004_agent_learning_system.sql

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS agent;

-- ============================================
-- 1. DOMAIN REGISTRY
-- ============================================
CREATE TABLE IF NOT EXISTS agent.learning_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Configuration
    config JSONB DEFAULT '{}',
    taxonomy_version VARCHAR(50) DEFAULT '1.0',

    -- Status
    is_active BOOLEAN DEFAULT true,
    initialized_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default domains
INSERT INTO agent.learning_domains (domain_name, display_name, description) VALUES
    ('web3', 'Web3 & Blockchain', 'Cryptocurrency, DeFi, smart contracts, and blockchain technology'),
    ('legal', 'Juridisk', 'Legal research, regulations, compliance, and legal documentation')
ON CONFLICT (domain_name) DO NOTHING;

-- ============================================
-- 2. HISTORIKER: KNOWLEDGE EVENTS
-- ============================================
-- Tracks all knowledge events recorded by domain Historiker
CREATE TABLE IF NOT EXISTS agent.learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100) NOT NULL REFERENCES agent.learning_domains(domain_name),

    -- Event Details
    topic VARCHAR(500) NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- created, updated, deprecated, validated, trend_detected, etc.

    -- Event Data
    data JSONB NOT NULL,
    context JSONB DEFAULT '{}',
    source VARCHAR(500),

    -- Significance
    significance FLOAT DEFAULT 0.5,  -- 0.0 - 1.0

    -- Timestamps
    occurred_at TIMESTAMP NOT NULL DEFAULT NOW(),
    recorded_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for fast timeline queries
    CONSTRAINT valid_significance CHECK (significance >= 0 AND significance <= 1)
);

CREATE INDEX IF NOT EXISTS idx_events_domain ON agent.learning_events(domain);
CREATE INDEX IF NOT EXISTS idx_events_topic ON agent.learning_events(topic);
CREATE INDEX IF NOT EXISTS idx_events_type ON agent.learning_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_occurred ON agent.learning_events(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_domain_occurred ON agent.learning_events(domain, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_topic_occurred ON agent.learning_events(topic, occurred_at DESC);

-- ============================================
-- 3. HISTORIKER: PATTERNS
-- ============================================
-- Identified patterns in knowledge evolution
CREATE TABLE IF NOT EXISTS agent.learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100) NOT NULL REFERENCES agent.learning_domains(domain_name),

    -- Pattern Details
    pattern_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,

    -- Strength
    strength VARCHAR(20) NOT NULL,  -- weak, moderate, strong, dominant
    occurrences INTEGER DEFAULT 1,

    -- Temporal
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,

    -- Related
    related_topics JSONB DEFAULT '[]',
    related_events JSONB DEFAULT '[]',

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patterns_domain ON agent.learning_patterns(domain);
CREATE INDEX IF NOT EXISTS idx_patterns_strength ON agent.learning_patterns(strength);
CREATE INDEX IF NOT EXISTS idx_patterns_last_seen ON agent.learning_patterns(last_seen DESC);

-- ============================================
-- 4. BIBLIOTEKAR: TAXONOMY
-- ============================================
-- Category hierarchy for each domain
CREATE TABLE IF NOT EXISTS agent.learning_taxonomy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100) NOT NULL REFERENCES agent.learning_domains(domain_name),

    -- Category Info
    category_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Hierarchy
    parent_id UUID REFERENCES agent.learning_taxonomy(id) ON DELETE SET NULL,
    depth INTEGER DEFAULT 0,
    path VARCHAR(1000),  -- Materialized path for fast hierarchy queries: /root/parent/child

    -- Stats
    item_count INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Unique per domain
    CONSTRAINT unique_category_per_domain UNIQUE (domain, category_name)
);

CREATE INDEX IF NOT EXISTS idx_taxonomy_domain ON agent.learning_taxonomy(domain);
CREATE INDEX IF NOT EXISTS idx_taxonomy_parent ON agent.learning_taxonomy(parent_id);
CREATE INDEX IF NOT EXISTS idx_taxonomy_path ON agent.learning_taxonomy(path);

-- ============================================
-- 5. BIBLIOTEKAR: CONTENT
-- ============================================
-- All indexed content in the library
CREATE TABLE IF NOT EXISTS agent.learning_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100) NOT NULL REFERENCES agent.learning_domains(domain_name),

    -- Content
    title VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,  -- research_finding, document, analysis, report, note, reference, external_link
    source VARCHAR(500),

    -- Classification
    primary_category_id UUID REFERENCES agent.learning_taxonomy(id),
    primary_category VARCHAR(255),  -- Denormalized for fast access
    secondary_categories JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    classification_confidence FLOAT DEFAULT 1.0,

    -- Search
    search_vector tsvector,  -- Full-text search

    -- Embedding
    embedding_id VARCHAR(100),  -- Reference to vector store

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    indexed_at TIMESTAMP,
    classified_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_content_domain ON agent.learning_content(domain);
CREATE INDEX IF NOT EXISTS idx_content_type ON agent.learning_content(content_type);
CREATE INDEX IF NOT EXISTS idx_content_category ON agent.learning_content(primary_category);
CREATE INDEX IF NOT EXISTS idx_content_search ON agent.learning_content USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_content_tags ON agent.learning_content USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_content_created ON agent.learning_content(created_at DESC);

-- Trigger to update search vector
CREATE OR REPLACE FUNCTION agent.update_content_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.body, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS content_search_vector_update ON agent.learning_content;
CREATE TRIGGER content_search_vector_update
    BEFORE INSERT OR UPDATE OF title, body ON agent.learning_content
    FOR EACH ROW
    EXECUTE FUNCTION agent.update_content_search_vector();

-- ============================================
-- 6. BIBLIOTEKAR: RELATIONS
-- ============================================
-- Relationships between content items
CREATE TABLE IF NOT EXISTS agent.learning_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relation
    source_content_id UUID NOT NULL REFERENCES agent.learning_content(id) ON DELETE CASCADE,
    target_content_id UUID NOT NULL REFERENCES agent.learning_content(id) ON DELETE CASCADE,

    -- Relation Type
    relationship_type VARCHAR(50) NOT NULL,  -- references, extends, contradicts, updates, related_to

    -- Strength
    strength FLOAT DEFAULT 0.5,  -- 0.0 - 1.0

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),

    -- No duplicate relations
    CONSTRAINT unique_relation UNIQUE (source_content_id, target_content_id, relationship_type),
    CONSTRAINT valid_strength CHECK (strength >= 0 AND strength <= 1),
    CONSTRAINT no_self_relation CHECK (source_content_id != target_content_id)
);

CREATE INDEX IF NOT EXISTS idx_relations_source ON agent.learning_relations(source_content_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON agent.learning_relations(target_content_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON agent.learning_relations(relationship_type);

-- ============================================
-- 7. INDEX ENTRIES (For Bibliotekar Search)
-- ============================================
-- Explicit index entries with term weights
CREATE TABLE IF NOT EXISTS agent.learning_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES agent.learning_content(id) ON DELETE CASCADE,
    domain VARCHAR(100) NOT NULL REFERENCES agent.learning_domains(domain_name),

    -- Term
    term VARCHAR(255) NOT NULL,
    term_type VARCHAR(50) DEFAULT 'keyword',  -- keyword, entity, concept, phrase

    -- Weight
    weight FLOAT DEFAULT 1.0,

    indexed_at TIMESTAMP DEFAULT NOW(),

    -- No duplicate term-content pairs
    CONSTRAINT unique_index_entry UNIQUE (content_id, term, term_type)
);

CREATE INDEX IF NOT EXISTS idx_index_domain ON agent.learning_index(domain);
CREATE INDEX IF NOT EXISTS idx_index_term ON agent.learning_index(term);
CREATE INDEX IF NOT EXISTS idx_index_term_type ON agent.learning_index(term_type);
CREATE INDEX IF NOT EXISTS idx_index_content ON agent.learning_index(content_id);

-- ============================================
-- 8. EVOLUTION REPORTS (Cached)
-- ============================================
-- Cached evolution reports for performance
CREATE TABLE IF NOT EXISTS agent.learning_evolution_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100) NOT NULL REFERENCES agent.learning_domains(domain_name),
    topic VARCHAR(500) NOT NULL,

    -- Report Content
    period_days INTEGER NOT NULL,
    key_milestones JSONB DEFAULT '[]',
    trends JSONB DEFAULT '[]',
    predictions JSONB DEFAULT '[]',
    confidence FLOAT DEFAULT 0.5,

    -- Cache
    generated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,

    -- Unique report per topic/period combo
    CONSTRAINT unique_evolution_report UNIQUE (domain, topic, period_days)
);

CREATE INDEX IF NOT EXISTS idx_evolution_domain ON agent.learning_evolution_reports(domain);
CREATE INDEX IF NOT EXISTS idx_evolution_topic ON agent.learning_evolution_reports(topic);
CREATE INDEX IF NOT EXISTS idx_evolution_expires ON agent.learning_evolution_reports(expires_at);

-- ============================================
-- 9. WEB3 DOMAIN: SPECIFIC TAXONOMY
-- ============================================
-- Insert Web3-specific taxonomy structure
INSERT INTO agent.learning_taxonomy (domain, category_name, description, path, depth) VALUES
    -- Root categories
    ('web3', 'DeFi', 'Decentralized Finance protocols and mechanisms', '/DeFi', 0),
    ('web3', 'Smart Contracts', 'Smart contract development and security', '/Smart Contracts', 0),
    ('web3', 'Governance', 'DAO governance and voting mechanisms', '/Governance', 0),
    ('web3', 'Security', 'Blockchain and smart contract security', '/Security', 0),
    ('web3', 'Infrastructure', 'Blockchain infrastructure and tooling', '/Infrastructure', 0),
    ('web3', 'NFT', 'Non-Fungible Tokens and digital assets', '/NFT', 0),
    ('web3', 'Layer 2', 'Layer 2 scaling solutions', '/Layer 2', 0),
    ('web3', 'Ecosystem', 'Blockchain ecosystem and community', '/Ecosystem', 0)
ON CONFLICT (domain, category_name) DO NOTHING;

-- Insert subcategories for DeFi
INSERT INTO agent.learning_taxonomy (domain, category_name, description, path, depth, parent_id)
SELECT 'web3', 'Lending Protocols', 'Lending and borrowing protocols', '/DeFi/Lending Protocols', 1, id
FROM agent.learning_taxonomy WHERE domain = 'web3' AND category_name = 'DeFi'
ON CONFLICT (domain, category_name) DO NOTHING;

INSERT INTO agent.learning_taxonomy (domain, category_name, description, path, depth, parent_id)
SELECT 'web3', 'AMM', 'Automated Market Makers', '/DeFi/AMM', 1, id
FROM agent.learning_taxonomy WHERE domain = 'web3' AND category_name = 'DeFi'
ON CONFLICT (domain, category_name) DO NOTHING;

INSERT INTO agent.learning_taxonomy (domain, category_name, description, path, depth, parent_id)
SELECT 'web3', 'Yield Farming', 'Yield farming strategies and protocols', '/DeFi/Yield Farming', 1, id
FROM agent.learning_taxonomy WHERE domain = 'web3' AND category_name = 'DeFi'
ON CONFLICT (domain, category_name) DO NOTHING;

-- ============================================
-- 10. LEGAL DOMAIN: SPECIFIC TAXONOMY
-- ============================================
INSERT INTO agent.learning_taxonomy (domain, category_name, description, path, depth) VALUES
    -- Root categories
    ('legal', 'Contract Law', 'Contract analysis and interpretation', '/Contract Law', 0),
    ('legal', 'Compliance', 'Regulatory compliance and requirements', '/Compliance', 0),
    ('legal', 'GDPR', 'General Data Protection Regulation', '/GDPR', 0),
    ('legal', 'Intellectual Property', 'IP rights, patents, and trademarks', '/Intellectual Property', 0),
    ('legal', 'Corporate Law', 'Corporate governance and business law', '/Corporate Law', 0),
    ('legal', 'Employment Law', 'Employment regulations and labor law', '/Employment Law', 0),
    ('legal', 'Litigation', 'Dispute resolution and litigation', '/Litigation', 0)
ON CONFLICT (domain, category_name) DO NOTHING;

-- ============================================
-- VERIFICATION
-- ============================================
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'agent'
    AND table_name LIKE 'learning_%';

    IF table_count >= 8 THEN
        RAISE NOTICE '✅ Agent Learning System: % tables created successfully', table_count;
    ELSE
        RAISE WARNING '⚠️ Expected 8+ tables, found %', table_count;
    END IF;
END $$;

-- Show created tables
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size('agent.' || table_name)) as size
FROM information_schema.tables
WHERE table_schema = 'agent'
ORDER BY table_name;
