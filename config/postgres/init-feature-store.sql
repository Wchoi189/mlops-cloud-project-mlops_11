-- PostgreSQL 초기화 스크립트 - 2단계 피처 스토어용

-- 피처 스토어 데이터베이스 설정
\c mlops;

-- 피처 메타데이터 확장 설치
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 피처 스토어용 스키마 생성
CREATE SCHEMA IF NOT EXISTS feature_store;

-- 피처 메타데이터 테이블 (이미 feature_store.py에서 생성되지만 백업용)
CREATE TABLE IF NOT EXISTS feature_store.feature_metadata_backup (
    feature_name VARCHAR(255) PRIMARY KEY,
    feature_group VARCHAR(255),
    data_type TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version VARCHAR(50),
    file_path TEXT,
    size_bytes BIGINT,
    record_count INTEGER
);

-- 피처 그룹 테이블
CREATE TABLE IF NOT EXISTS feature_store.feature_groups_backup (
    group_name VARCHAR(255) PRIMARY KEY,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    features TEXT
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_feature_metadata_group ON feature_store.feature_metadata_backup(feature_group);
CREATE INDEX IF NOT EXISTS idx_feature_metadata_created ON feature_store.feature_metadata_backup(created_at);

-- 사용자 권한 설정
GRANT ALL PRIVILEGES ON SCHEMA feature_store TO mlops_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA feature_store TO mlops_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA feature_store TO mlops_user;

-- 완료 메시지
\echo 'Feature Store PostgreSQL 초기화 완료'
