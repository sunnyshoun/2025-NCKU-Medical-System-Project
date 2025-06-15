-- Ensure UUID extension is installed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Creating roles table
CREATE TABLE IF NOT EXISTS roles (
    role_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
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
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    chat_context JSONB DEFAULT '[]'::jsonb
);

-- Creating user_roles table
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(role_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Creating records table
CREATE TABLE IF NOT EXISTS records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    corr_l TEXT,
    diopter_l TEXT,
    corr_r TEXT,
    diopter_r TEXT,
    unco_l TEXT NOT NULL,
    unco_r TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Creating knowledges table
CREATE TABLE IF NOT EXISTS knowledges (
    knowledge_id TEXT PRIMARY KEY,
    knowledge_point TEXT NOT NULL,
    tags TEXT[] NOT NULL,
    summary TEXT NOT NULL,
    source TEXT NOT NULL
);

-- Creating jwt_ids table
CREATE TABLE IF NOT EXISTS jwt_ids (
    jti TEXT PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE
);

-- Insert sample roles
INSERT INTO roles (role_id, name) VALUES 
(1, 'USER'),
(2, 'ADMIN')
ON CONFLICT (role_id) DO NOTHING;

-- Insert sample users
INSERT INTO users (id, username, password, email, age, gender, job, created_at, updated_at, chat_context) VALUES 
('123e4567-e89b-12d3-a456-426614174000', 'dockeruser', '$2y$10$oQTRm468nkTOz7IUCPnKZOpND1cgtaZBfN1btk.aH2D3V/v/.6ywW', 'dockeruser@example.com', 25, 'Male', 'Engineer', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '[{"role": "user", "content": "Hello, how can I use this app?"}, {"role": "assistant", "content": "Welcome! You can start by exploring the dashboard."}]'::jsonb),
('223e4567-e89b-12d3-a456-426614174001', 'janedoe', '$2y$10$oQTRm468nkTOz7IUCPnKZOpND1cgtaZBfN1btk.aH2D3V/v/.6ywW', 'janedoe@example.com', 30, 'Female', 'Data Scientist', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '[{"role": "user", "content": "Can you help with data analysis?"}, {"role": "assistant", "content": "Sure, I can assist with that!"}]'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- Insert sample user-role relationships
INSERT INTO user_roles (user_id, role_id) VALUES 
('123e4567-e89b-12d3-a456-426614174000', 1),
('223e4567-e89b-12d3-a456-426614174001', 1),
('223e4567-e89b-12d3-a456-426614174001', 2)
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Insert sample records
INSERT INTO records (record_id, user_id, corr_l, diopter_l, corr_r, diopter_r, unco_l, unco_r, created_at, updated_at) VALUES 
('aaaaaaaa-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', '1.0', '2.0D', '1.0', '1.5D', '0.4', '0.5', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('bbbbbbbb-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', '1.0', '2.0D', '1.0', '1.5D', '0.4', '0.5', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('cccccccc-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', '1.1', '1.9D', '1.0', '1.6D', '1.2', '1.2', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('dddddddd-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', NULL, '2.0D', '1.0', '1.5D', '0.4', '0.5', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('eeeeeeee-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', '0.0', NULL, '0.0', NULL, '2.0', '2.0', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('ffffffff-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', '0.5', '-2.0D', '-1.0', '1.5D', '1.0', '1.0', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('00000000-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', '1.1', '2.1D', NULL, NULL, '2.0', '2.0', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('11111111-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', NULL, NULL, NULL, NULL, '2.0', '2.0', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('22222222-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', '0.3', '0.6D', '0.9', '0.2D', '0.4', '0.5', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('33333333-bbbb-cccc-dddd-123412341234', '123e4567-e89b-12d3-a456-426614174000', '0.2', NULL, '1.0', '1.5D', '0.0', '0.0', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('44444444-bbbb-cccc-dddd-123412341234', '223e4567-e89b-12d3-a456-426614174001', '1.0', NULL, NULL, '2.0D', '0.2', '0.1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (record_id) DO NOTHING;

-- Insert sample knowledges
INSERT INTO knowledges (knowledge_id, knowledge_point, tags, summary, source) VALUES 
('initial-knowledge-1', '這是關於PostgreSQL的知識點。', ARRAY['database', 'PostgreSQL'], 'PostgreSQL是一個強大的開源關係型資料庫系統。', 'https://www.postgresql.org/'),
('initial-knowledge-2', 'Spring Security基礎', ARRAY['security', 'Spring'], 'Spring Security提供強大的認證和授權功能。', 'https://spring.io/projects/spring-security')
ON CONFLICT (knowledge_id) DO NOTHING;

-- Insert sample jwt_ids
INSERT INTO jwt_ids (jti, user_id) VALUES 
('jwt-001', '123e4567-e89b-12d3-a456-426614174000'),
('jwt-002', '223e4567-e89b-12d3-a456-426614174001')
ON CONFLICT (jti) DO NOTHING;