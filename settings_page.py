import os
import sys
import shutil
from pathlib import Path
import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox
from sqlalchemy import func
from PIL import Image, ImageDraw
import tkinter.messagebox as tkmsg

from db_management import session, CategoriesTable, TransactionsTable
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
        
        # Кнопка добавления иконок
        self.add_icons_button = ctk.CTkButton(self, text="Добавить иконки", 
                                             font=("Arial", 16), text_color="black",
                                             command=self.add_icons_from_files,
                                             height=40)
        self.add_icons_button.grid(row=0, column=0, sticky="e", padx=20, pady=(20, 10))
        
        # Фрейм для отображения текущих иконок
        self.icons_preview_frame = ctk.CTkScrollableFrame(self, fg_color="#949191")
        self.icons_preview_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.icons_preview_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        
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
        
        # Отображаем все иконки с полными названиями
        columns = 6
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
                                        wraplength=80,
                                        justify="center")
                name_label.grid(row=1, column=0, pady=(0, 5), sticky="ew")
                
            except Exception as e:
                print(f"Ошибка загрузки иконки {icon_file}: {e}")
                continue
        
        # Обновляем информацию о количестве
        self.update_icons_info()
        
        # Вызываем обновление списка иконок в CategoryCreationPage
        self._update_category_creation_icons()

    def _update_category_creation_icons(self):
        """Обновляет список доступных иконок в CategoryCreationPage"""
        # Ищем родительский SettingsPage
        current = self.master
        while current:
            if hasattr(current, 'update_icons_in_category_creation'):
                current.update_icons_in_category_creation()
                break
            current = current.master

    def add_icons_from_files(self):
        """Добавление иконок из выбранных файлов"""
        # Диалог выбора нескольких файлов
        file_paths = ctk.filedialog.askopenfilenames(
            title="Выберите файлы иконок (PNG)",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not file_paths:
            return
        
        try:
            self._process_files_addition(file_paths)
        except Exception as e:
            self._show_error_dialog("Ошибка при добавлении иконок", str(e))

    def _show_error_dialog(self, title, message):
        """Показывает увеличенный диалог ошибки с возможностью прокрутки для длинных сообщений"""
        error_window = ctk.CTkToplevel(self)
        error_window.title(title)
        error_window.geometry("600x400")  # Увеличенный размер
        error_window.resizable(True, True)
        error_window.transient(self)
        error_window.grab_set()
        
        error_window.grid_columnconfigure(0, weight=1)
        error_window.grid_rowconfigure(0, weight=1)
        error_window.grid_rowconfigure(1, weight=0)
        
        text_frame = ctk.CTkFrame(error_window)
        text_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        error_text = ctk.CTkTextbox(text_frame, wrap="word", font=("Arial", 14), height=250)
        error_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        error_text.insert("1.0", message)
        error_text.configure(state="disabled")
        
        ok_button = ctk.CTkButton(error_window, text="OK", 
                                 command=error_window.destroy,
                                 font=("Arial", 14, "bold"),
                                 height=40, width=120)
        ok_button.grid(row=1, column=0, pady=20)
        
        # Центрируем окно
        error_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - error_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - error_window.winfo_height()) // 2
        error_window.geometry(f"+{x}+{y}")

    def _process_files_addition(self, file_paths):
        """Обрабатывает добавление иконок из выбранных файлов"""
        icons_dir = resource_path("assets/icons/categories")
        
        # Создаем папку для иконок, если её нет
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir)
        
        # Фильтруем только PNG файлы
        png_files = [f for f in file_paths if f.lower().endswith('.png')]
        
        if not png_files:
            raise ValueError("Не выбрано ни одного PNG файла")
        
        # Счетчики для отчета
        added_count = 0
        replaced_count = 0
        skipped_count = 0
        added_icons = []
        replaced_icons = []
        skipped_icons = []
        
        # Обрабатываем каждый файл
        for file_path in png_files:
            file_name = os.path.basename(file_path)
            dst_path = os.path.join(icons_dir, file_name)
            
            # Проверяем, существует ли уже такая иконка
            if os.path.exists(dst_path):
                # Проверяем, действительно ли файлы разные (по размеру)
                src_size = os.path.getsize(file_path)
                dst_size = os.path.getsize(dst_path)
                
                if src_size != dst_size:
                    # Если размер отличается, заменяем
                    shutil.copy2(file_path, dst_path)
                    replaced_count += 1
                    replaced_icons.append(file_name)
                else:
                    # Если размер одинаковый, пропускаем
                    skipped_count += 1
                    skipped_icons.append(file_name)
            else:
                # Добавляем новую иконку
                shutil.copy2(file_path, dst_path)
                added_count += 1
                added_icons.append(file_name)
        
        # Формируем сообщение о результате
        result_message = []
        if added_count > 0:
            result_message.append(f"✅ Добавлено новых иконок: {added_count}")
            if added_count <= 10:
                result_message.append("Новые иконки:")
                result_message.extend([f"  • {icon}" for icon in added_icons])
            else:
                result_message.append(f"  (всего {added_count} иконок)")
        
        if replaced_count > 0:
            result_message.append(f"🔄 Заменено существующих иконок: {replaced_count}")
            if replaced_count <= 10:
                result_message.append("Замененные иконки:")
                result_message.extend([f"  • {icon}" for icon in replaced_icons])
            else:
                result_message.append(f"  (всего {replaced_count} иконок)")
        
        if skipped_count > 0:
            result_message.append(f"⏭️ Пропущено (уже есть такие же): {skipped_count}")
            if skipped_count <= 10:
                result_message.append("Пропущенные иконки:")
                result_message.extend([f"  • {icon}" for icon in skipped_icons])
        
        if not result_message:
            result_message = ["Не было добавлено или заменено ни одной иконки"]
        
        # Добавляем общую статистику
        result_message.insert(0, f"📊 Всего обработано файлов: {len(png_files)}")
        
        # Обновляем информацию и превью
        self.update_icons_info()
        self.update_icons_preview()
        
        # НЕМЕДЛЕННО обновляем список иконок в окне создания категории
        self._update_category_creation_icons()
        
        # Показываем увеличенное сообщение об успехе
        self._show_success_dialog("Результат добавления иконок", "\n".join(result_message))
    
    def _show_success_dialog(self, title, message):
        """Показывает увеличенный диалог успеха"""
        success_window = ctk.CTkToplevel(self)
        success_window.title(title)
        success_window.geometry("600x500")  # Увеличенный размер
        success_window.resizable(True, True)
        success_window.transient(self)
        success_window.grab_set()
        
        success_window.grid_columnconfigure(0, weight=1)
        success_window.grid_rowconfigure(0, weight=1)
        success_window.grid_rowconfigure(1, weight=0)
        
        text_frame = ctk.CTkFrame(success_window)
        text_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        success_text = ctk.CTkTextbox(text_frame, wrap="word", font=("Arial", 14), height=350)
        success_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        success_text.insert("1.0", message)
        success_text.configure(state="disabled")
        
        ok_button = ctk.CTkButton(success_window, text="OK", 
                                 command=success_window.destroy,
                                 font=("Arial", 14, "bold"),
                                 height=40, width=120)
        ok_button.grid(row=1, column=0, pady=20)
        
        # Центрируем окно
        success_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - success_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - success_window.winfo_height()) // 2
        success_window.geometry(f"+{x}+{y}")

def create_color_square(color_hex, size=(30, 30)):
    """
    Создает изображение цветного квадратика заданного цвета
    """
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), size], fill=color_hex, outline="black", width=1)
    return img

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
            # Устанавливаем callback для обновления списка категорий
            self.new_category.save_callback = self.on_category_saved
            # Привязываем событие закрытия окна к обновлению списка категорий
            self.new_category.protocol("WM_DELETE_WINDOW", self.on_category_window_close)
        
        self.new_category.attributes('-topmost', True)
        self.new_category.deiconify()
        self.new_category.update()
        self.new_category.focus()

    def on_category_saved(self):
        """Вызывается при успешном сохранении категории"""
        print("Категория сохранена, обновляем список")
        self.update_categories_list()
        # Также обновляем категории в главном приложении
        if hasattr(self.master, 'update_categories'):
            self.master.update_categories()

    def on_category_window_close(self):
        if self.new_category:
            self.new_category.destroy()
            self.new_category = None
        # Обновляем список на всякий случай
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
        category_frame.grid_columnconfigure(0, weight=0)  # Иконка
        category_frame.grid_columnconfigure(1, weight=1)  # Название
        category_frame.grid_columnconfigure(2, weight=0)  # Тип
        category_frame.grid_columnconfigure(3, weight=0)  # Цветной квадратик
        category_frame.grid_columnconfigure(4, weight=0)  # Кнопка редактирования
        category_frame.grid_columnconfigure(5, weight=0)  # Кнопка удаления
        
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
        
        # Тип категории
        type_label = ctk.CTkLabel(category_frame, 
                                text=f"Тип: {category.transaction_type}",
                                font=("Arial", 12), text_color="black")
        type_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        
        # Цветной квадратик
        try:
            color_square_image = ctk.CTkImage(
                light_image=create_color_square(category.colour, size=(30, 30)),
                size=(30, 30)
            )
            color_label = ctk.CTkLabel(category_frame, image=color_square_image, text="")
            color_label.grid(row=0, column=3, padx=(5, 10), pady=5)
        except Exception as e:
            print(f"Ошибка создания цветного квадратика для категории {category.category_name}: {e}")
            fallback_label = ctk.CTkLabel(category_frame, text=category.colour,
                                        font=("Arial", 10), text_color="black")
            fallback_label.grid(row=0, column=3, padx=(5, 10), pady=5)
        
        # Кнопка редактирования
        try:
            edit_icon = ctk.CTkImage(
                light_image=Image.open(resource_path("assets/icons/edit.png")),
                size=(20, 20)
            )
            edit_button = ctk.CTkButton(
                category_frame,
                image=edit_icon,
                text="",
                width=30,
                height=30,
                fg_color="transparent",
                hover_color="#8a8585",
                command=lambda c=category: self._edit_category(c)
            )
        except:
            edit_button = ctk.CTkButton(
                category_frame,
                text="✏️",
                width=30,
                height=30,
                fg_color="transparent",
                hover_color="#8a8585",
                command=lambda c=category: self._edit_category(c)
            )
        edit_button.grid(row=0, column=4, padx=2, pady=5)
        
        # Кнопка удаления
        try:
            delete_icon = ctk.CTkImage(
                light_image=Image.open(resource_path("assets/icons/delete.png")),
                size=(20, 20)
            )
            delete_button = ctk.CTkButton(
                category_frame,
                image=delete_icon,
                text="",
                width=30,
                height=30,
                fg_color="transparent",
                hover_color="#8a8585",
                command=lambda c=category: self._delete_category(c)
            )
        except:
            delete_button = ctk.CTkButton(
                category_frame,
                text="🗑️",
                width=30,
                height=30,
                fg_color="transparent",
                hover_color="#8a8585",
                command=lambda c=category: self._delete_category(c)
            )
        delete_button.grid(row=0, column=5, padx=(2, 10), pady=5)

    def _edit_category(self, category):
        """Открывает увеличенное окно для редактирования категории"""
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Редактирование категории: {category.category_name}")
        edit_window.geometry("600x450")  # Увеличенный размер
        edit_window.transient(self)
        edit_window.grab_set()
        
        # Флаг для отслеживания, было ли окно уже закрыто
        window_closed = False
        
        def on_window_close():
            nonlocal window_closed
            window_closed = True
            if edit_window.winfo_exists():
                edit_window.destroy()
        
        edit_window.protocol("WM_DELETE_WINDOW", on_window_close)
        
        edit_window.grid_columnconfigure(0, weight=1)
        edit_window.grid_rowconfigure(0, weight=0)
        edit_window.grid_rowconfigure(1, weight=0)
        edit_window.grid_rowconfigure(2, weight=0)
        edit_window.grid_rowconfigure(3, weight=0)
        edit_window.grid_rowconfigure(4, weight=1)
        
        # Поле для нового названия
        name_label = ctk.CTkLabel(edit_window, text="Новое название категории:", 
                                font=("Arial", 16, "bold"))
        name_label.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")
        
        name_entry = ctk.CTkEntry(edit_window, placeholder_text=category.category_name,
                                 font=("Arial", 16), width=400, height=40)
        name_entry.grid(row=1, column=0, padx=30, pady=10)
        name_entry.insert(0, category.category_name)
        
        # Устанавливаем фокус с задержкой, чтобы избежать ошибки
        edit_window.after(100, lambda: name_entry.focus() if edit_window.winfo_exists() else None)
        
        # Информация о транзакциях
        transactions_count = session.query(TransactionsTable).filter(
            TransactionsTable.category_id == category.category_id
        ).count()
        
        if transactions_count > 0:
            info_label = ctk.CTkLabel(
                edit_window, 
                text=f"⚠ Категория используется в {transactions_count} транзакциях.\n"
                     "При переименовании транзакции обновятся автоматически.",
                font=("Arial", 14),
                text_color="#FF6B6B",
                wraplength=500,
                justify="left"
            )
            info_label.grid(row=2, column=0, padx=30, pady=(20, 10), sticky="w")
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, padx=30, pady=30)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        def save_changes():
            nonlocal window_closed
            if window_closed or not edit_window.winfo_exists():
                return
                
            new_name = name_entry.get().strip()
            if not new_name:
                self._show_error_dialog("Ошибка", "Название категории не может быть пустым!")
                return
            
            if new_name != category.category_name:
                # Проверяем, нет ли уже категории с таким названием
                existing = session.query(CategoriesTable).filter(
                    CategoriesTable.category_name == new_name,
                    CategoriesTable.category_id != category.category_id
                ).first()
                
                if existing:
                    self._show_error_dialog("Ошибка", "Категория с таким названием уже существует!")
                    return
                
                try:
                    # Обновляем название категории
                    category.category_name = new_name
                    session.commit()
                    
                    # Закрываем окно ДО показа сообщения об успехе
                    if edit_window.winfo_exists():
                        edit_window.destroy()
                    
                    # Обновляем отображение ПОСЛЕ закрытия окна
                    self.update_categories_list()
                    
                    # Обновляем категории в главном приложении
                    if hasattr(self.master, 'update_categories'):
                        self.master.update_categories()
                    
                    # Показываем увеличенное сообщение об успехе
                    self._show_success_dialog("Успех", f"Категория успешно переименована в '{new_name}'")
                    
                except Exception as e:
                    session.rollback()
                    self._show_error_dialog("Ошибка", f"Не удалось переименовать категорию: {str(e)}")
            else:
                # Если имя не изменилось, просто закрываем окно
                if edit_window.winfo_exists():
                    edit_window.destroy()
        
        def cancel_changes():
            nonlocal window_closed
            window_closed = True
            if edit_window.winfo_exists():
                edit_window.destroy()
        
        save_button = ctk.CTkButton(buttons_frame, text="Сохранить", 
                                   command=save_changes, 
                                   font=("Arial", 14, "bold"),
                                   height=40, width=150)
        save_button.grid(row=0, column=0, padx=10)
        
        cancel_button = ctk.CTkButton(buttons_frame, text="Отмена", 
                                     command=cancel_changes,
                                     font=("Arial", 14, "bold"),
                                     height=40, width=150)
        cancel_button.grid(row=0, column=1, padx=10)
        
        # Центрируем окно
        edit_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - edit_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - edit_window.winfo_height()) // 2
        edit_window.geometry(f"+{x}+{y}")

    def _delete_category(self, category):
        """Удаляет категорию после подтверждения с увеличенными диалогами"""
        
        # Проверяем, есть ли транзакции с этой категорией
        transactions_count = session.query(TransactionsTable).filter(
            TransactionsTable.category_id == category.category_id
        ).count()
        
        if transactions_count > 0:
            warning_text = f"Категория '{category.category_name}' используется в {transactions_count} транзакциях.\n\n"
            warning_text += "Удаление категории невозможно, пока существуют транзакции с этой категорией.\n"
            warning_text += "Сначала перенесите транзакции в другую категорию или удалите их."
            
            # Создаем увеличенное кастомное диалоговое окно
            self._show_warning_dialog("Невозможно удалить категорию", warning_text)
            return
        
        # Используем увеличенный кастомный диалог для подтверждения
        self._show_confirmation_dialog(category)
    
    def _show_warning_dialog(self, title, message):
        """Показывает увеличенный диалог предупреждения"""
        warning_window = ctk.CTkToplevel(self)
        warning_window.title(title)
        warning_window.geometry("600x400")
        warning_window.resizable(False, False)
        warning_window.transient(self)
        warning_window.grab_set()
        
        warning_window.grid_columnconfigure(0, weight=1)
        warning_window.grid_rowconfigure(0, weight=1)
        warning_window.grid_rowconfigure(1, weight=0)
        
        # Основной фрейм с текстом
        text_frame = ctk.CTkFrame(warning_window, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        # Иконка предупреждения
        icon_label = ctk.CTkLabel(text_frame, text="⚠️", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        # Текстовое поле с прокруткой для длинных сообщений
        error_text = ctk.CTkTextbox(
            text_frame, 
            wrap="word", 
            font=("Arial", 14),
            height=150,
            activate_scrollbars=True
        )
        error_text.grid(row=1, column=0, sticky="nsew", pady=10)
        error_text.insert("1.0", message)
        error_text.configure(state="disabled")
        
        # Кнопка OK
        ok_button = ctk.CTkButton(
            warning_window, 
            text="OK", 
            command=warning_window.destroy,
            font=("Arial", 14, "bold"),
            height=45,
            width=150
        )
        ok_button.grid(row=1, column=0, pady=20)
        
        # Центрируем окно
        warning_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - warning_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - warning_window.winfo_height()) // 2
        warning_window.geometry(f"+{x}+{y}")
    
    def _show_confirmation_dialog(self, category):
        """Показывает увеличенный диалог подтверждения удаления"""
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Подтверждение удаления")
        confirm_window.geometry("550x350")
        confirm_window.resizable(False, False)
        confirm_window.transient(self)
        confirm_window.grab_set()
        
        confirm_window.grid_columnconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(1, weight=0)
        
        # Основной фрейм
        main_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Иконка вопроса
        icon_label = ctk.CTkLabel(main_frame, text="❓", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        # Текст подтверждения
        confirm_text = ctk.CTkLabel(
            main_frame,
            text=f"Вы уверены, что хотите удалить категорию\n'{category.category_name}'?",
            font=("Arial", 16),
            wraplength=450,
            justify="center"
        )
        confirm_text.grid(row=1, column=0, pady=10)
        
        # Дополнительное предупреждение
        warning_text = ctk.CTkLabel(
            main_frame,
            text="Это действие нельзя отменить!",
            font=("Arial", 12),
            text_color="#FF6B6B",
            wraplength=450,
            justify="center"
        )
        warning_text.grid(row=2, column=0, pady=10)
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, pady=20)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        def confirm_delete():
            confirm_window.destroy()
            self._perform_deletion(category)
        
        def cancel_delete():
            confirm_window.destroy()
        
        yes_button = ctk.CTkButton(
            buttons_frame, 
            text="Да, удалить", 
            command=confirm_delete,
            font=("Arial", 14, "bold"),
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            height=45,
            width=150
        )
        yes_button.grid(row=0, column=0, padx=10)
        
        no_button = ctk.CTkButton(
            buttons_frame, 
            text="Отмена", 
            command=cancel_delete,
            font=("Arial", 14, "bold"),
            height=45,
            width=150
        )
        no_button.grid(row=0, column=1, padx=10)
        
        # Центрируем окно
        confirm_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - confirm_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - confirm_window.winfo_height()) // 2
        confirm_window.geometry(f"+{x}+{y}")
    
    def _perform_deletion(self, category):
        """Выполняет удаление категории после подтверждения"""
        try:
            # Удаляем категорию
            session.delete(category)
            session.commit()
            
            # Обновляем отображение
            self.update_categories_list()
            
            # Обновляем категории в главном приложении
            if hasattr(self.master, 'update_categories'):
                self.master.update_categories()
            
            # Увеличенное окно успеха
            self._show_success_dialog("Успех", f"Категория '{category.category_name}' успешно удалена")
            
        except Exception as e:
            session.rollback()
            self._show_error_dialog("Ошибка", f"Не удалось удалить категорию: {str(e)}")
    
    def _show_success_dialog(self, title, message):
        """Показывает увеличенный диалог успеха"""
        success_window = ctk.CTkToplevel(self)
        success_window.title(title)
        success_window.geometry("550x300")
        success_window.resizable(False, False)
        success_window.transient(self)
        success_window.grab_set()
        
        success_window.grid_columnconfigure(0, weight=1)
        success_window.grid_rowconfigure(0, weight=1)
        success_window.grid_rowconfigure(1, weight=0)
        
        # Контейнер для контента
        content_frame = ctk.CTkFrame(success_window, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Иконка успеха
        icon_label = ctk.CTkLabel(content_frame, text="✅", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        # Текст успеха
        success_text = ctk.CTkLabel(
            content_frame, 
            text=message,
            font=("Arial", 16),
            wraplength=450,
            justify="center"
        )
        success_text.grid(row=1, column=0, pady=10)
        
        # Кнопка OK
        ok_button = ctk.CTkButton(
            success_window, 
            text="OK", 
            command=success_window.destroy,
            font=("Arial", 14, "bold"),
            height=45,
            width=150
        )
        ok_button.grid(row=1, column=0, pady=20)
        
        # Центрируем окно
        success_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - success_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - success_window.winfo_height()) // 2
        success_window.geometry(f"+{x}+{y}")
    
    def _show_error_dialog(self, title, message):
        """Показывает увеличенный диалог ошибки"""
        error_window = ctk.CTkToplevel(self)
        error_window.title(title)
        error_window.geometry("600x350")
        error_window.resizable(False, False)
        error_window.transient(self)
        error_window.grab_set()
        
        error_window.grid_columnconfigure(0, weight=1)
        error_window.grid_rowconfigure(0, weight=1)
        error_window.grid_rowconfigure(1, weight=0)
        
        content_frame = ctk.CTkFrame(error_window, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Иконка ошибки
        icon_label = ctk.CTkLabel(content_frame, text="❌", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        error_text = ctk.CTkLabel(
            content_frame,
            text=message,
            font=("Arial", 14),
            wraplength=500,
            justify="center",
            text_color="#FF6B6B"
        )
        error_text.grid(row=1, column=0, pady=10)
        
        ok_button = ctk.CTkButton(
            error_window, 
            text="OK", 
            command=error_window.destroy,
            font=("Arial", 14, "bold"),
            height=45,
            width=150
        )
        ok_button.grid(row=1, column=0, pady=20)
        
        # Центрируем окно
        error_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - error_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - error_window.winfo_height()) // 2
        error_window.geometry(f"+{x}+{y}")

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
    
    def update_icons_in_category_creation(self):
        """Метод для обновления списка иконок в окне создания категории"""
        if hasattr(self.categories_management, 'new_category') and self.categories_management.new_category:
            if self.categories_management.new_category.winfo_exists():
                self.categories_management.new_category.force_update_icons()