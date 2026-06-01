-- Event Outbox 表 — 用于事件持久化
-- 与应用表一起由 init SQL 或 Alembic 创建

CREATE TABLE IF NOT EXISTS event_outbox (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_id VARCHAR(36) NOT NULL UNIQUE,
    event_type VARCHAR(128) NOT NULL,
    domain VARCHAR(64) NOT NULL,
    payload JSON,
    priority TINYINT DEFAULT 1,
    source VARCHAR(128) DEFAULT '',
    status ENUM('pending', 'done', 'dead') NOT NULL DEFAULT 'pending',
    error VARCHAR(512) DEFAULT NULL,
    retry_count TINYINT DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME DEFAULT NULL,
    INDEX idx_outbox_status (status, created_at),
    INDEX idx_outbox_event_type (event_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
