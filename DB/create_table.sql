-- Удаление существующих таблиц (если они есть)
DROP TABLE IF EXISTS Transfers;
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Categories;
DROP TABLE IF EXISTS Accounts;

-- Удаление существующих типов (если они есть)
DROP TYPE IF EXISTS account_type;
DROP TYPE IF EXISTS transaction_type;

-- Создание типов данных
CREATE TYPE account_type AS ENUM ('Обычный', 'Кредитный', 'Накопительный');
CREATE TYPE transaction_type AS ENUM ('Доход', 'Расход');

-- Создание таблицы Accounts (Счета)
CREATE TABLE Accounts (
    account_id SERIAL PRIMARY KEY,
    type account_type NOT NULL,
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    icon_url TEXT,
    description TEXT
);

-- Создание таблицы Categories (Категории)
CREATE TABLE Categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    colour VARCHAR(7) NOT NULL DEFAULT '#144870',
    transaction_type transaction_type NOT NULL,
    icon_url TEXT
);

-- Создание таблицы Transactions (Транзакции)
CREATE TABLE Transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES Accounts(account_id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES Categories(category_id) ON DELETE SET NULL,
    transaction_type transaction_type NOT NULL,
    transaction_date_time TIMESTAMP NOT NULL DEFAULT NOW(),
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    description TEXT,
    check_photo BYTEA
);

-- Создание таблицы Transfers (Переводы)
CREATE TABLE Transfers (
    transfer_id SERIAL PRIMARY KEY,
    from_account INTEGER NOT NULL REFERENCES Accounts(account_id) ON DELETE CASCADE,
    to_account INTEGER NOT NULL REFERENCES Accounts(account_id) ON DELETE CASCADE,
    transfer_date_time TIMESTAMP NOT NULL DEFAULT NOW(),
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    description TEXT
);

-- Создание индексов для улучшения производительности
CREATE INDEX idx_transactions_date ON Transactions(transaction_date_time);
CREATE INDEX idx_transactions_account ON Transactions(account_id);
CREATE INDEX idx_transactions_category ON Transactions(category_id);
CREATE INDEX idx_transfers_date ON Transfers(transfer_date_time);
CREATE INDEX idx_transfers_from_account ON Transfers(from_account);
CREATE INDEX idx_transfers_to_account ON Transfers(to_account);