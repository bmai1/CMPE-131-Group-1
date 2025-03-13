CREATE TABLE users (
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(50) NOT NULL,
    address1 VARCHAR(50) NOT NULL,
    address2 VARCHAR(50) ,
    city VARCHAR(50) NOT NULL,
    "state" VARCHAR(50) NOT NULL,
    zip VARCHAR(50) NOT NULL,
    dob DATE NOT NULL,
    phone VARCHAR(50) NOT NULL,
    password BLOB NOT NULL
);