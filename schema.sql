-- Create database
CREATE DATABASE IF NOT EXISTS simplystock;
USE simplystock;

-- Table for user login and account info
CREATE TABLE IF NOT EXISTS login (
    username   VARCHAR(40) PRIMARY KEY,
    password   VARCHAR(40) NOT NULL,
    firstname  VARCHAR(40),
    lastname   VARCHAR(40),
    phone      VARCHAR(20),
    aadhar     VARCHAR(13),
    balance    INT DEFAULT 0
);

-- Table for user stock holdings
CREATE TABLE IF NOT EXISTS stocks (
    username   VARCHAR(45),
    sname      VARCHAR(80),     -- Stock name
    shares     INT,
    money      FLOAT,           -- Total invested money
    ticker     VARCHAR(20),     -- Stock symbol
    PRIMARY KEY (username, sname),
    FOREIGN KEY (username) REFERENCES login(username) ON DELETE CASCADE
);
