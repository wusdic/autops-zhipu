-- AUTOPS MySQL 初始化脚本
CREATE DATABASE IF NOT EXISTS autops CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE autops;

-- 表结构由 Alembic 迁移或 SQLAlchemy create_all 自动创建
-- 此文件仅用于 Docker 初始化时确保数据库存在
