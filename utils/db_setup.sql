CREATE DATABASE IF NOT EXISTS mini_competition_db;

USE mini_competition_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    role ENUM('user', 'admin') DEFAULT 'user'
);
