# *"Система учёта финансов"*
**Приложение разрабатывается на БК 536 *Вега* на учебной практике**

# Описание
Приложение предоставляет следующие функции учёта финансов:
- добавление расходов и доходов;
- добавление категорий, выбор цветов и иконок, загрузка своих иконок;
- добавление переводов между счетами;
- фильтрация по категории;
- отображение статистики трат за день, неделю, месяц или другой выбранный период дат;
- выбор дат трат и отображение расходов и доходов за выбранный промежуток времени.
- добавление и сохранение чеков
- 

# Сборка
Для запуска приложения следует:
- Клонировать репозиторий
```bash
git clone https://github.com/inverse888/desktop-tutorial
```

- Установить зависимости
```bash
pip install -r requirements.txt
```

- Создать базу данных postgresSql, таблицы и заполнить их
```
открыть редактор запросов pgAdmin Tool и выполнить запросы из файла DB/practice_db_upd.sql
```
- Подключение к собственной БД
```
Создаете в папке проекта файл database.ini 
копируете:
[postgresql]
host = localhost
port = 5432
database = finances_accounting
user = postgres
password = 3648
и меняете Хост: "свой Хост" и Password: "свой Пароль"
```

- собрать исполняемый файл
```bash
pyinstaller main.py --onefile --noconsole --icon=assets/icons/asset-management.ico --add-data "assets/icons/asset-management.ico;assets/icons" --add-data "assets/icons/categories;assets/icons/categories" --add-data "assets/icons/sidebar;assets/icons/sidebar" --add-data "assets/icons;assets/icons" --clean
```
- 
Запустить файл main.exe в папке Finance_application\dist

# Авторы
***Корчагин А.И.*** — *korchalex82@gmail.com*
