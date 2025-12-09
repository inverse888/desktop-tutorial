import os
import sys
import zipfile
import shutil
from pathlib import Path
import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox
from sqlalchemy import func
from PIL import Image

from db_management import session, CategoriesTable
from addition_classes import recolor_icon, resource_path
from category_creation import CategoryCreationPage, get_icon_names

class IconsManagementFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="#aba6a6")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        
        # Заголовок
        self.title_label = ctk.CTkLabel(self, text="Управление иконками", 
                                       font=("Arial", 24, "bold"), text_color="black")
        self.title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        # Информация о текущих иконках
        self.icons_info_label = ctk.CTkLabel(self, text="", 
                                           font=("Arial", 12), text_color="black")
        self.icons_info_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))
        
        # Кнопка замены иконок
        self.replace_icons_button = ctk.CTkButton(self, text="Заменить иконки", 
                                                font=("Arial", 16), text_color="black",
                                                command=self.replace_icons,
                                                height=40)
        self.replace_icons_button.grid(row=0, column=0, sticky="e", padx=20, pady=(20, 10))
        
        # Фрейм для отображения текущих иконок
        self.icons_preview_frame = ctk.CTkScrollableFrame(self, fg_color="#949191")
        self.icons_preview_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.icons_preview_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)  # Увеличили количество колонок
        
        self.update_icons_info()
        self.update_icons_preview()

    def update_icons_info(self):
        """Обновляет информацию о текущих иконках"""
        icons_path = resource_path("assets/icons/categories")
        if os.path.exists(icons_path):
            icons = [f for f in os.listdir(icons_path) if f.endswith('.png')]
            self.icons_info_label.configure(
                text=f"Текущее количество иконок: {len(icons)}"
            )
        else:
            self.icons_info_label.configure(text="Папка с иконками не найдена")

    def update_icons_preview(self):
        """Обновляет превью иконок"""
        # Очищаем текущий превью
        for widget in self.icons_preview_frame.winfo_children():
            widget.destroy()
        
        icons_path = resource_path("assets/icons/categories")
        if not os.path.exists(icons_path):
            no_icons_label = ctk.CTkLabel(self.icons_preview_frame, 
                                        text="Папка с иконками не найдена", 
                                        font=("Arial", 16), text_color="black")
            no_icons_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
            return
        
        icons = [f for f in os.listdir(icons_path) if f.endswith('.png')]
        icons.sort()
        
        if not icons:
            no_icons_label = ctk.CTkLabel(self.icons_preview_frame, 
                                        text="Нет иконок для отображения", 
                                        font=("Arial", 16), text_color="black")
            no_icons_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
            return
        
        # Отображаем ВСЕ иконки с полными названиями
        columns = 6  # Немного уменьшим количество колонок для более широких ячеек
        for i, icon_file in enumerate(icons):
            row = i // columns
            col = i % columns
            
            icon_path = os.path.join(icons_path, icon_file)
            try:
                # Создаем контейнер для иконки и названия
                icon_container = ctk.CTkFrame(self.icons_preview_frame, fg_color="transparent", height=80)
                icon_container.grid(row=row*2, column=col, padx=5, pady=5, sticky="nsew")
                icon_container.grid_propagate(False)
                icon_container.grid_columnconfigure(0, weight=1)
                
                # Загружаем иконку
                icon_image = ctk.CTkImage(
                    light_image=Image.open(icon_path),
                    size=(40, 40)
                )
                
                # Иконка
                icon_label = ctk.CTkLabel(icon_container, image=icon_image, text="")
                icon_label.grid(row=0, column=0, pady=(5, 2))
                
                # Полное название иконки с переносом слов
                icon_name = icon_file.replace('.png', '')
                name_label = ctk.CTkLabel(icon_container, text=icon_name,
                                        font=("Arial", 9), text_color="black",
                                        wraplength=80,  # Ширина для переноса
                                        justify="center")  # Выравнивание по центру
                name_label.grid(row=1, column=0, pady=(0, 5), sticky="ew")
                
            except Exception as e:
                print(f"Ошибка загрузки иконки {icon_file}: {e}")
                continue
        
        # Обновляем информацию о количестве
        self.update_icons_info()

    def replace_icons(self):
        """Замена иконок из zip архива"""
        # Диалог выбора файла
        zip_path = ctk.filedialog.askopenfilename(
            title="Выберите zip архив с новыми иконками",
            filetypes=[("ZIP files", "*.zip")]
        )
        
        if not zip_path:
            return
        
        try:
            self._process_zip_replacement(zip_path)
        except Exception as e:
            # Создаем собственное окно ошибки для длинных сообщений
            self._show_error_dialog("Ошибка при замене иконок", str(e))

    def _show_error_dialog(self, title, message):
        """Показывает диалог ошибки с возможностью прокрутки для длинных сообщений"""
        error_window = ctk.CTkToplevel(self)
        error_window.title(title)
        error_window.geometry("500x300")
        error_window.resizable(True, True)
        error_window.transient(self)
        error_window.grab_set()
        
        error_window.grid_columnconfigure(0, weight=1)
        error_window.grid_rowconfigure(0, weight=1)
        error_window.grid_rowconfigure(1, weight=0)
        
        # Текст ошибки с прокруткой
        text_frame = ctk.CTkFrame(error_window)
        text_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        error_text = ctk.CTkTextbox(text_frame, wrap="word", font=("Arial", 12))
        error_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        error_text.insert("1.0", message)
        error_text.configure(state="disabled")
        
        # Кнопка OK
        ok_button = ctk.CTkButton(error_window, text="OK", command=error_window.destroy)
        ok_button.grid(row=1, column=0, pady=10)

    def _process_zip_replacement(self, zip_path):
        """Обрабатывает замену иконок из zip архива"""
        icons_dir = resource_path("assets/icons/categories")
        
        # Создаем временную директорию для проверки новых иконок
        temp_dir = resource_path("assets/icons/categories_temp")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        try:
            # Распаковываем архив во временную директорию
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Проверяем новые иконки
            new_icons = self._validate_new_icons(temp_dir, icons_dir)
            
            # Создаем backup текущих иконок
            self._create_backup(icons_dir)
            
            # Заменяем иконки
            self._replace_icons_files(icons_dir, temp_dir, new_icons)
            
            CTkMessagebox.messagebox(title="Успех!", text="Иконки успешно заменены!")
            
            # Обновляем информацию и превью
            self.update_icons_info()
            self.update_icons_preview()
            
        finally:
            # Очищаем временную директорию
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _validate_new_icons(self, temp_dir, icons_dir):
        """Проверяет новые иконки на соответствие требованиям"""
        # Получаем список текущих иконок
        current_icons = set()
        if os.path.exists(icons_dir):
            for file in os.listdir(icons_dir):
                if file.endswith('.png') and file != 'previous_icons_backup.zip':
                    current_icons.add(file)
        
        # Получаем список новых иконок
        new_icons = set()
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.png'):
                    new_icons.add(file)
        
        if not current_icons:
            raise ValueError("Не найдены текущие иконки для сравнения")
        
        if not new_icons:
            raise ValueError("В архиве не найдены PNG иконки")
        
        # Проверяем количество
        if len(new_icons) != len(current_icons):
            raise ValueError(
                f"Количество иконок не совпадает!\n"
                f"Текущие: {len(current_icons)}\n"
                f"Новые: {len(new_icons)}"
            )
        
        # Проверяем имена
        if new_icons != current_icons:
            missing_icons = current_icons - new_icons
            extra_icons = new_icons - current_icons
            
            error_msg = "Имена иконок не совпадают!\n\n"
            if missing_icons:
                error_msg += f"Отсутствующие иконки ({len(missing_icons)}):\n"
                error_msg += "\n".join([f"• {icon}" for icon in sorted(missing_icons)]) + "\n\n"
            if extra_icons:
                error_msg += f"Лишние иконки ({len(extra_icons)}):\n"
                error_msg += "\n".join([f"• {icon}" for icon in sorted(extra_icons)])
            
            raise ValueError(error_msg)
        
        return new_icons

    def _create_backup(self, icons_dir):
        """Создает backup текущих иконок в zip архив"""
        backup_path = resource_path("assets/icons/categories/previous_icons_backup.zip")
        
        # Удаляем старый backup если существует
        if os.path.exists(backup_path):
            os.remove(backup_path)
        
        # Создаем новый backup
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(icons_dir):
                for file in files:
                    if file.endswith('.png') and file != 'previous_icons_backup.zip':
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, icons_dir)
                        zipf.write(file_path, arcname)

    def _replace_icons_files(self, icons_dir, temp_dir, new_icons):
        """Заменяет файлы иконок"""
        # Удаляем текущие иконки
        for file in os.listdir(icons_dir):
            if file.endswith('.png') and file != 'previous_icons_backup.zip':
                os.remove(os.path.join(icons_dir, file))
        
        # Копируем новые иконки
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.png'):
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(icons_dir, file)
                    shutil.copy2(src_path, dst_path)

class CategoriesManagementFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="#aba6a6")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        # Заголовок
        self.title_label = ctk.CTkLabel(self, text="Категории", 
                                       font=("Arial", 24, "bold"), text_color="black")
        self.title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        # Кнопка добавления категории
        self.add_category_button = ctk.CTkButton(self, text="Добавить новую категорию", 
                                               font=("Arial", 18), text_color="black",
                                               command=self._create_category,
                                               height=50)
        self.add_category_button.grid(row=0, column=0, sticky="e", padx=20, pady=(20, 10))
        
        # Фрейм для отображения существующих категорий
        self.categories_frame = ctk.CTkScrollableFrame(self, fg_color="#949191")
        self.categories_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.categories_frame.grid_columnconfigure(0, weight=1)
        
        self.new_category = None
        self.update_categories_list()

    def _create_category(self):
        if not self.new_category or not self.new_category.winfo_exists():
            self.new_category = CategoryCreationPage(self.master)
        
        self.new_category.attributes('-topmost', True)
        self.new_category.deiconify()
        self.new_category.update()
        self.new_category.focus()
        
        # Привязываем событие закрытия окна создания категории к обновлению списка
        self.new_category.protocol("WM_DELETE_WINDOW", self.on_category_window_close)

    def on_category_window_close(self):
        if self.new_category:
            self.new_category.destroy()
        self.update_categories_list()

    def update_categories_list(self):
        # Очищаем текущий список
        for widget in self.categories_frame.winfo_children():
            widget.destroy()
        
        # Получаем все категории из базы данных
        categories = session.query(CategoriesTable).order_by(CategoriesTable.transaction_type, 
                                                           CategoriesTable.category_name).all()
        
        if not categories:
            no_categories_label = ctk.CTkLabel(self.categories_frame, 
                                             text="Категории не найдены", 
                                             font=("Arial", 16), text_color="black")
            no_categories_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
            return
        
        # Группируем категории по типам
        expense_categories = [cat for cat in categories if cat.transaction_type == "Расход"]
        income_categories = [cat for cat in categories if cat.transaction_type == "Доход"]
        
        row = 0
        
        # Отображаем категории расходов
        if expense_categories:
            expense_label = ctk.CTkLabel(self.categories_frame, text="Категории расходов:",
                                       font=("Arial", 20, "bold"), text_color="black")
            expense_label.grid(row=row, column=0, sticky="w", padx=20, pady=(10, 5))
            row += 1
            
            for i, category in enumerate(expense_categories):
                self._create_category_row(category, row + i)
            row += len(expense_categories)
        
        # Отображаем категории доходов
        if income_categories:
            income_label = ctk.CTkLabel(self.categories_frame, text="Категории доходов:",
                                      font=("Arial", 20, "bold"), text_color="black")
            income_label.grid(row=row, column=0, sticky="w", padx=20, pady=(10, 5))
            row += 1
            
            for i, category in enumerate(income_categories):
                self._create_category_row(category, row + i)

    def _create_category_row(self, category, row):
        category_frame = ctk.CTkFrame(self.categories_frame, fg_color="#aba6a6")
        category_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        category_frame.grid_columnconfigure(0, weight=0)
        category_frame.grid_columnconfigure(1, weight=1)
        category_frame.grid_columnconfigure(2, weight=0)
        
        # Иконка категории
        icon_image = ctk.CTkImage(
            light_image=recolor_icon(resource_path(f"assets/{category.icon_url}"), category.colour),
            size=(40, 40)
        )
        icon_label = ctk.CTkLabel(category_frame, image=icon_image, text="")
        icon_label.grid(row=0, column=0, padx=(10, 5), pady=5)
        
        # Название категории
        name_label = ctk.CTkLabel(category_frame, text=category.category_name, 
                                font=("Arial", 16), text_color="black")
        name_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Тип категории и цвет
        type_label = ctk.CTkLabel(category_frame, 
                                text=f"Тип: {category.transaction_type} | Цвет: {category.colour}",
                                font=("Arial", 12), text_color="black")
        type_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Создаем вкладки
        self.tabview = ctk.CTkTabview(self, fg_color="#aba6a6")
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Добавляем вкладки
        self.tabview.add("Категории")
        self.tabview.add("Иконки")
        
        # Настройка вкладки категорий
        self.tabview.tab("Категории").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Категории").grid_rowconfigure(0, weight=1)
        
        self.categories_management = CategoriesManagementFrame(self.tabview.tab("Категории"))
        self.categories_management.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Настройка вкладки иконок
        self.tabview.tab("Иконки").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Иконки").grid_rowconfigure(0, weight=1)
        
        self.icons_management = IconsManagementFrame(self.tabview.tab("Иконки"))
        self.icons_management.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def update_categories(self):
        """Метод для обновления списка категорий"""
        self.categories_management.update_categories_list()