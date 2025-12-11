--чтобы пересоздать базу нужны
--drop table Transfers;
--drop table Transactions;
--drop table Categories;
--drop table Accounts;


CREATE TYPE account_type AS ENUM ('Обычный', 'Кредитный', 'Накопительный');

CREATE TYPE transaction_type AS ENUM ('Доход', 'Расход');


CREATE TABLE Accounts (
    account_id SERIAL PRIMARY KEY,
    type account_type NOT NULL,
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
	icon_url TEXT,
    description TEXT
);

CREATE TABLE Categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    colour VARCHAR(7) NOT NULL DEFAULT 'Синий',
	transaction_type  transaction_type NOT NULL,
    icon_url TEXT
);

CREATE TABLE Transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES Accounts(account_id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES Categories(category_id) ON DELETE SET NULL,
    transaction_type  transaction_type NOT NULL,
    transaction_date_time TIMESTAMP NOT NULL DEFAULT NOW(),
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
	description TEXT,
    check_photo BYTEA
);

CREATE TABLE Transfers (
    transfer_id SERIAL PRIMARY KEY,
    from_account INTEGER NOT NULL REFERENCES Accounts(account_id) ON DELETE CASCADE,
    to_account INTEGER NOT NULL REFERENCES Accounts(account_id) ON DELETE CASCADE,
    transfer_date_time TIMESTAMP NOT NULL DEFAULT NOW(),
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    description TEXT
);


--удаление всех данных, и сброс счетчика 
--TRUNCATE TABLE Transfers, Transactions, Categories, Accounts RESTART IDENTITY CASCADE;

--delete  from Accounts;
--delete from Categories;
--delete from Transactions;
--delete from Transfers;

-- 1. Сначала вставляем Accounts
INSERT INTO Accounts (type, amount, icon_url, description) VALUES
('Обычный', 15000.50, 'icons/categories/bill.png', 'Обычный'),
('Кредитный', 15000.50, 'icons/sidebar/credit-card.png', 'Кредитка'),
('Накопительный', 75000.00, 'icons/categories/piggybank.png', 'Накопительный счет на отпуск');

-- 2. Проверяем какие ID получились
SELECT account_id, type FROM Accounts;

-- 3. Затем вставляем Categories
INSERT INTO Categories (category_name, colour, transaction_type, icon_url) VALUES
-- Доходы (зеленые оттенки)
('Зарплата', '#2E7D32', 'Доход', 'icons/categories/document.png'),
('Фриланс', '#388E3C', 'Доход', 'icons/categories/document.png'),
('Инвестиции', '#1B5E20', 'Доход', 'icons/categories/bank.png'),
('Дивиденды', '#43A047', 'Доход', 'icons/categories/bank.png'),

-- Расходы (разные оттенки для лучшего визуального разделения)
('Продукты', '#D32F2F', 'Расход', 'icons/categories/goods.png'),
('Транспорт', '#1976D2', 'Расход', 'icons/categories/car.png'),
('Общественный транспорт', '#0288D1', 'Расход', 'icons/categories/train.png'),
('Связь', '#7B1FA2', 'Расход', 'icons/categories/telephone.png'),
('Развлечения', '#C2185B', 'Расход', 'icons/categories/media.png'),
('Парковка', '#5D4037', 'Расход', 'icons/categories/parking.png'),
('Автомобиль', '#455A64', 'Расход', 'icons/categories/car.png'),
('Домашние животные', '#F57C00', 'Расход', 'icons/categories/cat.png'),
('Банковские услуги', '#303F9F', 'Расход', 'icons/categories/bank.png'),
('Одежда', '#512DA8', 'Расход', 'icons/categories/goods.png');

-- 4. Вставляем Transactions (замените 1,2,3 на реальные ID из шага 2)
INSERT INTO Transactions (account_id, category_id, transaction_type, transaction_date_time, amount, description) VALUES
(1, 1, 'Доход', '2025-11-01 10:00:00', 50000.00, 'Зарплата за январь'),
(1, 2, 'Доход', '2025-11-02 14:30:00', 15000.00, 'Фриланс проект'),
(1, 3, 'Доход', '2025-11-01 09:15:00', 2500.50, 'Инвестиционный доход'),
(1, 5, 'Расход', '2025-11-03 18:45:00', 3500.75, 'Продукты на неделю'),
(1, 6, 'Расход', '2025-11-10 08:20:00', 500.00, 'Бензин'),
(1, 7, 'Расход', '2025-11-11 09:00:00', 150.00, 'Метро до работы'),
(1, 8, 'Расход', '2025-11-12 12:00:00', 450.00, 'Мобильная связь'),
(1, 9, 'Расход', '2025-11-15 20:00:00', 1200.00, 'Кино и ужин'),
(1, 10, 'Расход', '2025-11-06 14:30:00', 300.00, 'Парковка в центре'),
(2, 13, 'Расход', '2025-11-08 13:15:00', 150.00, 'Обслуживание счета'),
(1, 14, 'Расход', '2025-11-07 15:45:00', 3000.00, 'Новая одежда'),
(1, 5, 'Расход', '2025-11-15 17:30:00', 2800.25, 'Продукты');

-- 5. Вставляем Transfers
INSERT INTO Transfers (from_account, to_account, transfer_date_time, amount, description) VALUES
(1, 2, '2025-11-11 11:00:00', 10000.00, 'Пополнение накопительного счета'),
(2, 1, '2025-11-10 10:30:00', 2000.00, 'Снятие с накопительного счета');

