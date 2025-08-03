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
    user_id INTEGER REFERENCES users(id),
    problem_id VARCHAR(50) NOT NULL,
    language VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    judge_response JSONB
);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_problem_id ON submissions(problem_id);