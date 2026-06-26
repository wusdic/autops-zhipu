# AUTOPS 数据架构设计

> 文档路径：`docs/01-architecture/DATA_ARCHITECTURE.md`
> 状态：current | 事实源：yes
> 数据库：MySQL 8.0+ / MariaDB 10.6+，字符集 utf8mb4
> 反向同步时间：2026-05-31（从实际运行数据库提取）
> 
> **本文件是数据库设计的唯一事实源。所有建表、种子数据、ORM 模型必须与此文档一致。**

---

## 1. 设计原则

### 1.1 命名规范

| 规则 | 说明 | 示例 |
|---|---|---|
| 表名 | 小写下划线，复数形式 | `assets`, `alert_rules` |
| 主键 | `id`，VARCHAR(36) UUID | `id varchar(36) NOT NULL` |
| 外键 | `{引用表单数}_id` | `asset_id`, `rule_id` |
| 时间戳 | `created_at`, `updated_at` | `datetime NOT NULL DEFAULT now()` |
| 布尔 | `is_{描述}` | `is_deleted tinyint(1)` |
| 状态 | `status` 或 `{实体}_status` | `status varchar(16)` |
| JSON | 存储为 TEXT，应用层序列化 | `tags text` |

### 1.2 通用约定

- 所有表使用 InnoDB 引擎，utf8mb4_unicode_ci 排序
- 主键均为 VARCHAR(36) UUID（非自增）
- 软删除：`is_deleted` + `deleted_at`
- 审计字段：`created_at`（必填，默认 now()）、`updated_at`
- 外键约束：ON DELETE CASCADE（子表随主表删除）

---

## 2. 外键关系图

```
users ─┬─ user_roles ──── roles
       ├─ api_keys
       └─ (audit_logs, tickets, etc. via user_id)

assets ─┬─ asset_ips
        ├─ asset_timeline
        ├─ asset_group_members ──── asset_groups (self-ref: parent_id)
        ├─ asset_relations (source/target)
        ├─ credential_bindings ──── credentials
        ├─ collection_jobs ─┬─ collectors
        │                    └─ credentials
        ├─ state_snapshots
        ├─ state_changes
        └─ events ──→ alerts ──── alert_rules

config_definitions ── config_versions ── config_bindings

scripts ── playbooks ── policies ── policy_executions
                      └─ executions ─┬─ execution_steps
                                     └─ execution_logs

tickets ── ticket_comments

knowledge_articles
ai_analyses
notifications
audit_logs
```

---

## 3. 全量表结构（DDL）


### 3.1 平台治理

### users
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `username` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `display_name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login_at` datetime DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### roles
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `permissions` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_builtin` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### user_roles
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_user_roles_user_id` (`user_id`),
  KEY `ix_user_roles_role_id` (`role_id`),
  CONSTRAINT `user_roles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `user_roles_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### api_keys
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `key_prefix` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL,
  `key_hash` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `scope` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `expires_at` datetime DEFAULT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_used_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_api_keys_key_prefix` (`key_prefix`),
  KEY `ix_api_keys_user_id` (`user_id`),
  CONSTRAINT `api_keys_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### audit_logs
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `trace_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `username` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `action` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `resource_type` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `resource_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `detail` text COLLATE utf8mb4_unicode_ci,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_audit_logs_user_id` (`user_id`),
  KEY `ix_audit_logs_trace_id` (`trace_id`),
  KEY `ix_audit_logs_action` (`action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```


### 3.2 资产中心

### assets
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `port` int DEFAULT NULL,
  `hostname` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `os_type` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `os_version` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `business_system` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `environment` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `health_status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reachability` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tags` text COLLATE utf8mb4_unicode_ci,
  `is_deleted` tinyint(1) NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_assets_ip` (`ip`),
  KEY `ix_assets_status` (`status`),
  KEY `ix_assets_asset_type` (`asset_type`),
  KEY `ix_assets_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### asset_groups
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `parent_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `parent_id` (`parent_id`),
  CONSTRAINT `asset_groups_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `asset_groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### asset_group_members
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_asset_group_members_asset_id` (`asset_id`),
  KEY `ix_asset_group_members_group_id` (`group_id`),
  CONSTRAINT `asset_group_members_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `asset_groups` (`id`) ON DELETE CASCADE,
  CONSTRAINT `asset_group_members_ibfk_2` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### asset_ips
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_primary` tinyint(1) NOT NULL,
  `interface` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_asset_ips_asset_id` (`asset_id`),
  KEY `ix_asset_ips_ip` (`ip`),
  CONSTRAINT `asset_ips_ibfk_1` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### asset_relations
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `target_asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `relation_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_asset_relations_target_asset_id` (`target_asset_id`),
  KEY `ix_asset_relations_source_asset_id` (`source_asset_id`),
  CONSTRAINT `asset_relations_ibfk_1` FOREIGN KEY (`source_asset_id`) REFERENCES `assets` (`id`) ON DELETE CASCADE,
  CONSTRAINT `asset_relations_ibfk_2` FOREIGN KEY (`target_asset_id`) REFERENCES `assets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### asset_timeline
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `event_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detail` text COLLATE utf8mb4_unicode_ci,
  `source` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_asset_timeline_event_type` (`event_type`),
  KEY `ix_asset_timeline_created_at` (`created_at`),
  KEY `ix_asset_timeline_asset_id` (`asset_id`),
  CONSTRAINT `asset_timeline_ibfk_1` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```


### 3.3 配置与凭证

### credentials
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `cred_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `encrypted_data` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `test_status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_tested_at` datetime DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### credential_bindings
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `credential_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_credential_bindings_credential_id` (`credential_id`),
  KEY `ix_credential_bindings_asset_id` (`asset_id`),
  CONSTRAINT `credential_bindings_ibfk_1` FOREIGN KEY (`credential_id`) REFERENCES `credentials` (`id`),
  CONSTRAINT `credential_bindings_ibfk_2` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### config_definitions
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `config_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `schema_def` text COLLATE utf8mb4_unicode_ci,
  `is_deleted` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### config_versions
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `definition_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version` int NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `published_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `published_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_config_versions_definition_id` (`definition_id`),
  CONSTRAINT `config_versions_ibfk_1` FOREIGN KEY (`definition_id`) REFERENCES `config_definitions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### config_bindings
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `target_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `target_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_config_bindings_version_id` (`version_id`),
  KEY `ix_config_bindings_target_id` (`target_id`),
  CONSTRAINT `config_bindings_ibfk_1` FOREIGN KEY (`version_id`) REFERENCES `config_versions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```


### 3.4 采集与状态

### collectors
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `collector_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `config_schema` text COLLATE utf8mb4_unicode_ci,
  `is_builtin` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### collection_jobs
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `collector_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `config_version_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `credential_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `schedule` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timeout` int NOT NULL,
  `last_run_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `credential_id` (`credential_id`),
  KEY `ix_collection_jobs_collector_id` (`collector_id`),
  KEY `ix_collection_jobs_asset_id` (`asset_id`),
  CONSTRAINT `collection_jobs_ibfk_1` FOREIGN KEY (`collector_id`) REFERENCES `collectors` (`id`),
  CONSTRAINT `collection_jobs_ibfk_2` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`id`),
  CONSTRAINT `collection_jobs_ibfk_3` FOREIGN KEY (`credential_id`) REFERENCES `credentials` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### collection_results
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `job_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `result_data` text COLLATE utf8mb4_unicode_ci,
  `error_message` text COLLATE utf8mb4_unicode_ci,
  `error_category` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `duration_ms` int DEFAULT NULL,
  `started_at` datetime NOT NULL,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_collection_results_job_id` (`job_id`),
  KEY `ix_collection_results_asset_id` (`asset_id`),
  CONSTRAINT `collection_results_ibfk_1` FOREIGN KEY (`job_id`) REFERENCES `collection_jobs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### state_snapshots
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `state_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `collected_at` datetime NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_state_snapshots_asset_id` (`asset_id`),
  CONSTRAINT `state_snapshots_ibfk_1` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### state_changes
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `state_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `old_status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `new_status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `old_value` text COLLATE utf8mb4_unicode_ci,
  `new_value` text COLLATE utf8mb4_unicode_ci,
  `snapshot_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_state_changes_created_at` (`created_at`),
  KEY `ix_state_changes_asset_id` (`asset_id`),
  CONSTRAINT `state_changes_ibfk_1` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```


### 3.5 事件与告警

### events
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `event_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `asset_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `title` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detail` text COLLATE utf8mb4_unicode_ci,
  `raw_data` text COLLATE utf8mb4_unicode_ci,
  `severity` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fingerprint` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_deduplicated` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_events_event_type` (`event_type`),
  KEY `ix_events_fingerprint` (`fingerprint`),
  KEY `ix_events_created_at` (`created_at`),
  KEY `ix_events_asset_id` (`asset_id`),
  CONSTRAINT `events_ibfk_1` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### alert_rules
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `event_types` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `conditions` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `severity` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `suppress_duration` int NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### alerts
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `severity` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rule_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `event_ids` text COLLATE utf8mb4_unicode_ci,
  `asset_ids` text COLLATE utf8mb4_unicode_ci,
  `context` text COLLATE utf8mb4_unicode_ci,
  `acknowledged_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `acknowledged_at` datetime DEFAULT NULL,
  `resolved_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `ticket_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `rule_id` (`rule_id`),
  KEY `ix_alerts_created_at` (`created_at`),
  KEY `ix_alerts_severity` (`severity`),
  KEY `ix_alerts_status` (`status`),
  CONSTRAINT `alerts_ibfk_1` FOREIGN KEY (`rule_id`) REFERENCES `alert_rules` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```


### 3.6 自动化引擎

### scripts
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `script_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `parameters` text COLLATE utf8mb4_unicode_ci,
  `timeout` int NOT NULL,
  `risk_level` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_blocked` tinyint(1) NOT NULL,
  `version` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### playbooks
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `steps` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `risk_level` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `version` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### policies
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `trigger_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `trigger_condition` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `scope` text COLLATE utf8mb4_unicode_ci,
  `action_chain` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `risk_level` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `requires_approval` tinyint(1) NOT NULL,
  `max_affected_assets` int NOT NULL,
  `verification_steps` text COLLATE utf8mb4_unicode_ci,
  `rollback_actions` text COLLATE utf8mb4_unicode_ci,
  `version` int NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### policy_executions
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `policy_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `policy_version` int NOT NULL,
  `alert_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trigger_event` text COLLATE utf8mb4_unicode_ci,
  `matched_assets` text COLLATE utf8mb4_unicode_ci,
  `execution_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `result` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_policy_executions_alert_id` (`alert_id`),
  KEY `ix_policy_executions_policy_id` (`policy_id`),
  CONSTRAINT `policy_executions_ibfk_1` FOREIGN KEY (`policy_id`) REFERENCES `policies` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### executions
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `execution_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `target_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_ids` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `parameters` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `trigger_source` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `trigger_source_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `policy_execution_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_dry_run` tinyint(1) NOT NULL,
  `risk_level` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `approved_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL,
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `result` text COLLATE utf8mb4_unicode_ci,
  `error_message` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_executions_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### execution_steps
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `execution_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `step_number` int NOT NULL,
  `script_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `parameters` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `result` text COLLATE utf8mb4_unicode_ci,
  `error_message` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_execution_steps_execution_id` (`execution_id`),
  CONSTRAINT `execution_steps_ibfk_1` FOREIGN KEY (`execution_id`) REFERENCES `executions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### execution_logs
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `execution_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `step_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `stream_type` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `offset` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_execution_logs_execution_id` (`execution_id`),
  KEY `ix_execution_logs_created_at` (`created_at`),
  KEY `ix_execution_logs_step_id` (`step_id`),
  CONSTRAINT `execution_logs_ibfk_1` FOREIGN KEY (`execution_id`) REFERENCES `executions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```


### 3.7 工单与协同

### tickets
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ticket_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `priority` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `context` text COLLATE utf8mb4_unicode_ci,
  `alert_ids` text COLLATE utf8mb4_unicode_ci,
  `execution_ids` text COLLATE utf8mb4_unicode_ci,
  `assigned_to` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `resolved_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `closed_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `closed_at` datetime DEFAULT NULL,
  `sla_deadline` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_tickets_assigned_to` (`assigned_to`),
  KEY `ix_tickets_status` (`status`),
  KEY `ix_tickets_ticket_type` (`ticket_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### ticket_comments
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ticket_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_ticket_comments_ticket_id` (`ticket_id`),
  CONSTRAINT `ticket_comments_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```


### 3.8 知识与AI

### knowledge_articles
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `article_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_types` text COLLATE utf8mb4_unicode_ci,
  `trigger_events` text COLLATE utf8mb4_unicode_ci,
  `diagnosis_steps` text COLLATE utf8mb4_unicode_ci,
  `action_steps` text COLLATE utf8mb4_unicode_ci,
  `verification_steps` text COLLATE utf8mb4_unicode_ci,
  `risk_level` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tags` text COLLATE utf8mb4_unicode_ci,
  `version` int NOT NULL,
  `published_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `published_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### ai_analyses
```sql
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `analysis_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `alert_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `asset_ids` text COLLATE utf8mb4_unicode_ci,
  `input_context` text COLLATE utf8mb4_unicode_ci,
  `model_name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `summary` text COLLATE utf8mb4_unicode_ci,
  `root_causes` text COLLATE utf8mb4_unicode_ci,
  `recommended_actions` text COLLATE utf8mb4_unicode_ci,
  `raw_output` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `error_message` text COLLATE utf8mb4_unicode_ci,
  `duration_ms` int DEFAULT NULL,
  `feedback_rating` int DEFAULT NULL,
  `feedback_comment` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_ai_analyses_alert_id` (`alert_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```


### 3.9 通知

### notifications
```sql
  `id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `type` varchar(32) NOT NULL,
  `title` varchar(256) NOT NULL,
  `message` text,
  `link` varchar(512) DEFAULT NULL,
  `ref_id` varchar(36) DEFAULT NULL,
  `read_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_notifications_user_id` (`user_id`),
  KEY `idx_notifications_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

---

## 附录 A. 0.7.0 新增表（迁移 0005–0009，2026-06-26）

> 部署须 `alembic upgrade head`。表总数 36 → **47**。

| 迁移 | 表/列 | 用途 |
|---|---|---|
| 0005 | `inspection_results.check_type`（列） | 巡检结果分类：baseline/resource/service/config/security/log/page |
| 0006 | `dictionaries` | 数据字典（type/code/label/value/sort_order/is_active） |
| 0006 | `tenants` | 租户（name/code/admin_user_id/resource_quota/feature_scope/status） |
| 0006 | `licenses` | 许可证（license_key/licensed_to/edition/max_assets/expires_at/status） |
| 0006 | `upgrade_history` | 升级历史（version/from_version/status/notes/operated_by） |
| 0006 | `model_agents` | 模型注册（name/provider/model_id/endpoint/api_key_enc/max_tokens/temperature/is_default/status） |
| 0006 | `system_settings` | 键值配置（skey/svalue），存模型/备份等全局配置 |
| 0006 | `backups` | 备份记录（name/backup_type/status/file_path/file_size/checksum/error） |
| 0007 | `inspection_rules` | 巡检规则（name/category/check_target/condition/severity/asset_types/enabled/last_triggered_at） |
| 0008 | `exports` | 导出任务（name/export_type/format/status/filters/file_path/file_size/row_count） |
| 0008 | `ticket_attachments` | 工单附件（ticket_id/filename/content_type/size/storage_path/uploaded_by） |
| 0009 | `trigger_history` | 触发历史（ref_type/ref_id/ref_name/action/status/detail） |

> 说明：`api_key_enc` 用凭证加密（`app/common/crypto.py`）存储，不回显明文。

