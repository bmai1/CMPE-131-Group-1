CREATE TABLE users (
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(50) NOT NULL,
    address1 VARCHAR(50) NOT NULL,
    dob DATE NOT NULL,
    password BLOB NOT NULL
);