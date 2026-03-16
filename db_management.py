import os
import configparser
from pathlib import Path
from sqlalchemy import (create_engine, Text, Column, Integer, Numeric,
                        String, DateTime, ForeignKey, LargeBinary)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime

# Функция для получения строки подключения из .ini файла
def get_connection_string():
    """
    Читает параметры подключения из database.ini файла
    и возвращает строку подключения для SQLAlchemy
    """
    # Пути, где может находиться файл конфигурации
    config_paths = [
        Path('database.ini'),  # В текущей директории
        Path(__file__).parent / 'database.ini',  # Рядом с текущим файлом
        Path.home() / '.finances' / 'database.ini',  # В домашней директории пользователя
    ]
    
    # Ищем файл конфигурации
    config_file = None
    for path in config_paths:
        if path.exists():
            config_file = path
            break
    
    # Если файл не найден, создаем его с параметрами по умолчанию
    if not config_file:
        print("⚠ Файл database.ini не найден. Создаю с параметрами по умолчанию...")
        
        # Создаем директорию для конфига в домашней папке
        home_config_dir = Path.home() / '.finances'
        home_config_dir.mkdir(exist_ok=True)
        config_file = home_config_dir / 'database.ini'
        
        # Создаем конфигурационный файл
        config = configparser.ConfigParser()
        config['postgresql'] = {
            'host': 'localhost',
            'port': '5432',
            'database': 'finances_accounting',
            'user': 'postgres',
            'password': '3648'
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        
        print(f"✅ Файл конфигурации создан: {config_file}")
        print("ℹ Отредактируйте его при необходимости")
    
    # Читаем конфигурацию
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')
    
    # Проверяем наличие секции [postgresql]
    if 'postgresql' not in config:
        raise KeyError(f"Секция [postgresql] не найдена в файле {config_file}")
    
    # Получаем параметры с значениями по умолчанию
    db_config = {
        'host': config.get('postgresql', 'host', fallback='localhost'),
        'port': config.get('postgresql', 'port', fallback='5432'),
        'database': config.get('postgresql', 'database', fallback='finances_accounting'),
        'user': config.get('postgresql', 'user', fallback='postgres'),
        'password': config.get('postgresql', 'password', fallback='3648'),
    }
    
    # Формируем строку подключения
    connection_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    print(f"📊 Используется подключение: postgresql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    return connection_string

# Создаем подключение к базе данных
try:
    engine = create_engine(get_connection_string())
    print("✅ Подключение к базе данных установлено")
except Exception as e:
    print(f"❌ Ошибка подключения к базе данных: {e}")
    print("⚠ Использую параметры подключения по умолчанию...")
    # Параметры по умолчанию для совместимости
    engine = create_engine('postgresql+psycopg2://postgres:3648@localhost:5432/finances_accounting')

Session = sessionmaker(autoflush=False, bind=engine)
session = Session()

Base = declarative_base()

class AccountsTable(Base):
    __tablename__ = 'accounts'

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False, default=0.0)
    icon_url = Column(Text)
    description = Column(Text)

    transactions = relationship("TransactionsTable", back_populates="account", cascade="all, delete")
    transfers_from = relationship("TransfersTable", back_populates="from_account_ref",
                                  foreign_keys='TransfersTable.from_account')
    transfers_to = relationship("TransfersTable", back_populates="to_account_ref",
                                foreign_keys='TransfersTable.to_account')


class CategoriesTable(Base):
    __tablename__ = 'categories'

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(50), nullable=False, unique=True)
    transaction_type = Column(String(50), nullable=False)
    colour = Column(String(7), nullable=False, default="#144870")
    icon_url = Column(Text)

    transactions = relationship("TransactionsTable", back_populates="category")


class TransactionsTable(Base):
    __tablename__ = 'transactions'

    transaction_id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id", ondelete="SET NULL"))
    transaction_type = Column(String(50), nullable=False)
    transaction_date_time = Column(DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))
    amount = Column(Numeric(10, 2), nullable=False, default=0.0)
    check_photo = Column(LargeBinary)
    description = Column(Text)

    account = relationship("AccountsTable", back_populates="transactions")
    category = relationship("CategoriesTable", back_populates="transactions")


class TransfersTable(Base):
    __tablename__ = 'transfers'

    transfer_id = Column(Integer, primary_key=True)
    from_account = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    to_account = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    transfer_date_time = Column(DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))
    amount = Column(Numeric(10, 2), nullable=False, default=0.0)
    description = Column(Text)

    from_account_ref = relationship("AccountsTable", foreign_keys=[from_account],
                                    back_populates="transfers_from")
    to_account_ref = relationship("AccountsTable", foreign_keys=[to_account],
                                  back_populates="transfers_to")