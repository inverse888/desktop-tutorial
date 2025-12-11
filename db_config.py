# Конфигурация подключения к базе данных PostgreSQL
DB_CONFIG = {
    'username': 'postgres',          # Имя пользователя PostgreSQL
    'password': '3648',        # Пароль пользователя
    'host': 'localhost',             # Адрес сервера
    'port': '5432',                  # Порт PostgreSQL (по умолчанию 5432)
    'database': 'finances_accounting'       # Название базы данных
}

# Формирование строки подключения для SQLAlchemy
def get_connection_string():
    return f"postgresql+psycopg2://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"