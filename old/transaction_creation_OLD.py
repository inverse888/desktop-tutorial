import datetime
from decimal import Decimal

import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox
from PIL import Image

from db_management import AccountsTable, session, CategoriesTable, TransactionsTable
from addition_classes import ToggleButton, app_color, FormattedEntry, resource_path
from main_page import open_pop_up_calendar
from pop_up_calendar import PopUpCalendar

transactions_history = {}

class ButtonsFrame(ctk.CTkFrame):
    def __init__(self, master, income_button_text, expenses_button_text, status_change_callback = None, **kwargs):
        super().__init__(master, **kwargs)
        self.status_change_callback = status_change_callback

        self.configure(fg_color="#aba6a6")
        self.grid_propagate(True)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        self.income_button_text = income_button_text
        self.expenses_button_text = expenses_button_text

        self.status = "Расход"
        self.selected_style = {"fg_color": app_color["dark_blue"], "text_color": "white"}
        self.deselected_style = {"fg_color": app_color["blue"], "text_color": "black"}

        self.income_button = ctk.CTkButton(self, text=income_button_text, font=("Arial", 16), corner_radius=10,
                        command=lambda: self.toggle("Доход"), width=100, height=40, **self.deselected_style)
        self.income_button.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=20)

        self.expenses_button = ctk.CTkButton(self, text=expenses_button_text, font=("Arial", 16), corner_radius=10,
                        command=lambda: self.toggle("Расход"), width=100, height=40,  **self.selected_style)
        self.expenses_button.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=20)

    def toggle(self, selection):
        if selection == self.status:
            return

        self.status = selection
        if self.status_change_callback is not None:
            self.status_change_callback(self.status)

        if selection == "Доход":
            self.income_button.configure(**self.selected_style)
            self.expenses_button.configure(**self.deselected_style)
        else:
            self.income_button.configure(**self.deselected_style)
            self.expenses_button.configure(**self.selected_style)


class CategoriesAccountsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, status, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#aba6a6")

        self.buttons_in_row = 3
        self.status = status
        self.cat_status = "Расход"
        self.selected_category_name = None
        self.selected_account_name = None
        self.income_button_text = master.income_button_text
        self.expenses_button_text = master.expenses_button_text

        self.rowconfigure((0, 1, 2), weight=1)
        for i in range(self.buttons_in_row):
            self.columnconfigure(i, weight=1)

        self.accounts_buttons = []
        self.accounts_labels = []

        self.accs = session.query(AccountsTable).all()
        for acc in self.accs:
            exp_image = ctk.CTkImage(light_image=Image.open(resource_path(f"assets/{acc.icon_url}")), size=(40, 40))
            exp_button = ToggleButton(self, text_color="black", text="", width=50, height=50, image=exp_image,
                                      command=lambda n=acc.description: self.select_single(n))
            exp_label = ctk.CTkLabel(self, text_color="black", text=acc.description, wraplength=100)

            self.accounts_buttons.append(exp_button)
            self.accounts_labels.append(exp_label)


        self.cat_exp_buttons: list[ToggleButton] = []
        self.cat_inc_buttons: list[ToggleButton] = []

        self.cat_exp_labels: list[ctk.CTkLabel] = []
        self.cat_inc_labels: list[ctk.CTkLabel]  = []

        self.cat_exp_query = session.query(CategoriesTable).filter(CategoriesTable.transaction_type == "Расход").all()
        self.cat_inc_query = session.query(CategoriesTable).filter(CategoriesTable.transaction_type == "Доход").all()

        for cat_exp in self.cat_exp_query:
            exp_image = ctk.CTkImage(light_image=Image.open(resource_path(f"assets/{cat_exp.icon_url}")), size=(40, 40))
            exp_button = ToggleButton(self, text_color="black", text="", width=50, height=50, image=exp_image,
                                      command=lambda n=cat_exp.category_name: self.select_single(n))
            exp_label = ctk.CTkLabel(self, text_color="black", text=cat_exp.category_name, wraplength=100)

            self.cat_exp_buttons.append(exp_button)
            self.cat_exp_labels.append(exp_label)

        for cat_inc in self.cat_inc_query:
            inc_image = ctk.CTkImage(light_image=Image.open(resource_path(f"assets/{cat_inc.icon_url}")), size=(40, 40))
            inc_button = ToggleButton(self, text_color="black", text="", width=50, height=50, image=inc_image,
                                      command=lambda n=cat_inc.category_name: self.select_single(n))
            inc_label = ctk.CTkLabel(self, text_color="black", text=cat_inc.category_name, wraplength=100)

            self.cat_inc_buttons.append(inc_button)
            self.cat_inc_labels.append(inc_label)

        self.update_display()

    def select_single(self, selected_name):
        if self.status == self.expenses_button_text:
            if self.cat_status == "Расход":
                items = [cat.category_name for cat in self.cat_exp_query]
                buttons = self.cat_exp_buttons
            else:
                items = [cat.category_name for cat in self.cat_inc_query]
                buttons = self.cat_inc_buttons
            self.selected_category_name = selected_name
        else:
            items = [acc.description for acc in self.accs]
            buttons = self.accounts_buttons
            self.selected_account_name = selected_name

        for btn, name in zip(buttons, items):
            if name == selected_name:
                btn.select()
                if self.status == self.expenses_button_text:
                    self.selected_category_name = selected_name
                else:
                    self.selected_account_name = selected_name
            else:
                btn.deselect()

    def update_display(self):
        self.clear_all_buttons()

        if self.status == self.income_button_text:
            self.show_accounts()
        else:
            if self.cat_status == "Расход":
                self.show_category_group(self.cat_exp_buttons, self.cat_exp_labels)
            elif self.cat_status == "Доход":
                self.show_category_group(self.cat_inc_buttons, self.cat_inc_labels)
            else:
                raise ValueError("Неверный тип категории")

    def clear_all_buttons(self):
        for widgets in [
            self.accounts_buttons + self.accounts_labels,
            self.cat_exp_buttons + self.cat_exp_labels,
            self.cat_inc_buttons + self.cat_inc_labels,
        ]:
            for widget in widgets:
                widget.grid_remove()

    def show_accounts(self):
        for i, (button, label) in enumerate(zip(self.accounts_buttons, self.accounts_labels)):
            row = (i // self.buttons_in_row) * 2
            col = i % self.buttons_in_row
            button.grid(row=row, column=col, padx=5, pady=(5, 0))
            label.grid(row=row + 1, column=col, padx=5, pady=(0, 10))

    def show_category_group(self, buttons, labels):
        for i, (button, label) in enumerate(zip(buttons, labels)):
            row = (i // self.buttons_in_row) * 2
            col = i % self.buttons_in_row
            button.grid(row=row, column=col, padx=5, pady=(5, 0))
            label.grid(row=row + 1, column=col, padx=5, pady=(0, 10))

        self.reselect_category_button(buttons, labels)

    def reselect_category_button(self, buttons, labels):
        if not self.selected_category_name:
            return

        found = False
        for button, label in zip(buttons, labels):
            if label.cget("text") == self.selected_category_name:
                button.select()
                found = True
            else:
                button.deselect()

        if not found:
            self.selected_category_name = None


class NewTransactionWindow(ctk.CTkToplevel):
    def __init__(self, app_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("600x400+400+100")
        self.title("Создание транзакции")

        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.after(250, lambda: self.iconbitmap(resource_path("assets/icons/pay-per-click.ico")))

        self.configure(fg_color="#aba6a6")
        self.grid_propagate(False)

        for i in range(6):
            self.grid_rowconfigure(i, weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure(3, weight=3)

        self.pop_up_calendar = PopUpCalendar(False)
        self.pop_up_calendar.withdraw()
        self.transaction_date = None
        self.app_instance = app_instance

        self.cat_acc_buttons = ButtonsFrame(self, income_button_text="Счета", expenses_button_text="Категории",
                                            status_change_callback=self.show_cat_acc_by_status)
        self.cat_acc_buttons.grid(row=0, column=0, columnspan=2, sticky="new", padx=10, pady=(0, 10))

        self.income_button_text = "Доход"
        self.expenses_button_text = "Расход"

        self.cat_acc_frame = CategoriesAccountsFrame(self, self.cat_acc_buttons.status)
        self.cat_acc_frame.grid(row=1, column=0, rowspan=3, columnspan=2, sticky="new", padx=0, pady=20)

        self.inc_exp_cats_button = ctk.CTkButton(self, text_color="black", text=self.expenses_button_text,
                                                 command=self.change_state, corner_radius=10)
        self.inc_exp_cats_button.grid(row=0, column=2, columnspan=2, sticky="ns", padx=10, pady=(20, 30))

        self.comment_entry = ctk.CTkEntry(self, text_color="black", placeholder_text_color="black",
                                           placeholder_text="Комментарий:")
        self.comment_entry.grid(row=1, column=3, sticky="swe", padx=20, pady=5)

        self.amount_entry = FormattedEntry(self, text_color="black", accepted="number",
                                           placeholder_text="Сумма:", placeholder_text_color="black")
        self.amount_entry.grid(row=1, column=3, sticky="nwe", padx=20, pady=5)

        self.receipt_entry = ctk.CTkEntry(self, text_color="black", placeholder_text_color="black",
                                           placeholder_text="Файл чека (с расширением .jpg/.png)")
        self.receipt_entry.grid(row=1, column=3, sticky="we", padx=20, pady=5)

        self.calendar_button = ctk.CTkButton(self, text_color="black", font=("Arial", 16), text="Выбрать дату",
                                             command=lambda: open_pop_up_calendar(self, False))
        self.calendar_button.grid(row=2, column=3, sticky="nw", padx=10, pady=5)


        self.date_label = ctk.CTkLabel(self, text_color="black", text=self.get_date_display_text())
        self.date_label.grid(row=2, column=3, sticky="ne", padx=10, pady=5)

        self.hour_label = ctk.CTkLabel(self, text_color="black", text="Часы")
        self.hour_label.grid(row=3, column=3, sticky="w", padx=10, pady=0)

        self.minute_label = ctk.CTkLabel(self, text_color="black", text="Минуты")
        self.minute_label.grid(row=3, column=3, sticky="", padx=10, pady=0)

        self.second_label = ctk.CTkLabel(self, text_color="black", text="Секунды")
        self.second_label.grid(row=3, column=3, sticky="e", padx=10, pady=0)

        self.hour_entry = FormattedEntry(self, formatting=False, placeholder_text="00", width=60, accepted="number")
        self.hour_entry.grid(row=4, column=3, sticky="w", padx=10)

        self.minute_entry = FormattedEntry(self, formatting=False, placeholder_text="00", width=60, accepted="number")
        self.minute_entry.grid(row=4, column=3, sticky="", padx=10)

        self.second_entry = FormattedEntry(self, formatting=False, placeholder_text="00", width=60, accepted="number")
        self.second_entry.grid(row=4, column=3, sticky="e", padx=10)

        self.add_button = ctk.CTkButton(self, text_color="black", text="Добавить",
                                        command=self.add_transaction)
        self.add_button.grid(row=5, column=3, sticky="nsew", padx=20, pady=(10, 20))

    def add_transaction(self):
        account_name = self.cat_acc_frame.selected_account_name
        category_name = self.cat_acc_frame.selected_category_name
        category_type = self.cat_acc_frame.cat_status

        if self.pop_up_calendar and self.pop_up_calendar.frame and self.pop_up_calendar.frame.date_range \
                and self.pop_up_calendar.frame.date_range[0]:
            date = datetime.datetime.combine(self.pop_up_calendar.frame.date_range[0], datetime.time.min).date()
        else:
            date = datetime.date.today()

        hours = int(self.hour_entry.get()) if self.hour_entry.get() else 0
        minutes = int(self.minute_entry.get()) if self.minute_entry.get() else 0
        seconds = int(self.second_entry.get()) if self.second_entry.get() else 0
        if not 0 <= hours < 24 or not 0 <= minutes < 60 or not 0 <= seconds < 60:
            CTkMessagebox.messagebox(title="Ошибка!", text="Неверное время!")
            return

        date_time = datetime.datetime.combine(date, datetime.time(
                int(self.hour_entry.get() or 0),
                int(self.minute_entry.get() or 0),
                int(self.second_entry.get() or 0)
            ))

        amount = self.amount_entry.amount
        description = self.comment_entry.get()

        receipt_name = (resource_path(f"assets/receipts/{self.receipt_entry.get()}")
                        if len(self.receipt_entry.get()) > 0 else None)

        if not account_name:
            CTkMessagebox.messagebox(title="Ошибка!", text="Выберите иконку счёта!")
            return
        if not amount:
            CTkMessagebox.messagebox(title="Ошибка!", text="Введите сумму!")
            return
        if not date:
            CTkMessagebox.messagebox(title="Ошибка!", text="Укажите дату!")
            return
        if not category_name and category_type == self.expenses_button_text:
            CTkMessagebox.messagebox(title="Ошибка!", text="Укажите категорию!")
            return
        if not receipt_name.lower().endswith(('.jpg', '.png')):
            CTkMessagebox.messagebox(title="Ошибка!", text="Файл чека должен быть в формате .jpg или .png!")
            return

        account = session.query(AccountsTable).filter_by(description=account_name).first()
        category = session.query(CategoriesTable).filter_by(category_name=category_name).first()

        transaction = TransactionsTable(
            transaction_date_time=date_time,
            transaction_type=category_type,
            amount=float(amount),
            description=description,
            account_id=account.account_id,
            category_id=category.category_id,
            check_photo_url=receipt_name
        )

        amount = Decimal(self.amount_entry.amount)
        if category_type == self.expenses_button_text:
            account.amount -= amount
        else:
            account.amount += amount

        session.add(transaction)
        session.commit()

        if self.app_instance:
            self.app_instance.update_transactions()
        self._destroy()

    def change_state(self):
        self.cat_acc_frame.cat_status = "Расход" if self.cat_acc_frame.cat_status == "Доход" else "Доход"
        self.inc_exp_cats_button.configure(text=self.cat_acc_frame.cat_status)
        self.cat_acc_frame.update_display()

    def _destroy(self):
        self.destroy()
        if self.pop_up_calendar is not None and self.pop_up_calendar.winfo_exists():
            self.pop_up_calendar.destroy()

    def show_cat_acc_by_status(self, status):
        self.status = status
        self.cat_acc_frame.status = status
        self.cat_acc_frame.update_display()

    def update_text(self):
        date_text = self.get_date_display_text()
        self.date_label.configure(text=date_text)

    def get_date_display_text(self):
        return datetime.date.today().strftime("%d.%m.%Y") \
            if self.transaction_date is None else self.transaction_date[0].strftime("%d.%m.%Y")


