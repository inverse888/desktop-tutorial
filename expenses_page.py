import datetime

import customtkinter as ctk
from sqlalchemy import func

from db_management import session, CategoriesTable, TransactionsTable
from addition_classes import recolor_icon, get_expense_data, ExpensesPageStackedBar, PeriodButtons, ToggleButton
from category_creation import resource_path

def safe_format_currency(value, default="0.00"):
    """Безопасное форматирование денежных значений"""
    if value is None:
        return default
    try:
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return default


class StatsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.days_delta = 6

        self.stacked_bar = ExpensesPageStackedBar(self, master.transaction_date, title="")
        self.stacked_bar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def update_by_category(self, category_names):
        if isinstance(category_names, str):
            category_names = [category_names]
        
        if not category_names:
            self.stacked_bar.create_stacked_bar()
        else:
            self.stacked_bar.show_multiple_categories(category_names)


class IncomeFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        self._update_lock = False
        self._pending_update = False
        
        self.grid_columnconfigure(0, weight=0, minsize=70)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)
        self.grid_columnconfigure(3, weight=1)
        
        self.update_frame()

    def schedule_update(self):
        if self._update_lock:
            self._pending_update = True
            return
        
        self._update_lock = True
        self._pending_update = False
        self.after(300, self._perform_update)
    
    def _perform_update(self):
        try:
            self.update_frame()
        finally:
            self._update_lock = False
            if self._pending_update:
                self._pending_update = False
                self.schedule_update()

    def update_frame(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        self.name_label = ctk.CTkLabel(
            self, text_color="black", text="Основные доходы", font=("Arial", 24, "bold")
        )
        self.name_label.grid(row=0, column=0, columnspan=4, padx=20, pady=(10, 5), sticky="w")
        
        headers = ["", "Категория", "Дата", "Сумма"]
        for col, header in enumerate(headers):
            header_label = ctk.CTkLabel(
                self, text=header, text_color="black", font=("Arial", 14, "bold")
            )
            if col == 0:
                header_label.grid(row=1, column=col, padx=20, pady=5, sticky="w")
            elif col == 3:
                header_label.grid(row=1, column=col, padx=10, pady=5, sticky="e")
            else:
                header_label.grid(row=1, column=col, padx=10, pady=5, sticky="w")
        
        total_amount = session.query(func.sum(TransactionsTable.amount)).filter(
            TransactionsTable.transaction_type == "Доход"
        ).scalar()
        
        total_amount_label = ctk.CTkLabel(
            self, text_color="black",
            text=f"Итого за период: {safe_format_currency(total_amount)}", 
            font=("Arial", 20, "bold")
        )
        total_amount_label.grid(row=2, column=0, columnspan=4, padx=20, pady=(20, 10), sticky="w")

        self.categories_model = (
            session.query(CategoriesTable, TransactionsTable)
            .join(TransactionsTable, CategoriesTable.category_id == TransactionsTable.category_id)
            .filter(TransactionsTable.transaction_type == 'Доход')
            .order_by(TransactionsTable.transaction_date_time.desc())
            .all()
        )

        if not self.categories_model:
            empty_label = ctk.CTkLabel(
                self, text="Нет доходов", font=("Arial", 16), text_color="gray"
            )
            empty_label.grid(row=3, column=0, columnspan=4, padx=20, pady=30)
            return

        for i, (cat, trans) in enumerate(self.categories_model):
            row = i + 3
            
            icon_image = ctk.CTkImage(
                light_image=recolor_icon(resource_path(f"assets/{cat.icon_url}"), fg_color=cat.colour),
                size=(40, 40)
            )
            icon_label = ctk.CTkLabel(self, image=icon_image, text="", width=50)
            icon_label.grid(row=row, column=0, padx=20, pady=8, sticky="w")
            icon_label.image = icon_image

            category_name_label = ctk.CTkLabel(
                self, text_color="black", text=cat.category_name, font=("Arial", 16), anchor="w"
            )
            category_name_label.grid(row=row, column=1, padx=10, pady=8, sticky="w")

            date_label = ctk.CTkLabel(
                self, text_color="black", text=trans.transaction_date_time.strftime("%Y-%m-%d"), font=("Arial", 14)
            )
            date_label.grid(row=row, column=2, padx=10, pady=8, sticky="w")

            amount_label = ctk.CTkLabel(
                self, text_color="green", font=("Arial", 16, "bold"),
                text=f"{trans.amount:,.2f}", anchor="e"
            )
            amount_label.grid(row=row, column=3, padx=10, pady=8, sticky="e")


class CategoriesFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        
        self.master = master
        self.selected_categories = []
        self.category_items = []
        self.cats = []
        
        self.frame_name = ctk.CTkLabel(
            self, text_color="black", text="Категории расходов", font=("Arial", 24, "bold")
        )
        self.frame_name.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        self.buttons_control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_control_frame.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.buttons_control_frame.grid_columnconfigure(0, weight=1)
        self.buttons_control_frame.grid_columnconfigure(1, weight=1)
        
        self.select_all_button = ctk.CTkButton(
            self.buttons_control_frame, text_color="black", text="Выбрать все", 
            font=("Arial", 14), command=self.select_all, width=150, height=40
        )
        self.select_all_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.deselect_all_button = ctk.CTkButton(
            self.buttons_control_frame, text_color="black", text="Снять все", 
            font=("Arial", 14), command=self.deselect_all, width=150, height=40
        )
        self.deselect_all_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="#aba6a6")
        self.scrollable_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.update_categories()

    def update_categories(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.cats = (session.query(CategoriesTable)
                    .filter(CategoriesTable.transaction_type == "Расход")
                    .order_by(CategoriesTable.category_name).all())
        
        if not self.cats:
            empty_label = ctk.CTkLabel(
                self.scrollable_frame, text="Нет категорий расходов", 
                font=("Arial", 16), text_color="gray"
            )
            empty_label.grid(row=0, column=0, padx=20, pady=30)
            return
        
        self.category_items = []
        for i, cat in enumerate(self.cats):
            item_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#aba6a6")
            item_frame.grid(row=i, column=0, sticky="ew", padx=10, pady=2)
            item_frame.grid_columnconfigure(0, weight=0, minsize=80)
            item_frame.grid_columnconfigure(1, weight=1)
            
            icon_image = ctk.CTkImage(
                light_image=recolor_icon(resource_path(f"assets/{cat.icon_url}"), fg_color=cat.colour), 
                size=(45, 45)
            )
            
            category_button = ToggleButton(
                item_frame, image=icon_image, text="", width=55, height=55,
                fg_color="transparent", hover_color="#8a8585"
            )
            category_button.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
            
            category_name_label = ctk.CTkLabel(
                item_frame, text_color="black", text=cat.category_name, 
                font=("Arial", 18), cursor="hand2"
            )
            category_name_label.grid(row=0, column=1, pady=10, sticky="w")
            
            item_data = {
                "frame": item_frame,
                "button": category_button,
                "label": category_name_label,
                "name": cat.category_name,
                "index": i
            }
            self.category_items.append(item_data)
            
            category_button.configure(command=lambda idx=i, b=category_button: self.toggle_category_by_index(idx, b))
            category_name_label.bind("<Button-1>", lambda e, idx=i, b=category_button: self.toggle_category_by_index(idx, b))
            
            if cat.category_name in self.selected_categories:
                category_button.select()
    
    def toggle_category_by_index(self, category_index, button):
        category_name = self.cats[category_index].category_name
        
        if category_name in self.selected_categories:
            self.selected_categories.remove(category_name)
            button.deselect()
        else:
            self.selected_categories.append(category_name)
            button.select()
        
        self.update_stats(self.selected_categories)
    
    def select_all(self):
        self.selected_categories = [cat.category_name for cat in self.cats]
        for item in self.category_items:
            item["button"].select()
        self.update_stats(self.selected_categories)
    
    def deselect_all(self):
        self.selected_categories = []
        for item in self.category_items:
            item["button"].deselect()
        self.update_stats([])
    
    def update_stats(self, category_names):
        self.master.stats_frame.update_by_category(category_names)


class ExpensesPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.period_buttons = PeriodButtons(self)
        self.period_buttons.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=(20, 10))

        self.transaction_date = [datetime.date.today() - datetime.timedelta(days=6), datetime.date.today()]

        self.stats_frame = StatsFrame(self)
        self.stats_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)

        self.income_frame = IncomeFrame(self, orientation="vertical")
        self.income_frame.grid(row=2, column=0, sticky="nsew", padx=(20, 10), pady=(10, 20))

        self.categories_frame = CategoriesFrame(self)
        self.categories_frame.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(10, 20), pady=(20, 20))

    def update_chart(self, dates, period):
        """Обновляет график"""
        new_data = get_expense_data(dates[0], dates[1], period)
        
        if hasattr(self.stats_frame, 'stacked_bar') and self.stats_frame.stacked_bar:
            self.stats_frame.stacked_bar.update_data(new_data, period, dates[0], dates[1])
            self.stats_frame.stacked_bar.update_idletasks()

    def update_delta(self, days):
        """Обновляет период на основе выбранного количества дней"""
        self.stats_frame.days_delta = days
        today = datetime.date.today()
        
        if days == 0:
            # За день - только сегодня
            self.transaction_date = [today, today]
        elif days == 6:
            # За неделю - последние 7 дней (включая сегодня)
            self.transaction_date = [today - datetime.timedelta(days=days), today]
        elif days == 30:
            # За месяц - с 1 числа текущего месяца по сегодня
            first_day_of_month = datetime.date(today.year, today.month, 1)
            self.transaction_date = [first_day_of_month, today]
        else:
            # По умолчанию
            self.transaction_date = [today - datetime.timedelta(days=days), today]

    def update_transactions(self):
        self.update_chart(self.transaction_date, "Same")
        self.income_frame.schedule_update()

    def update_categories(self):
        self.categories_frame.update_categories()
    
    def force_refresh(self):
        """Принудительно обновляет график и список доходов"""
        try:
            # Обновляем график
            if hasattr(self, 'update_chart'):
                self.update_chart(self.transaction_date, "Same")
            
            # Обновляем список доходов
            if hasattr(self, 'income_frame'):
                if hasattr(self.income_frame, 'update_frame'):
                    self.income_frame.update_frame()
            
            # Обновляем категории расходов
            if hasattr(self, 'categories_frame'):
                if hasattr(self.categories_frame, 'update_categories'):
                    self.categories_frame.update_categories()
            
            # Принудительно обновляем отображение
            self.update_idletasks()
            
        except Exception as e:
            print(f"Ошибка при обновлении страницы расходов: {e}")