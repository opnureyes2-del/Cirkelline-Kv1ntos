-- ═══════════════════════════════════════════════════════════════════════════════
-- AUDIT COMPLIANCE LOGS TABLE MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════════
-- Purpose: Long-term retention compliance audit trail
-- Compliance: GDPR Article 30, SOC 2 Type II
-- Retention: 7+ years (legal requirement)
--
-- Run: PGPASSWORD=cirkelline123 psql -h localhost -p 5532 -U cirkelline -d cirkelline -f migrations/audit_compliance_setup.sql

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- Create audit_compliance_logs table in ai schema
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ai.audit_compliance_logs (
    id BIGSERIAL PRIMARY KEY,

    -- Request correlation
    request_id VARCHAR(12) NOT NULL,

    -- Timestamp (immutable)
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Who performed action
    user_id VARCHAR(255) NOT NULL,

    -- What was done
    action VARCHAR(100) NOT NULL,

    -- What type of data/resource
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),

    -- API details
    endpoint VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,

    -- Client information
    ip_address VARCHAR(45),  -- IPv6 compatible
    user_agent VARCHAR(500),

    -- Performance
    duration_ms INTEGER,

    -- User context
    tier VARCHAR(20),
    is_admin BOOLEAN DEFAULT FALSE,

    -- Additional details (before/after for modifications)
    changes JSONB,

    -- Metadata
    metadata JSONB
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Indexes for efficient querying
-- ─────────────────────────────────────────────────────────────────────────────

-- Primary query patterns
CREATE INDEX IF NOT EXISTS idx_audit_compliance_user_id
    ON ai.audit_compliance_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_compliance_timestamp
    ON ai.audit_compliance_logs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_compliance_action
    ON ai.audit_compliance_logs(action);

CREATE INDEX IF NOT EXISTS idx_audit_compliance_resource_type
    ON ai.audit_compliance_logs(resource_type);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_audit_compliance_user_timestamp
    ON ai.audit_compliance_logs(user_id, timestamp DESC);

-- Index for compliance reporting
CREATE INDEX IF NOT EXISTS idx_audit_compliance_request_id
    ON ai.audit_compliance_logs(request_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- Partitioning by month (for large-scale retention)
-- ─────────────────────────────────────────────────────────────────────────────
-- Note: This is a placeholder. For production, implement table partitioning:
-- CREATE TABLE ai.audit_compliance_logs_2025_01 PARTITION OF ai.audit_compliance_logs
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- ─────────────────────────────────────────────────────────────────────────────
-- Comments for documentation
-- ─────────────────────────────────────────────────────────────────────────────

COMMENT ON TABLE ai.audit_compliance_logs IS
    'Compliance-grade audit trail for GDPR/SOC2. Append-only, 7+ year retention.';

COMMENT ON COLUMN ai.audit_compliance_logs.request_id IS
    'Correlation ID for tracing requests across services';

COMMENT ON COLUMN ai.audit_compliance_logs.action IS
    'Action type: auth_login, document_upload, data_export, etc.';

COMMENT ON COLUMN ai.audit_compliance_logs.changes IS
    'Before/after values for data modifications (GDPR requirement)';

-- ─────────────────────────────────────────────────────────────────────────────
-- Views for compliance reporting
-- ─────────────────────────────────────────────────────────────────────────────

-- Daily activity summary
CREATE OR REPLACE VIEW ai.audit_daily_summary AS
SELECT
    DATE(timestamp) as date,
    action,
    COUNT(*) as count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(duration_ms)::INTEGER as avg_duration_ms,
    COUNT(*) FILTER (WHERE status_code >= 400) as error_count
FROM ai.audit_compliance_logs
GROUP BY DATE(timestamp), action
ORDER BY date DESC, count DESC;

-- User activity report (for GDPR subject access requests)
CREATE OR REPLACE VIEW ai.audit_user_activity AS
SELECT
    user_id,
    action,
    resource_type,
    endpoint,
    timestamp,
    ip_address,
    status_code,
    duration_ms
FROM ai.audit_compliance_logs
ORDER BY timestamp DESC;

-- Security events (failed auth, permission denials)
CREATE OR REPLACE VIEW ai.audit_security_events AS
SELECT
    timestamp,
    user_id,
    action,
    endpoint,
    ip_address,
    status_code,
    metadata
FROM ai.audit_compliance_logs
WHERE action LIKE 'auth_%'
   OR action = 'rbac_access_denied'
   OR status_code >= 400
ORDER BY timestamp DESC;

COMMIT;

-- ─────────────────────────────────────────────────────────────────────────────
-- Verification
-- ─────────────────────────────────────────────────────────────────────────────

SELECT 'Audit Compliance Table Created' as status,
       COUNT(*) as column_count
FROM information_schema.columns
WHERE table_schema = 'ai'
  AND table_name = 'audit_compliance_logs';
