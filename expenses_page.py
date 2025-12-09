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

    def update_by_category(self, category_name):
        self.stacked_bar.show_single_category(category_name)


class IncomeFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")

        self.master = master

        self.name_label = ctk.CTkLabel(self, text_color="black", text="Основные доходы", font=("Arial", 24))
        self.name_label.grid(row=0, column=0, columnspan=3, padx=20, pady=10, sticky="w")  # Убрали columnspan=2

        # УБИРАЕМ кнопку добавления категории отсюда
        # self.add_category = ctk.CTkButton(self,  text_color="black", text="Добавить категорию", font=("Arial", 18),
        #                                   command=self._create_category)
        # self.add_category.grid(row=0, column=3, pady=10, sticky="nse")

        self.categories_model = (
            session.query(CategoriesTable, TransactionsTable)
            .join(TransactionsTable, CategoriesTable.category_id == TransactionsTable.category_id)
            .filter(TransactionsTable.transaction_type == 'Доход')
            .all()
        )

        self.update_frame()

    def update_frame(self):
        total_amount = (session.query(func.sum(TransactionsTable.amount))
            .filter(TransactionsTable.transaction_type == "Доход").scalar())
        total_amount_label = ctk.CTkLabel(self, text_color="black",
                                               text=f"Итого за период: {safe_format_currency(total_amount)}", font=("Arial", 24))
        total_amount_label.grid(row=1, column=0, columnspan=3, padx=20, pady=20, sticky="w")

        for i, (cat, trans) in enumerate(self.categories_model):
            icon_image = ctk.CTkImage(
                light_image=recolor_icon(resource_path(f"assets/{cat.icon_url}"), fg_color=cat.colour),
                size=(50, 50)
            )
            icon_label = ctk.CTkLabel(self, image=icon_image, text="")
            icon_label.grid(row=i+2, column=0, pady=10, sticky="e")

            category_name_label = ctk.CTkLabel(self, text_color="black", text=cat.category_name, font=("Arial", 20))
            category_name_label.grid(row=i+2, column=1, pady=10, sticky="nsew")

            date_label = ctk.CTkLabel(self, text_color="black", text=trans.transaction_date_time.date(), font=("Arial", 20))
            date_label.grid(row=i+2, column=2, pady=10, sticky="e")

            amount_label = ctk.CTkLabel(self, text_color="black", font=("Arial", 20),
                                        text=f"{trans.amount:,.2f}")
            amount_label.grid(row=i+2, column=3, padx=(0, 10), pady=10, sticky="e")

    # УБИРАЕМ методы создания категории из этого класса
    # def _create_category(self):
    #     if not self.new_category.winfo_exists():
    #         self.new_category = CategoryCreationPage(self.master)
    #
    #     self.new_category.attributes('-topmost', True)
    #     self.new_category.deiconify()
    #     self.new_category.update()
    #     self.new_category.focus()
    #
    #     self.new_category.bind("<<DateSelected>>", lambda x: self.close_pop_up_window())
    #
    # def close_pop_up_window(self):
    #     self.new_category.destroy()


class CategoriesFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        self.master = master

        self.frame_name = ctk.CTkLabel(self, text_color="black", text="Категории", font=("Arial", 24))
        self.frame_name.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=20)

        self.select_all_button = ctk.CTkButton(self, text_color="black", text="Выбрать все", font=("Arial", 18),
                                               command=self.deselect_all, width=200, height=50)
        self.select_all_button.grid(row=1, column=0, columnspan=2, padx=20, pady=20)

        self.categories_buttons = []
        self.selected_category_name = None
        self.cats = (session.query(CategoriesTable).filter(CategoriesTable.transaction_type == "Расход")
                     .order_by(CategoriesTable.category_name).all())

        self.update_categories()

    def update_categories(self):
        for i, cat in enumerate(self.cats):
            icon_image = ctk.CTkImage(light_image=recolor_icon(resource_path(f"assets/{cat.icon_url}"),
                                                               fg_color=cat.colour), size=(50, 50))
            category_button = ToggleButton(self, image=icon_image, text="", width=50, height=50,
                                            command=lambda n=cat.category_name: self.select_single(n))
            category_button.grid(row=i+2, column=0, padx=(30, 0), pady=10, sticky="w")

            self.categories_buttons.append(category_button)

            category_name_label = ctk.CTkLabel(self, text_color="black", text=cat.category_name, font=("Arial", 18))
            category_name_label.grid(row=i+2, column=1, pady=10, sticky="w")

    def select_single(self, selected_name):
        items = [cat.category_name for cat in self.cats]
        buttons = self.categories_buttons

        self.selected_category_name = selected_name

        for btn, name in zip(buttons, items):
            if name == selected_name:
                btn.select()
            else:
                btn.deselect()

        self.update_stats(self.selected_category_name)

    def deselect_all(self):
        for btn in self.categories_buttons:
            btn.deselect()

        self.selected_category_name = None
        self.master.period_buttons.toggle(self.master, self.master.period_buttons.selected_period)

    def update_stats(self, category_name):
        self.master.stats_frame.update_by_category(category_name)


class ExpensesPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=4)
        self.grid_rowconfigure(1, weight=20)
        self.grid_rowconfigure(2, weight=9)

        self.period_buttons = PeriodButtons(self)
        self.period_buttons.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=(20, 10))

        self.transaction_date: list[datetime.date] = \
            [datetime.date.today() - datetime.timedelta(days=6), datetime.date.today()]

        self.stats_frame = StatsFrame(self)
        self.stats_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)

        self.income_frame = IncomeFrame(self, orientation="vertical")
        self.income_frame.grid(row=2, column=0, sticky="nsew", padx=(20, 10), pady=(10, 20))

        self.categories_frame = CategoriesFrame(self, orientation="vertical")
        self.categories_frame.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(10, 20), pady=(20, 20))

    def update_chart(self, dates: list[datetime.date], period):
        new_data = get_expense_data(dates[0], dates[1], period)
        self.stats_frame.stacked_bar.update_data(new_data, period, dates[0], dates[1])

    def update_delta(self, days):
        self.stats_frame.days_delta = days

        today = datetime.date.today()
        self.transaction_date = [today - datetime.timedelta(days=days), today]

    def update_transactions(self):
        self.update_chart(self.transaction_date, "Same")
        self.income_frame.update_frame()

    def update_categories(self):
        self.categories_frame.update_categories()