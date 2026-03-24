import customtkinter as ctk
from PIL import Image
import tempfile
import os
import platform
import subprocess
from tkinter import filedialog
import datetime
from decimal import Decimal

from addition_classes import resource_path, recolor_icon
from db_management import session, TransactionsTable, TransfersTable, AccountsTable, CategoriesTable
from CustomTkinterMessagebox import CTkMessagebox


class CategorySelectionWindow(ctk.CTkToplevel):
    """Отдельное окно для выбора категории"""
    def __init__(self, master, transaction_type, callback, **kwargs):
        super().__init__(master, **kwargs)
        
        self.transaction_type = transaction_type
        self.callback = callback
        self.selected_category = None
        self.master_window = master
        
        self.geometry("600x550+500+200")
        self.title("Выбор категории")
        self.resizable(False, False)
        self.configure(fg_color="#aba6a6")
        
        self.transient(master)
        self.grab_set()
        
        self._create_widgets()
        self._load_categories()
        
        self.protocol("WM_DELETE_WINDOW", self.safe_destroy)
    
    def _create_widgets(self):
        """Создает виджеты окна выбора категории"""
        
        title_label = ctk.CTkLabel(
            self,
            text="Выберите категорию",
            font=("Arial", 20, "bold"),
            text_color="black"
        )
        title_label.pack(pady=(15, 10))
        
        self.categories_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#3a3a3a",
            corner_radius=12
        )
        self.categories_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.categories_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="cat_col")
        
        self.category_buttons = []
        
        cancel_button = ctk.CTkButton(
            self,
            text="❌ Отмена",
            command=self.safe_destroy,
            font=("Arial", 14, "bold"),
            height=42,
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            corner_radius=10
        )
        cancel_button.pack(pady=(5, 15), padx=15, fill="x")
    
    def _wrap_text(self, text, max_length=12):
        """Разбивает текст на строки"""
        if len(text) <= max_length:
            return text
        
        words = text.split()
        if len(words) > 1:
            mid = len(words) // 2
            return "\n".join([" ".join(words[:mid]), " ".join(words[mid:])])
        else:
            mid = len(text) // 2
            return text[:mid] + "\n" + text[mid:]
    
    def _load_categories(self):
        """Загружает категории из БД"""
        categories = session.query(CategoriesTable).filter_by(
            transaction_type=self.transaction_type
        ).order_by(CategoriesTable.category_name).all()
        
        if not categories:
            empty_label = ctk.CTkLabel(
                self.categories_frame,
                text="Нет категорий",
                font=("Arial", 14),
                text_color="gray"
            )
            empty_label.grid(row=0, column=0, padx=20, pady=20)
            return
        
        columns = 4
        for i, cat in enumerate(categories):
            col = i % columns
            row = i // columns
            
            cat_name_display = self._wrap_text(cat.category_name, 12)
            
            btn_frame = ctk.CTkFrame(self.categories_frame, fg_color="transparent", corner_radius=10)
            btn_frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            
            try:
                icon_image = ctk.CTkImage(
                    light_image=recolor_icon(resource_path(f"assets/{cat.icon_url}"), cat.colour),
                    size=(55, 55)
                )
                icon_label = ctk.CTkLabel(btn_frame, image=icon_image, text="")
                icon_label.image = icon_image
                icon_label.pack(pady=(10, 5))
            except:
                icon_label = ctk.CTkLabel(btn_frame, text="📁", font=("Arial", 40))
                icon_label.pack(pady=(10, 5))
            
            text_label = ctk.CTkLabel(
                btn_frame,
                text=cat_name_display,
                font=("Arial", 12, "bold"),
                text_color="white",
                wraplength=100,
                justify="center"
            )
            text_label.pack(pady=(0, 10))
            
            btn_frame.bind("<Button-1>", lambda e, c=cat, f=btn_frame: self._select_category(c, f))
            icon_label.bind("<Button-1>", lambda e, c=cat, f=btn_frame: self._select_category(c, f))
            text_label.bind("<Button-1>", lambda e, c=cat, f=btn_frame: self._select_category(c, f))
            
            btn_frame.bind("<Enter>", lambda e, f=btn_frame: f.configure(fg_color="#5a5a5a"))
            btn_frame.bind("<Leave>", lambda e, f=btn_frame: f.configure(fg_color="transparent"))
            
            self.category_buttons.append({
                "frame": btn_frame,
                "category": cat
            })
    
    def _select_category(self, category, selected_frame):
        """Выбирает категорию и возвращает в основное окно"""
        for btn_data in self.category_buttons:
            if btn_data["category"] == category:
                btn_data["frame"].configure(fg_color="#4CAF50")
                self.selected_category = category
            else:
                btn_data["frame"].configure(fg_color="transparent")
        
        if self.callback:
            self.callback(category)
        
        self.after(200, self.safe_destroy)
    
    def safe_destroy(self):
        """Безопасное закрытие окна"""
        try:
            self.grab_release()
            if self.winfo_exists():
                self.destroy()
        except:
            pass


class EditTransactionWindow(ctk.CTkToplevel):
    """Окно редактирования транзакции"""
    def __init__(self, master, transaction, app_instance, **kwargs):
        super().__init__(master, **kwargs)
        
        self.transaction = transaction
        self.app_instance = app_instance
        self.master_ref = master
        self._destroying = False
        self.selected_category = None
        
        self.geometry("600x750+400+100")
        self.title("Редактирование транзакции")
        self.resizable(False, False)
        self.configure(fg_color="#aba6a6")
        
        self.transient(master)
        self.grab_set()
        self.focus_force()
        
        self._disable_parent_scroll()
        
        self._create_widgets()
        self._load_transaction_data()
        
        self.protocol("WM_DELETE_WINDOW", self.safe_destroy)
    
    def _disable_parent_scroll(self):
        """Отключает скроллер родительского окна"""
        try:
            current = self.master_ref
            while current:
                if hasattr(current, 'disable_all_scroll'):
                    current.disable_all_scroll()
                    break
                current = current.master
        except Exception as e:
            print(f"Ошибка отключения скроллера: {e}")
    
    def _enable_parent_scroll(self):
        """Включает скроллер родительского окна"""
        try:
            current = self.master_ref
            while current:
                if hasattr(current, 'enable_all_scroll'):
                    current.enable_all_scroll()
                    break
                current = current.master
        except Exception as e:
            print(f"Ошибка включения скроллера: {e}")
    
    def _create_widgets(self):
        """Создает виджеты окна редактирования"""
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        main_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Тип транзакции
        type_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        type_container.pack(fill="x", pady=(0, 15))
        
        self.type_label = ctk.CTkLabel(
            type_container, 
            text="Тип транзакции", 
            font=("Arial", 18, "bold"),
            text_color="black"
        )
        self.type_label.pack(anchor="w", pady=(0, 8))
        
        type_buttons_frame = ctk.CTkFrame(type_container, fg_color="transparent")
        type_buttons_frame.pack(fill="x")
        
        self.income_button = ctk.CTkButton(
            type_buttons_frame,
            text="💰 Доход",
            font=("Arial", 15, "bold"),
            command=lambda: self._change_type("Доход"),
            fg_color="#4CAF50" if self.transaction.transaction_type == "Доход" else "#d9d9d9",
            hover_color="#45a049",
            text_color="black",
            width=150,
            height=45,
            corner_radius=10
        )
        self.income_button.pack(side="left", padx=(0, 12))
        
        self.expense_button = ctk.CTkButton(
            type_buttons_frame,
            text="💸 Расход",
            font=("Arial", 15, "bold"),
            command=lambda: self._change_type("Расход"),
            fg_color="#FF6B6B" if self.transaction.transaction_type == "Расход" else "#d9d9d9",
            hover_color="#FF5252",
            text_color="black",
            width=150,
            height=45,
            corner_radius=10
        )
        self.expense_button.pack(side="left")
        
        # Счет
        account_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        account_container.pack(fill="x", pady=(0, 15))
        
        self.account_label = ctk.CTkLabel(
            account_container, 
            text="Счет", 
            font=("Arial", 18, "bold"),
            text_color="black"
        )
        self.account_label.pack(anchor="w", pady=(0, 8))
        
        accounts = session.query(AccountsTable).all()
        account_names = [acc.description for acc in accounts]
        
        self.account_menu = ctk.CTkOptionMenu(
            account_container,
            values=account_names,
            font=("Arial", 14),
            fg_color="#d9d9d9",
            button_color="#8a8585",
            text_color="black",
            width=350,
            height=45,
            corner_radius=10
        )
        self.account_menu.pack(anchor="w")
        
        # Категория
        category_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        category_container.pack(fill="x", pady=(0, 15))
        
        self.category_label = ctk.CTkLabel(
            category_container, 
            text="Категория", 
            font=("Arial", 18, "bold"),
            text_color="black"
        )
        self.category_label.pack(anchor="w", pady=(0, 8))
        
        self.selected_category_frame = ctk.CTkFrame(
            category_container,
            fg_color="#d9d9d9",
            corner_radius=10,
            height=70
        )
        self.selected_category_frame.pack(fill="x", pady=(0, 10))
        self.selected_category_frame.pack_propagate(False)
        
        cat_content_frame = ctk.CTkFrame(self.selected_category_frame, fg_color="transparent")
        cat_content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.category_icon_label = ctk.CTkLabel(
            cat_content_frame,
            text="❓",
            font=("Arial", 32),
            width=50
        )
        self.category_icon_label.pack(side="left", padx=(0, 15))
        
        self.selected_category_label = ctk.CTkLabel(
            cat_content_frame,
            text="Не выбрана",
            font=("Arial", 16),
            text_color="gray"
        )
        self.selected_category_label.pack(side="left", expand=True, fill="x")
        
        self.select_category_button = ctk.CTkButton(
            category_container,
            text="📁 Выбрать категорию",
            command=self._open_category_window,
            font=("Arial", 14, "bold"),
            height=45,
            fg_color="#4CAF50",
            hover_color="#45a049",
            corner_radius=10
        )
        self.select_category_button.pack(fill="x", pady=(0, 5))
        
        # Сумма
        amount_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        amount_container.pack(fill="x", pady=(0, 15))
        
        self.amount_label = ctk.CTkLabel(
            amount_container, 
            text="Сумма", 
            font=("Arial", 18, "bold"),
            text_color="black"
        )
        self.amount_label.pack(anchor="w", pady=(0, 8))
        
        self.amount_entry = ctk.CTkEntry(
            amount_container,
            placeholder_text="0.00",
            placeholder_text_color="gray",
            text_color="white",
            font=("Arial", 18),
            height=50,
            width=350,
            corner_radius=10
        )
        self.amount_entry.pack(anchor="w")
        
        # Время (дата не редактируется, только время)
        datetime_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        datetime_container.pack(fill="x", pady=(0, 15))
        
        # Показываем дату как статический текст
        self.date_label = ctk.CTkLabel(
            datetime_container,
            text=f"Дата: {self.transaction.transaction_date_time.strftime('%d.%m.%Y')}",
            font=("Arial", 16, "bold"),
            text_color="black"
        )
        self.date_label.pack(anchor="w", pady=(0, 10))
        
        self.time_label = ctk.CTkLabel(
            datetime_container, 
            text="Время", 
            font=("Arial", 18, "bold"),
            text_color="black"
        )
        self.time_label.pack(anchor="w", pady=(0, 8))
        
        time_frame = ctk.CTkFrame(datetime_container, fg_color="transparent")
        time_frame.pack(fill="x")
        
        self.hour_label = ctk.CTkLabel(time_frame, text_color="black", text="Часы", font=("Arial", 12))
        self.hour_label.grid(row=0, column=0, sticky="w", padx=5, pady=0)
        
        self.minute_label = ctk.CTkLabel(time_frame, text_color="black", text="Минуты", font=("Arial", 12))
        self.minute_label.grid(row=0, column=1, sticky="w", padx=5, pady=0)
        
        self.second_label = ctk.CTkLabel(time_frame, text_color="black", text="Секунды", font=("Arial", 12))
        self.second_label.grid(row=0, column=2, sticky="w", padx=5, pady=0)
        
        self.hour_entry = ctk.CTkEntry(time_frame, width=80, 
                                       placeholder_text="00", 
                                       placeholder_text_color="gray", 
                                       font=("Arial", 14), 
                                       height=40,
                                       text_color="gray")
        self.hour_entry.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.minute_entry = ctk.CTkEntry(time_frame, width=80, 
                                         placeholder_text="00", 
                                         placeholder_text_color="gray", 
                                         font=("Arial", 14), 
                                         height=40,
                                         text_color="gray")
        self.minute_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        self.second_entry = ctk.CTkEntry(time_frame, width=80, 
                                         placeholder_text="00", 
                                         placeholder_text_color="gray", 
                                         font=("Arial", 14), 
                                         height=40,
                                         text_color="gray")
        self.second_entry.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        self.hour_entry.bind("<FocusIn>", lambda e: self._on_time_entry_focus(e, self.hour_entry))
        self.hour_entry.bind("<FocusOut>", lambda e: self._on_time_entry_focus_out(e, self.hour_entry))
        self.minute_entry.bind("<FocusIn>", lambda e: self._on_time_entry_focus(e, self.minute_entry))
        self.minute_entry.bind("<FocusOut>", lambda e: self._on_time_entry_focus_out(e, self.minute_entry))
        self.second_entry.bind("<FocusIn>", lambda e: self._on_time_entry_focus(e, self.second_entry))
        self.second_entry.bind("<FocusOut>", lambda e: self._on_time_entry_focus_out(e, self.second_entry))
        
        # Комментарий
        comment_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        comment_container.pack(fill="x", pady=(0, 20))
        
        self.comment_label = ctk.CTkLabel(
            comment_container, 
            text="Комментарий", 
            font=("Arial", 18, "bold"),
            text_color="black"
        )
        self.comment_label.pack(anchor="w", pady=(0, 8))
        
        self.comment_entry = ctk.CTkTextbox(
            comment_container,
            font=("Arial", 14),
            height=100,
            width=480,
            corner_radius=10,
            border_width=2,
            border_color="#8a8585"
        )
        self.comment_entry.pack(anchor="w")
        
        # Кнопки
        buttons_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_container.pack(fill="x", pady=(20, 10))
        
        self.save_button = ctk.CTkButton(
            buttons_container,
            text="✅ Сохранить изменения",
            command=self.save_transaction,
            font=("Arial", 16, "bold"),
            height=52,
            fg_color="#4CAF50",
            hover_color="#45a049",
            corner_radius=12
        )
        self.save_button.pack(side="left", padx=(0, 12), fill="x", expand=True)
        
        self.cancel_button = ctk.CTkButton(
            buttons_container,
            text="❌ Отмена",
            command=self.safe_destroy,
            font=("Arial", 16, "bold"),
            height=52,
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            corner_radius=12
        )
        self.cancel_button.pack(side="left", fill="x", expand=True)
    
    def _on_time_entry_focus(self, event, entry):
        """При фокусе на поле времени - меняем цвет текста на белый"""
        entry.configure(text_color="white")
    
    def _on_time_entry_focus_out(self, event, entry):
        """При потере фокуса - если поле пустое, ставим серый цвет"""
        if entry.get().strip() == "":
            entry.configure(text_color="gray")
        else:
            entry.configure(text_color="white")
    
    def _open_category_window(self):
        """Открывает окно выбора категории"""
        transaction_type = self.transaction.transaction_type
        category_window = CategorySelectionWindow(
            master=self,
            transaction_type=transaction_type,
            callback=self._on_category_selected
        )
        category_window.attributes('-topmost', True)
        category_window.deiconify()
    
    def _on_category_selected(self, category):
        """Обработчик выбора категории"""
        self.selected_category = category
        
        cat_name = category.category_name
        cat_color = category.colour
        
        self.selected_category_label.configure(
            text=cat_name,
            text_color=cat_color,
            font=("Arial", 18, "bold")
        )
        self.selected_category_frame.configure(fg_color="#e8f5e9")
        
        try:
            icon_image = ctk.CTkImage(
                light_image=recolor_icon(resource_path(f"assets/{category.icon_url}"), cat_color),
                size=(45, 45)
            )
            self.category_icon_label.configure(image=icon_image, text="")
            self.category_icon_label.image = icon_image
        except:
            self.category_icon_label.configure(text="📁", font=("Arial", 32))
    
    def _load_transaction_data(self):
        """Загружает данные транзакции в поля"""
        if self.transaction.account:
            self.account_menu.set(self.transaction.account.description)
        
        if self.transaction.category:
            self.selected_category = self.transaction.category
            self.selected_category_label.configure(
                text=self.transaction.category.category_name,
                text_color=self.transaction.category.colour,
                font=("Arial", 18, "bold")
            )
            self.selected_category_frame.configure(fg_color="#e8f5e9")
            
            try:
                icon_image = ctk.CTkImage(
                    light_image=recolor_icon(resource_path(f"assets/{self.transaction.category.icon_url}"), self.transaction.category.colour),
                    size=(45, 45)
                )
                self.category_icon_label.configure(image=icon_image, text="")
                self.category_icon_label.image = icon_image
            except:
                self.category_icon_label.configure(text="📁", font=("Arial", 32))
        
        # Загружаем сумму
        self.amount_entry.insert(0, f"{self.transaction.amount:,.2f}")
        
        # Загружаем время
        hour_val = self.transaction.transaction_date_time.strftime("%H")
        minute_val = self.transaction.transaction_date_time.strftime("%M")
        second_val = self.transaction.transaction_date_time.strftime("%S")
        
        self.hour_entry.delete(0, "end")
        self.hour_entry.insert(0, hour_val)
        
        self.minute_entry.delete(0, "end")
        self.minute_entry.insert(0, minute_val)
        
        self.second_entry.delete(0, "end")
        self.second_entry.insert(0, second_val)
        
        self.hour_entry.configure(text_color="gray")
        self.minute_entry.configure(text_color="gray")
        self.second_entry.configure(text_color="gray")
        
        # Загружаем комментарий
        if self.transaction.description:
            self.comment_entry.insert("1.0", self.transaction.description)
    
    def _change_type(self, new_type):
        """Изменяет тип транзакции"""
        if new_type == self.transaction.transaction_type:
            return
        
        self.transaction.transaction_type = new_type
        
        if new_type == "Доход":
            self.income_button.configure(fg_color="#4CAF50")
            self.expense_button.configure(fg_color="#d9d9d9")
        else:
            self.income_button.configure(fg_color="#d9d9d9")
            self.expense_button.configure(fg_color="#FF6B6B")
        
        self.selected_category = None
        self.selected_category_label.configure(
            text="Не выбрана",
            text_color="gray",
            font=("Arial", 16)
        )
        self.selected_category_frame.configure(fg_color="#d9d9d9")
        self.category_icon_label.configure(text="❓", font=("Arial", 32))
    
    def save_transaction(self):
        """Сохраняет изменения транзакции"""
        if self._destroying:
            return
        
        try:
            account_name = self.account_menu.get()
            if not account_name:
                CTkMessagebox.messagebox(title="Ошибка!", text="Выберите счет!")
                return
            
            account = session.query(AccountsTable).filter_by(description=account_name).first()
            if not account:
                CTkMessagebox.messagebox(title="Ошибка!", text="Счет не найден!")
                return
            
            if self.transaction.transaction_type == "Расход" and not self.selected_category:
                CTkMessagebox.messagebox(title="Ошибка!", text="Выберите категорию расхода!")
                return
            
            amount_str = self.amount_entry.get().strip().replace(',', '.')
            if not amount_str:
                CTkMessagebox.messagebox(title="Ошибка!", text="Введите сумму!")
                return
            
            try:
                new_amount = float(amount_str)
                if new_amount <= 0:
                    CTkMessagebox.messagebox(title="Ошибка!", text="Сумма должна быть больше нуля!")
                    return
            except ValueError:
                CTkMessagebox.messagebox(title="Ошибка!", text="Некорректный формат суммы!")
                return
            
            # Дата остается старой, меняем только время
            date = self.transaction.transaction_date_time.date()
            
            # Получаем время из полей
            hours_str = self.hour_entry.get()
            minutes_str = self.minute_entry.get()
            seconds_str = self.second_entry.get()
            
            if not hours_str and not minutes_str and not seconds_str:
                hours = self.transaction.transaction_date_time.hour
                minutes = self.transaction.transaction_date_time.minute
                seconds = self.transaction.transaction_date_time.second
            else:
                hours = int(hours_str) if hours_str else 0
                minutes = int(minutes_str) if minutes_str else 0
                seconds = int(seconds_str) if seconds_str else 0
                
                if not 0 <= hours < 24 or not 0 <= minutes < 60 or not 0 <= seconds < 60:
                    CTkMessagebox.messagebox(title="Ошибка!", text="Неверное время!")
                    return
            
            new_datetime = datetime.datetime.combine(date, datetime.time(hours, minutes, seconds))
            description = self.comment_entry.get("1.0", "end-1c").strip()
            
            # Восстанавливаем старый баланс счета
            old_account = self.transaction.account
            old_amount = self.transaction.amount
            old_type = self.transaction.transaction_type
            
            if old_type == "Расход":
                old_account.amount += old_amount
            else:
                old_account.amount -= old_amount
            
            # Применяем новую транзакцию
            if self.transaction.transaction_type == "Расход":
                if account.amount < new_amount:
                    CTkMessagebox.messagebox(title="Ошибка!", text=f"Недостаточно средств на счёте {account_name}!")
                    # Восстанавливаем старый баланс
                    if old_type == "Расход":
                        old_account.amount -= old_amount
                    else:
                        old_account.amount += old_amount
                    return
                account.amount -= new_amount
            else:
                account.amount += new_amount
            
            # Обновляем транзакцию
            self.transaction.account_id = account.account_id
            self.transaction.category_id = self.selected_category.category_id if self.selected_category else None
            self.transaction.amount = new_amount
            self.transaction.transaction_date_time = new_datetime
            self.transaction.description = description if description else None
            
            session.commit()
            
            CTkMessagebox.messagebox(title="Успех!", text="Транзакция успешно обновлена!")
            
            if self.app_instance and hasattr(self.app_instance, 'force_update_all'):
                self.app_instance.force_update_all()
            
            self.safe_destroy()
            
        except Exception as e:
            session.rollback()
            CTkMessagebox.messagebox(title="Ошибка!", text=f"Не удалось обновить транзакцию: {str(e)}")
    
    def safe_destroy(self):
        """Безопасное закрытие окна"""
        if self._destroying:
            return
        self._destroying = True
        try:
            self._enable_parent_scroll()
            self.grab_release()
            if self.winfo_exists():
                self.destroy()
        except Exception as e:
            print(f"Ошибка при закрытии окна редактирования: {e}")
            self._enable_parent_scroll()


class TransactionActions:
    """Класс для управления действиями с транзакциями"""
    
    def __init__(self, parent_frame, master_ref=None):
        self.parent_frame = parent_frame
        self.master_ref = master_ref
    
    def show_receipt(self, transaction_id):
        transaction = session.query(TransactionsTable).filter_by(transaction_id=transaction_id).first()
        
        if transaction and transaction.check_photo:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(transaction.check_photo)
                    temp_path = temp_file.name
                
                if platform.system() == 'Darwin':
                    subprocess.call(('open', temp_path))
                elif platform.system() == 'Windows':
                    os.startfile(temp_path)
                else:
                    subprocess.call(('xdg-open', temp_path))
                    
            except Exception as e:
                CTkMessagebox.messagebox(title="Ошибка!", text=f"Не удалось открыть чек: {str(e)}")
        else:
            CTkMessagebox.messagebox(title="Информация", text="Чек не найден")
    
    def add_receipt(self, transaction_id):
        transaction = session.query(TransactionsTable).filter_by(transaction_id=transaction_id).first()
        
        if not transaction:
            CTkMessagebox.messagebox(title="Ошибка!", text="Транзакция не найдена")
            return
        
        file_path = filedialog.askopenfilename(
            title="Выберите файл чека",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'rb') as file:
                    check_photo_data = file.read()
                
                transaction.check_photo = check_photo_data
                session.commit()
                
                CTkMessagebox.messagebox(title="Успех!", text="Чек успешно добавлен!")
                
                if hasattr(self.parent_frame, 'update_frame'):
                    self.parent_frame.update_frame()
                
            except Exception as e:
                CTkMessagebox.messagebox(title="Ошибка!", text=f"Не удалось загрузить файл: {str(e)}")
    
    def edit_transaction(self, transaction):
        app_instance = None
        current = self.parent_frame
        while current:
            if hasattr(current, 'app_instance'):
                app_instance = current.app_instance
                break
            current = current.master
        
        edit_window = EditTransactionWindow(
            master=self.parent_frame,
            transaction=transaction,
            app_instance=app_instance
        )
        edit_window.attributes('-topmost', True)
        edit_window.deiconify()
        edit_window.focus()
    
    def delete_transaction(self, transaction):
        confirm_window = ctk.CTkToplevel(self.parent_frame)
        confirm_window.title("Подтверждение удаления")
        confirm_window.geometry("450x400")
        confirm_window.resizable(False, False)
        confirm_window.transient(self.parent_frame)
        confirm_window.grab_set()
        
        confirm_window.grid_columnconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(1, weight=0)
        
        main_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        icon_label = ctk.CTkLabel(main_frame, text="⚠️", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 15))
        
        confirm_text = ctk.CTkLabel(
            main_frame,
            text=f"Вы уверены, что хотите удалить транзакцию?\n\n"
                 f"Сумма: {transaction.amount:,.2f}\n"
                 f"Дата: {transaction.transaction_date_time.strftime('%d.%m.%Y %H:%M:%S')}",
            font=("Arial", 13),
            justify="center"
        )
        confirm_text.grid(row=1, column=0, pady=10)
        
        warning_label = ctk.CTkLabel(
            main_frame,
            text="Это действие нельзя отменить!",
            font=("Arial", 12),
            text_color="#FF6B6B",
            justify="center"
        )
        warning_label.grid(row=2, column=0, pady=10)
        
        buttons_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        buttons_frame.grid(row=1, column=0, pady=20)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        result = [False]
        
        def on_yes():
            result[0] = True
            confirm_window.destroy()
        
        def on_no():
            result[0] = False
            confirm_window.destroy()
        
        yes_button = ctk.CTkButton(
            buttons_frame,
            text="Да, удалить",
            command=on_yes,
            font=("Arial", 13, "bold"),
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            width=120,
            height=38
        )
        yes_button.grid(row=0, column=0, padx=10)
        
        no_button = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            command=on_no,
            font=("Arial", 13, "bold"),
            width=120,
            height=38
        )
        no_button.grid(row=0, column=1, padx=10)
        
        confirm_window.wait_window()
        
        if result[0]:
            try:
                account = transaction.account
                if transaction.transaction_type == "Расход":
                    account.amount += transaction.amount
                else:
                    account.amount -= transaction.amount
                
                session.delete(transaction)
                session.commit()
                
                CTkMessagebox.messagebox(title="Успех!", text="Транзакция успешно удалена!")
                
                app_instance = None
                current = self.parent_frame
                while current:
                    if hasattr(current, 'app_instance'):
                        app_instance = current.app_instance
                        break
                    current = current.master
                
                if app_instance and hasattr(app_instance, 'force_update_all'):
                    app_instance.force_update_all()
                
                if hasattr(self.parent_frame, 'update_frame'):
                    self.parent_frame.update_frame()
                
            except Exception as e:
                session.rollback()
                CTkMessagebox.messagebox(title="Ошибка!", text=f"Не удалось удалить транзакцию: {str(e)}")


def create_action_buttons(parent, transaction, actions):
    """Создает кнопки действий для транзакции"""
    actions_frame = ctk.CTkFrame(parent, fg_color="transparent")
    
    try:
        edit_icon = ctk.CTkImage(
            light_image=Image.open(resource_path("assets/icons/edit.png")),
            size=(24, 24)
        )
        edit_button = ctk.CTkButton(
            actions_frame,
            text="",
            image=edit_icon,
            width=38,
            height=38,
            fg_color="#4CAF50",
            hover_color="#45a049",
            corner_radius=6,
            command=lambda tr=transaction: actions.edit_transaction(tr)
        )
        edit_button.pack(side="left", padx=2)
    except:
        edit_button = ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=38,
            height=38,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=("Arial", 18),
            corner_radius=6,
            command=lambda tr=transaction: actions.edit_transaction(tr)
        )
        edit_button.pack(side="left", padx=2)
    
    try:
        delete_icon = ctk.CTkImage(
            light_image=Image.open(resource_path("assets/icons/delete.png")),
            size=(24, 24)
        )
        delete_button = ctk.CTkButton(
            actions_frame,
            text="",
            image=delete_icon,
            width=38,
            height=38,
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            corner_radius=6,
            command=lambda tr=transaction: actions.delete_transaction(tr)
        )
        delete_button.pack(side="left", padx=2)
    except:
        delete_button = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=38,
            height=38,
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            font=("Arial", 18),
            corner_radius=6,
            command=lambda tr=transaction: actions.delete_transaction(tr)
        )
        delete_button.pack(side="left", padx=2)
    
    return actions_frame