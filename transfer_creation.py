import datetime
from decimal import Decimal

import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox
from PIL import Image

from addition_classes import ToggleButton, FormattedEntry, resource_path
from db_management import TransfersTable, session, AccountsTable
from main_page import open_pop_up_calendar
from pop_up_calendar import PopUpCalendar


class AccountsIconsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#aba6a6")

        self.buttons_in_row = 3
        self.selected_account_name = None
        self.accounts_buttons = []
        self.accounts_labels = []

        self.accounts_query = session.query(AccountsTable).all()
        for acc in self.accounts_query:
            exp_image = ctk.CTkImage(light_image=Image.open(resource_path(f"assets/{acc.icon_url}")), size=(40, 40))
            exp_button = ToggleButton(self, text_color="black", text="", width=50, height=50, image=exp_image,
                                      command=lambda n=acc.description: self.select_single(n))
            exp_label = ctk.CTkLabel(self, text_color="black", text=acc.description, wraplength=100)

            self.accounts_buttons.append(exp_button)
            self.accounts_labels.append(exp_label)

        for i, (button, label) in enumerate(zip(self.accounts_buttons, self.accounts_labels)):
            row = (i // self.buttons_in_row) * 2
            col = i % self.buttons_in_row
            button.grid(row=row, column=col, padx=5, pady=(5, 0))
            label.grid(row=row + 1, column=col, padx=5, pady=(0, 10))

    def select_single(self, selected_name):
        items = [acc.description for acc in self.accounts_query]
        buttons = self.accounts_buttons

        self.selected_account_name = selected_name

        for btn, name in zip(buttons, items):
            if name == selected_name:
                btn.select()
            else:
                btn.deselect()

class NewTransferWindow(ctk.CTkToplevel):
    def __init__(self, app_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("600x400+400+100")
        self.title("Создание переводов")

        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.after(250, lambda: self.iconbitmap(resource_path("assets/icons/card-payment.ico")))

        self.configure(fg_color="#aba6a6")
        self.grid_propagate(False)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)
        for i in range(2, 5):
            self.grid_rowconfigure(i, weight=1)

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_columnconfigure(3, weight=3)

        self.pop_up_calendar = PopUpCalendar(False)
        self.pop_up_calendar.withdraw()
        self.transaction_date = None
        self.app_instance = app_instance

        self.from_acc_name = None
        self.to_acc_name = None

        self.from_label = ctk.CTkLabel(self, text_color="black", text="Перевод со счёта", font=("Arial", 20))
        self.to_label = ctk.CTkLabel(self, text_color="black", text="Перевод на счёт", font=("Arial", 20))
        self.from_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.to_label.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.from_accounts_frame = AccountsIconsFrame(self)
        self.to_accounts_frame = AccountsIconsFrame(self)
        self.from_accounts_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.to_accounts_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.amount_entry = FormattedEntry(self, text_color="white", accepted="number",
                                           placeholder_text="Сумма:", placeholder_text_color="white")
        self.amount_entry.grid(row=2, column=0, sticky="nwe", padx=20, pady=5)

        self.comment_entry = ctk.CTkEntry(self, text_color="white", placeholder_text_color="white",
                                           placeholder_text="Комментарий:")
        self.comment_entry.grid(row=3, column=0, sticky="swe", padx=20, pady=5)

        self.calendar_button = ctk.CTkButton(self, text_color="black", font=("Arial", 16), text="Выбрать дату",
                                             command=lambda: open_pop_up_calendar(self, False))
        self.calendar_button.grid(row=2, column=1, sticky="nw", padx=10, pady=5)

        self.date_label = ctk.CTkLabel(self, text_color="black", text=self.get_date_display_text())
        self.date_label.grid(row=2, column=1, sticky="ne", padx=10, pady=5)

        self.hour_label = ctk.CTkLabel(self, text_color="black", text="Часы")
        self.hour_label.grid(row=3, column=1, sticky="w", padx=10, pady=0)

        self.minute_label = ctk.CTkLabel(self, text_color="black", text="Минуты")
        self.minute_label.grid(row=3, column=1, sticky="", padx=10, pady=0)

        self.second_label = ctk.CTkLabel(self, text_color="black", text="Секунды")
        self.second_label.grid(row=3, column=1, sticky="e", padx=10, pady=0)

        self.hour_entry = FormattedEntry(self, formatting=False, placeholder_text="00", width=60, accepted="number")
        self.hour_entry.grid(row=4, column=1, sticky="w", padx=10)

        self.minute_entry = FormattedEntry(self, formatting=False, placeholder_text="00", width=60, accepted="number")
        self.minute_entry.grid(row=4, column=1, sticky="", padx=10)

        self.second_entry = FormattedEntry(self, formatting=False, placeholder_text="00", width=60, accepted="number")
        self.second_entry.grid(row=4, column=1, sticky="e", padx=10)

        self.add_button = ctk.CTkButton(self, text_color="black", text="Добавить",
                                        command=self.add_transfer)
        self.add_button.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def add_transfer(self):
        self.from_acc_name = self.from_accounts_frame.selected_account_name
        self.to_acc_name = self.to_accounts_frame.selected_account_name

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
        amount = Decimal(self.amount_entry.amount)
        description = self.comment_entry.get()


        if not self.from_acc_name or not self.to_acc_name:
            CTkMessagebox.messagebox(title="Ошибка!", text="Выберите иконку счёта!")
            return
        if not amount:
            CTkMessagebox.messagebox(title="Ошибка!", text="Введите сумму!")
            return
        if not date:
            CTkMessagebox.messagebox(title="Ошибка!", text="Укажите дату!")
            return


        from_account = session.query(AccountsTable).filter_by(description=self.from_acc_name).first()
        to_account = session.query(AccountsTable).filter_by(description=self.to_acc_name).first()

        transfer = TransfersTable(
            from_account=from_account.account_id,
            to_account=to_account.account_id,
            transfer_date_time=date_time,
            amount=amount,
            description=description
        )

        amount = Decimal(self.amount_entry.amount)
        from_account.amount -= amount
        to_account.amount += amount

        session.add(transfer)
        session.commit()

        if self.app_instance:
            self.app_instance.update_transfers()
        self._destroy()

    def get_date_display_text(self):
        return datetime.date.today().strftime("%d.%m.%Y") \
            if self.transaction_date is None else self.transaction_date[0].strftime("%d.%m.%Y")

    def _destroy(self):
        self.destroy()
        if self.pop_up_calendar is not None and self.pop_up_calendar.winfo_exists():
            self.pop_up_calendar.destroy()