-- PostgreSQL Database Setup for Mini-Competition
-- Run this script to create the database and tables

-- Create database (run this as superuser)
-- CREATE DATABASE mini_competition_db;

-- Connect to the database
-- \c mini_competition_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin'))
);

-- Create submissions table for tracking user submissions
CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    problem_id VARCHAR(50) NOT NULL,
    language VARCHAR(50) NOT NULL,
    submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    judge_response JSONB,
    execution_time DECIMAL(10,3),
    memory_used INTEGER,
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS contests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    problems JSONB
);

CREATE TABLE IF NOT EXISTS contest_participants (
    id SERIAL PRIMARY KEY,
    contest_id INTEGER REFERENCES contests(id),
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create contest_submissions table for leaderboard functionality
CREATE TABLE IF NOT EXISTS contest_submissions (
    id SERIAL PRIMARY KEY,
    contest_id INTEGER REFERENCES contests(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    problem_id VARCHAR(50) NOT NULL,
    submission_id INTEGER REFERENCES submissions(id) ON DELETE CASCADE,
    submission_time TIMESTAMP NOT NULL,
    is_accepted BOOLEAN DEFAULT FALSE,
    score INTEGER DEFAULT 0,
    penalty_time INTEGER DEFAULT 0,  -- Time penalty for wrong submissions (in minutes)
    contest_start_time TIMESTAMP NOT NULL,  -- Contest start for validation
    contest_end_time TIMESTAMP NOT NULL,   -- Contest end for validation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_contest_submissions_contest_user ON contest_submissions(contest_id, user_id);
CREATE INDEX idx_contest_submissions_contest_problem ON contest_submissions(contest_id, problem_id);
CREATE INDEX idx_contest_submissions_time ON contest_submissions(submission_time);
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_problem_id ON submissions(problem_id);
