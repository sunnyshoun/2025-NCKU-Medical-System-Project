-- Creating roles table
CREATE TABLE IF NOT EXISTS roles (
    role_id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Creating users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    age INTEGER,
    gender TEXT,
    job TEXT,
    updated_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Creating user_roles table
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id),
    role_id INTEGER REFERENCES roles(role_id),
    PRIMARY KEY (user_id, role_id)
);

-- Creating records table
CREATE TABLE IF NOT EXISTS records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    corr_l TEXT,
    diopter_l TEXT,
    corr_r TEXT,
    diopter_r TEXT,
    unco_l TEXT NOT NULL,
    unco_r TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP
);

-- Creating knowledges table
CREATE TABLE IF NOT EXISTS knowledges (
    knowledge_id TEXT PRIMARY KEY,
    knowledge_point TEXT NOT NULL,
    tags TEXT[] NOT NULL,
    summary TEXT NOT NULL,
    source TEXT NOT NULL
);

-- Creating jti table
CREATE TABLE IF NOT EXISTS jwt_ids (
    jti TEXT PRIMARY KEY,
    user_id UUID REFERENCES users(id)
);

-- 確保 UUID 擴充套件已安裝
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 插入基礎角色數據
-- <-- 關鍵修正：只插入 'USER'，移除 'ADMIN'
INSERT INTO roles (role_id, name) VALUES (1, 'USER') ON CONFLICT (role_id) DO NOTHING;
-- 移除：INSERT INTO roles (role_id, name) VALUES (2, 'ADMIN') ON CONFLICT (role_id) DO NOTHING;

-- 插入一個測試用戶和角色（可選）
INSERT INTO users (id, username, password, email, age, gender, job, created_at, updated_at)
VALUES (
    '123e4567-e89b-12d3-a456-426614174000',
    'dockeruser',
    '$2y$10$oQTRm468nkTOz7IUCPnKZOpND1cgtaZBfN1btk.aH2D3V/v/.6ywW', -- BCrypt hash ('password')
    'dockeruser@example.com',
    25, 'Male', 'Engineer',
    now(), now()
) ON CONFLICT (id) DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
VALUES ('123e4567-e89b-12d3-a456-426614174000', 1) -- 這裡的 role_id 1 對應 'USER'
ON CONFLICT (user_id, role_id) DO NOTHING;

INSERT INTO records (record_id, user_id, corr_l, diopter_l, corr_r, diopter_r, unco_l, unco_r, created_at, updated_at)
VALUES (
    'aaaaaaaa-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000',
    '1.0', '2.0D', '1.0', '1.5D', '0.4', '0.5',
    now(), now()
) ON CONFLICT (record_id) DO NOTHING;

INSERT INTO knowledges (knowledge_id, knowledge_point, tags, summary, source)
VALUES (
    'initial-knowledge-1',
    '這是關於PostgreSQL的知識點。',
    ARRAY['database', 'PostgreSQL'],
    'PostgreSQL是一個強大的開源關係型資料庫系統。',
    'https://www.postgresql.org/'
) ON CONFLICT (knowledge_id) DO NOTHING;