import datetime
from decimal import Decimal

import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox
from PIL import Image

from addition_classes import ToggleButton, resource_path
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
        self.geometry("700x500+400+100")
        self.title("Создание переводов")

        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.safe_destroy)
        self.after(250, lambda: self.iconbitmap(resource_path("assets/icons/card-payment.ico")))

        self.configure(fg_color="#aba6a6")
        self.grid_propagate(False)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=2)

        self.pop_up_calendar = PopUpCalendar(False)
        self.pop_up_calendar.withdraw()
        self.transaction_date = None
        self.app_instance = app_instance
        self._destroying = False

        self.from_acc_name = None
        self.to_acc_name = None

        self.from_label = ctk.CTkLabel(self, text_color="black", text="Перевод со счёта", font=("Arial", 18, "bold"))
        self.to_label = ctk.CTkLabel(self, text_color="black", text="Перевод на счёт", font=("Arial", 18, "bold"))
        self.from_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=(15, 5))
        self.to_label.grid(row=0, column=1, sticky="nsew", padx=20, pady=(15, 5))

        self.from_accounts_frame = AccountsIconsFrame(self, height=200)
        self.to_accounts_frame = AccountsIconsFrame(self, height=200)
        self.from_accounts_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(5, 15))
        self.to_accounts_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=(5, 15))

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=1)
        self.input_frame.grid_columnconfigure(2, weight=2)

        self.amount_entry = ctk.CTkEntry(self.input_frame, text_color="white", 
                                         placeholder_text="Сумма перевода", placeholder_text_color="gray",
                                         font=("Arial", 14), height=35)
        self.amount_entry.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 10), pady=5)

        self.comment_entry = ctk.CTkEntry(self.input_frame, text_color="white", placeholder_text_color="gray",
                                          placeholder_text="Комментарий к переводу", font=("Arial", 14), height=35)
        self.comment_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 10), pady=5)

        # Кнопка календаря с отображением даты
        self.calendar_button = ctk.CTkButton(self.input_frame, text_color="black", font=("Arial", 14), 
                                             text=self.get_date_display_text(), height=35,
                                             command=lambda: open_pop_up_calendar(self, False))
        self.calendar_button.grid(row=0, column=2, sticky="ew", padx=(10, 0), pady=5)
        
        # Добавляем пустую метку для сохранения структуры сетки
        self.empty_label = ctk.CTkLabel(self.input_frame, text="", font=("Arial", 14))
        self.empty_label.grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=5)

        self.time_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.time_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=20, pady=(10, 5))
        self.time_frame.grid_columnconfigure(0, weight=1)
        self.time_frame.grid_columnconfigure(1, weight=1)
        self.time_frame.grid_columnconfigure(2, weight=1)
        self.time_frame.grid_columnconfigure(3, weight=3)

        self.hour_label = ctk.CTkLabel(self.time_frame, text_color="black", text="Часы", font=("Arial", 12))
        self.hour_label.grid(row=0, column=0, sticky="w", padx=5, pady=0)

        self.minute_label = ctk.CTkLabel(self.time_frame, text_color="black", text="Минуты", font=("Arial", 12))
        self.minute_label.grid(row=0, column=1, sticky="w", padx=5, pady=0)

        self.second_label = ctk.CTkLabel(self.time_frame, text_color="black", text="Секунды", font=("Arial", 12))
        self.second_label.grid(row=0, column=2, sticky="w", padx=5, pady=0)

        self.hour_entry = ctk.CTkEntry(self.time_frame, placeholder_text="00", width=70, 
                                       placeholder_text_color="gray", font=("Arial", 14), height=35)
        self.hour_entry.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.minute_entry = ctk.CTkEntry(self.time_frame, placeholder_text="00", width=70, 
                                         placeholder_text_color="gray", font=("Arial", 14), height=35)
        self.minute_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        self.second_entry = ctk.CTkEntry(self.time_frame, placeholder_text="00", width=70, 
                                         placeholder_text_color="gray", font=("Arial", 14), height=35)
        self.second_entry.grid(row=1, column=2, sticky="w", padx=5, pady=5)

        self.add_button = ctk.CTkButton(self, text_color="black", text="Добавить перевод",
                                        command=self.add_transfer, font=("Arial", 16, "bold"),
                                        height=45)
        self.add_button.grid(row=5, column=0, columnspan=2, sticky="ew", padx=100, pady=20)
        
        # Привязываем событие обновления даты
        self.bind("<<DateSelected>>", self.update_date_display)

    def update_date_display(self, event=None):
        """Обновляет отображение даты на кнопке"""
        if self._destroying:
            return
        self.calendar_button.configure(text=self.get_date_display_text())

    def add_transfer(self):
        if self._destroying:
            return
            
        self.from_acc_name = self.from_accounts_frame.selected_account_name
        self.to_acc_name = self.to_accounts_frame.selected_account_name

        if self.pop_up_calendar and self.pop_up_calendar.frame and self.pop_up_calendar.frame.date_range \
                and self.pop_up_calendar.frame.date_range[0]:
            date = datetime.datetime.combine(self.pop_up_calendar.frame.date_range[0], datetime.time.min).date()
        else:
            date = datetime.date.today()
        
        hours_str = self.hour_entry.get()
        minutes_str = self.minute_entry.get()
        seconds_str = self.second_entry.get()
        
        now = datetime.datetime.now()
        
        if not hours_str or hours_str == "00":
            hours = now.hour
        else:
            try:
                hours = int(hours_str)
            except ValueError:
                hours = now.hour
            
        if not minutes_str or minutes_str == "00":
            minutes = now.minute
        else:
            try:
                minutes = int(minutes_str)
            except ValueError:
                minutes = now.minute
            
        if not seconds_str or seconds_str == "00":
            seconds = now.second
        else:
            try:
                seconds = int(seconds_str)
            except ValueError:
                seconds = now.second
        
        if not 0 <= hours < 24 or not 0 <= minutes < 60 or not 0 <= seconds < 60:
            CTkMessagebox.messagebox(title="Ошибка!", text="Неверное время! Используйте значения от 0 до 23 для часов и от 0 до 59 для минут и секунд.")
            return

        date_time = datetime.datetime.combine(date, datetime.time(hours, minutes, seconds))
        
        amount_str = self.amount_entry.get()
        
        if not amount_str:
            CTkMessagebox.messagebox(title="Ошибка!", text="Введите сумму!")
            return
        
        try:
            amount_str = amount_str.replace(',', '.')
            amount = Decimal(amount_str)
        except:
            CTkMessagebox.messagebox(title="Ошибка!", text="Некорректный формат суммы!")
            return

        description = self.comment_entry.get()

        if not self.from_acc_name or not self.to_acc_name:
            CTkMessagebox.messagebox(title="Ошибка!", text="Выберите счета для перевода!")
            return
        
        if self.from_acc_name == self.to_acc_name:
            CTkMessagebox.messagebox(title="Ошибка!", text="Счета отправителя и получателя должны быть разными!")
            return
        
        if amount <= 0:
            CTkMessagebox.messagebox(title="Ошибка!", text="Сумма должна быть больше нуля!")
            return

        from_account = session.query(AccountsTable).filter_by(description=self.from_acc_name).first()
        to_account = session.query(AccountsTable).filter_by(description=self.to_acc_name).first()
        
        if not from_account or not to_account:
            CTkMessagebox.messagebox(title="Ошибка!", text="Один из счетов не найден!")
            return
        
        if from_account.amount < amount:
            CTkMessagebox.messagebox(title="Ошибка!", text=f"Недостаточно средств на счёте {self.from_acc_name}!")
            return

        transfer = TransfersTable(
            from_account=from_account.account_id,
            to_account=to_account.account_id,
            transfer_date_time=date_time,
            amount=amount,
            description=description
        )

        from_account.amount -= amount
        to_account.amount += amount

        session.add(transfer)
        session.commit()

        # Обновляем все страницы после создания перевода
        if self.app_instance and hasattr(self.app_instance, 'force_update_all'):
            self.app_instance.force_update_all()
        
        CTkMessagebox.messagebox(title="Успех!", text="Перевод успешно выполнен!")
        
        self.after(100, self.safe_destroy)

    def get_date_display_text(self):
        """Возвращает текст для отображения даты"""
        if self.transaction_date is not None and self.transaction_date[0]:
            return self.transaction_date[0].strftime("%d.%m.%Y")
        else:
            return datetime.date.today().strftime("%d.%m.%Y")

    def safe_destroy(self):
        if self._destroying:
            return
        
        self._destroying = True
        
        try:
            self.attributes('-topmost', False)
            
            try:
                self.unbind_all("<<DateSelected>>")
            except:
                pass
            
            if hasattr(self, 'pop_up_calendar') and self.pop_up_calendar is not None:
                try:
                    if self.pop_up_calendar.winfo_exists():
                        self.pop_up_calendar.destroy()
                except:
                    pass
                finally:
                    self.pop_up_calendar = None
            
            try:
                if self.winfo_exists():
                    self.destroy()
            except:
                pass
                
        except Exception as e:
            print(f"Ошибка при уничтожении окна: {e}")
        finally:
            self._destroying = False