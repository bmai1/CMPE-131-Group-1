CREATE TABLE users (
    username TEXT NOT NULL UNIQUE,
    password BLOB NOT NULL
);