import customtkinter as ctk
from sqlalchemy import func

from db_management import session, CategoriesTable
from addition_classes import recolor_icon, resource_path
from category_creation import CategoryCreationPage

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
        
        # Создаем фрейм управления категориями
        self.categories_management = CategoriesManagementFrame(self)
        self.categories_management.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def update_categories(self):
        """Метод для обновления списка категорий"""
        self.categories_management.update_categories_list()