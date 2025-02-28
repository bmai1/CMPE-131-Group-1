CREATE TYPE account {
    account_type varchar(255) NOT NULL,
    balance INT(255) NOT NULL,
}

CREATE TABLE users {
    username varchar(255) NOT NULL UNIQUE,
    password varchar(255) NOT NULL,
};