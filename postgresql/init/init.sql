-- Creating roles table
CREATE TABLE roles (
    roleID INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Creating users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    age TEXT,
    gender TEXT,
    job TEXT,
    updatedAt TIMESTAMP,
    createdAt TIMESTAMP DEFAULT now()
);

-- Creating user_roles table
CREATE TABLE user_roles (
    userID UUID REFERENCES users(id),
    roleID INTEGER REFERENCES roles(roleID),
    PRIMARY KEY (userID, roleID)
);

-- Creating records table
CREATE TABLE records (
    recordID BIGINT PRIMARY KEY,
    userID UUID REFERENCES users(id),
    corr_l TEXT,
    diopter_l TEXT,
    corr_r TEXT,
    diopter_r TEXT,
    unco_l TEXT NOT NULL,
    unco_r TEXT NOT NULL,
    createdAt TIMESTAMP DEFAULT now(),
    updatedAt TIMESTAMP
);

-- Inserting a test user
INSERT INTO users (id, username, password, email, age, gender, job, createdAt)
VALUES (
    '123e4567-e89b-12d3-a456-426614174000',
    'testuser',
    '$2a$10$8j9k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j', -- BCrypt hash
    'testuser@example.com',
    '30',
    'Male',
    'Developer',
    now()
);

-- Inserting a test role
INSERT INTO roles (roleID, name)
VALUES (1, 'USER');

-- Assigning role to test user
INSERT INTO user_roles (userID, roleID)
VALUES ('123e4567-e89b-12d3-a456-426614174000', 1);

-- Inserting a test record
INSERT INTO records (
    recordID, userID, corr_l, diopter_l, corr_r, diopter_r, unco_l, unco_r
)
VALUES (
    1,
    '123e4567-e89b-12d3-a456-426614174000',
    '1.0',
    '2.0D',
    '1.0',
    '1.5D',
    '0.4',
    '0.5'
)