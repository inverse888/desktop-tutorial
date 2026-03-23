import customtkinter as ctk
from PIL import Image
import tempfile
import os
import platform
import subprocess
from tkinter import filedialog

from addition_classes import resource_path
from db_management import session, TransactionsTable, TransfersTable, AccountsTable
from CustomTkinterMessagebox import CTkMessagebox


class FilterPanel(ctk.CTkFrame):
    """Панель фильтрации транзакций по счетам"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#949191")
        
        filter_label = ctk.CTkLabel(
            self, 
            text="Фильтр по счету:", 
            text_color="black",
            font=("Arial", 14, "bold")
        )
        filter_label.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        
        self.account_filter = ctk.CTkOptionMenu(
            self,
            values=["Загрузка..."],
            command=self.on_filter_change,
            text_color="black",
            fg_color="#d9d9d9",
            button_color="#8a8585",
            width=200,
            height=35
        )
        self.account_filter.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        self.reset_button = ctk.CTkButton(
            self,
            text="Сбросить",
            command=self.reset_filter,
            text_color="black",
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            width=100,
            height=35
        )
        self.reset_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        
        # Загружаем список счетов
        self.update_accounts_list()
    
    def update_accounts_list(self):
        """Обновляет список счетов в выпадающем меню"""
        accounts_list = ["Все счета"]
        accounts = session.query(AccountsTable).order_by(AccountsTable.description).all()
        accounts_list.extend([acc.description for acc in accounts])
        
        current_value = self.account_filter.get()
        self.account_filter.configure(values=accounts_list)
        
        # Если текущее значение еще существует в новом списке, оставляем его
        if current_value in accounts_list:
            self.account_filter.set(current_value)
        else:
            self.account_filter.set("Все счета")
    
    def on_filter_change(self, selected_account):
        if selected_account == "Все счета":
            self.master.filter_by_account(None)
        else:
            self.master.filter_by_account(selected_account)
    
    def reset_filter(self):
        self.account_filter.set("Все счета")
        self.master.filter_by_account(None)


class TransactionsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        
        self.grid_columnconfigure(0, weight=0, minsize=60)
        self.grid_columnconfigure(1, weight=0, minsize=80)
        self.grid_columnconfigure(2, weight=0, minsize=80)
        self.grid_columnconfigure(3, weight=2, minsize=150)
        self.grid_columnconfigure(4, weight=1, minsize=110)
        self.grid_columnconfigure(5, weight=3, minsize=220)
        self.grid_columnconfigure(6, weight=0, minsize=80)

        self.update_frame()

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
                self.update_frame()
                
            except Exception as e:
                CTkMessagebox.messagebox(title="Ошибка!", text=f"Не удалось загрузить файл: {str(e)}")
        else:
            CTkMessagebox.messagebox(title="Информация", text="Добавление чека отменено")

    def update_frame(self, filter_account=None):
        """Обновляет таблицу транзакций с возможностью фильтрации по счету"""
        for widget in self.winfo_children():
            widget.destroy()

        headers = ["Счёт", "Дата", "Время", "Категория", "Сумма", "Комментарий", "Чек"]
        header_alignments = ["center", "center", "center", "w", "e", "w", "center"]
        
        for col, (name, align) in enumerate(zip(headers, header_alignments)):
            label = ctk.CTkLabel(
                self, 
                text=name, 
                text_color="black",
                font=("Arial", 14, "bold"),
                anchor=align
            )
            label.grid(row=0, column=col, sticky="ew", padx=5, pady=10)

        # Получаем транзакции с фильтром
        query = session.query(TransactionsTable).order_by(
            TransactionsTable.transaction_date_time.desc()
        )
        
        if filter_account:
            account = session.query(AccountsTable).filter_by(
                description=filter_account
            ).first()
            if account:
                query = query.filter(TransactionsTable.account_id == account.account_id)
        
        transactions = query.all()
        
        if not transactions:
            empty_text = "Нет транзакций"
            if filter_account:
                empty_text += f" для счета '{filter_account}'"
            empty_label = ctk.CTkLabel(
                self, 
                text=empty_text, 
                font=("Arial", 16), 
                text_color="gray"
            )
            empty_label.grid(row=1, column=0, columnspan=7, padx=20, pady=30)
            return

        for i, t in enumerate(transactions):
            row = i + 1
            
            try:
                icon_path = resource_path(f"assets/{t.account.icon_url}")
                if os.path.exists(icon_path):
                    icon_image = Image.open(icon_path)
                    account_label = ctk.CTkLabel(
                        self, 
                        image=ctk.CTkImage(light_image=icon_image, size=(30, 30)),
                        text="",
                        width=40
                    )
                else:
                    account_label = ctk.CTkLabel(self, text="💰", font=("Arial", 20))
            except:
                account_label = ctk.CTkLabel(self, text="💰", font=("Arial", 20))
            account_label.grid(row=row, column=0, padx=5, pady=10)
            
            date_label = ctk.CTkLabel(
                self, 
                text=t.transaction_date_time.strftime("%d.%m.%y"), 
                text_color="black", 
                font=("Arial", 13)
            )
            date_label.grid(row=row, column=1, padx=5, pady=10, sticky="ew")
            
            time_label = ctk.CTkLabel(
                self, 
                text=t.transaction_date_time.strftime("%H:%M:%S"), 
                text_color="black", 
                font=("Arial", 13)
            )
            time_label.grid(row=row, column=2, padx=5, pady=10, sticky="ew")
            
            cat_color = t.category.colour if t.category else "#808080"
            cat_name = t.category.category_name if t.category else "Без категории"
            category_label = ctk.CTkLabel(
                self, 
                text=cat_name, 
                text_color=cat_color, 
                font=("Arial", 13, "bold"),
                wraplength=140,
                justify="left"
            )
            category_label.grid(row=row, column=3, padx=5, pady=10, sticky="w")
            
            amount_color = "red" if t.transaction_type == "Расход" else "green"
            amount_label = ctk.CTkLabel(
                self, 
                text=f"{t.amount:,.2f}", 
                text_color=amount_color, 
                font=("Arial", 13, "bold")
            )
            amount_label.grid(row=row, column=4, padx=5, pady=10, sticky="e")
            
            comment_text = t.description if t.description else "—"
            
            if len(comment_text) > 25 and '\n' not in comment_text:
                words = comment_text.split()
                lines = []
                current_line = ""
                
                for word in words:
                    if len(current_line + " " + word) <= 25:
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                comment_text = "\n".join(lines)
            
            comment_label = ctk.CTkLabel(
                self, 
                text=comment_text, 
                text_color="black", 
                font=("Arial", 13),
                wraplength=200,
                justify="left",
                anchor="nw"
            )
            comment_label.grid(row=row, column=5, padx=5, pady=10, sticky="w")
            
            if t.check_photo:
                try:
                    receipt_icon = ctk.CTkImage(
                        light_image=Image.open(resource_path("assets/icons/receipt.png")), 
                        size=(30, 30)
                    )
                    receipt_button = ctk.CTkButton(
                        self, 
                        text="", 
                        image=receipt_icon,
                        width=45,
                        height=45,
                        fg_color="transparent",
                        hover_color="#d3d3d3",
                        command=lambda tid=t.transaction_id: self.show_receipt(tid)
                    )
                    receipt_button.grid(row=row, column=6, padx=5, pady=8)
                except:
                    receipt_label = ctk.CTkLabel(self, text="📄", font=("Arial", 24))
                    receipt_label.grid(row=row, column=6, padx=5, pady=10)
            else:
                try:
                    button_frame = ctk.CTkFrame(self, fg_color="transparent")
                    button_frame.grid(row=row, column=6, padx=5, pady=8)
                    
                    add_receipt_button = ctk.CTkButton(
                        button_frame,
                        text="+",
                        width=45,
                        height=45,
                        fg_color="#4CAF50",
                        hover_color="#45a049",
                        text_color="white",
                        font=("Arial", 20, "bold"),
                        command=lambda tid=t.transaction_id: self.add_receipt(tid)
                    )
                    add_receipt_button.pack(side="left", padx=2)
                    
                except Exception as e:
                    no_receipt_label = ctk.CTkLabel(
                        self, 
                        text="—", 
                        text_color="gray", 
                        font=("Arial", 18)
                    )
                    no_receipt_label.grid(row=row, column=6, padx=5, pady=10)


class TransfersFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        
        self.grid_columnconfigure(0, weight=0, minsize=50)
        self.grid_columnconfigure(1, weight=0, minsize=50)
        self.grid_columnconfigure(2, weight=0, minsize=80)
        self.grid_columnconfigure(3, weight=0, minsize=80)
        self.grid_columnconfigure(4, weight=1, minsize=110)
        self.grid_columnconfigure(5, weight=4, minsize=250)

        self.update_frame()

    def update_frame(self):
        for widget in self.winfo_children():
            widget.destroy()

        transfers = (
            session.query(TransfersTable)
            .order_by(TransfersTable.transfer_date_time.desc())
            .all()
        )
        
        headers = ["Со счёта", "На счёт", "Дата", "Время", "Сумма", "Комментарий"]
        header_alignments = ["center", "center", "center", "center", "e", "w"]
        
        for col, (name, align) in enumerate(zip(headers, header_alignments)):
            label = ctk.CTkLabel(
                self, 
                text=name, 
                text_color="black",
                font=("Arial", 14, "bold"),
                anchor=align
            )
            label.grid(row=0, column=col, sticky="ew", padx=5, pady=10)

        if not transfers:
            empty_label = ctk.CTkLabel(
                self, 
                text="Нет переводов", 
                font=("Arial", 16), 
                text_color="gray"
            )
            empty_label.grid(row=1, column=0, columnspan=6, padx=20, pady=30)
            return

        for i, t in enumerate(transfers):
            row = i + 1
            
            try:
                icon_from = Image.open(resource_path(f"assets/{t.from_account_ref.icon_url}"))
                from_label = ctk.CTkLabel(
                    self, 
                    image=ctk.CTkImage(light_image=icon_from, size=(30, 30)),
                    text="",
                    width=40
                )
            except:
                from_label = ctk.CTkLabel(self, text="⬆️", font=("Arial", 20))
            from_label.grid(row=row, column=0, padx=5, pady=10)
            
            try:
                icon_to = Image.open(resource_path(f"assets/{t.to_account_ref.icon_url}"))
                to_label = ctk.CTkLabel(
                    self, 
                    image=ctk.CTkImage(light_image=icon_to, size=(30, 30)),
                    text="",
                    width=40
                )
            except:
                to_label = ctk.CTkLabel(self, text="⬇️", font=("Arial", 20))
            to_label.grid(row=row, column=1, padx=5, pady=10)
            
            date_label = ctk.CTkLabel(
                self, 
                text=t.transfer_date_time.strftime("%d.%m.%y"), 
                text_color="black", 
                font=("Arial", 13)
            )
            date_label.grid(row=row, column=2, padx=5, pady=10, sticky="ew")
            
            time_label = ctk.CTkLabel(
                self, 
                text=t.transfer_date_time.strftime("%H:%M:%S"), 
                text_color="black", 
                font=("Arial", 13)
            )
            time_label.grid(row=row, column=3, padx=5, pady=10, sticky="ew")
            
            amount_label = ctk.CTkLabel(
                self, 
                text=f"{t.amount:,.2f}", 
                text_color="black", 
                font=("Arial", 13, "bold")
            )
            amount_label.grid(row=row, column=4, padx=5, pady=10, sticky="e")
            
            comment_text = t.description if t.description else "—"
            
            if len(comment_text) > 25 and '\n' not in comment_text:
                words = comment_text.split()
                lines = []
                current_line = ""
                
                for word in words:
                    if len(current_line + " " + word) <= 25:
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                comment_text = "\n".join(lines)
            
            comment_label = ctk.CTkLabel(
                self, 
                text=comment_text, 
                text_color="black", 
                font=("Arial", 13),
                wraplength=240,
                justify="left",
                anchor="nw"
            )
            comment_label.grid(row=row, column=5, padx=5, pady=10, sticky="w")


class TransactionsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Изменяем сетку - теперь 4 строки
        self.grid_rowconfigure(0, weight=0)  # Главный заголовок
        self.grid_rowconfigure(1, weight=0)  # Панель фильтрации
        self.grid_rowconfigure(2, weight=0)  # Заголовки таблиц
        self.grid_rowconfigure(3, weight=1)  # Таблицы
        self.grid_columnconfigure(0, weight=6)
        self.grid_columnconfigure(1, weight=4)

        self.main_label = ctk.CTkLabel(
            self, 
            text="Транзакции и переводы", 
            font=("Arial", 26, "bold"),
            text_color="white"
        )
        self.main_label.grid(row=0, column=0, columnspan=2, sticky="nw", padx=15, pady=(15, 5))

        # Панель фильтрации
        self.filter_panel = FilterPanel(self)
        self.filter_panel.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 10))

        self.transactions_header = ctk.CTkLabel(
            self, 
            text="📊 Транзакции", 
            font=("Arial", 18, "bold"),
            text_color="white",
            anchor="w"
        )
        self.transactions_header.grid(row=2, column=0, sticky="sw", padx=(15, 5), pady=(0, 5))
        
        self.transfers_header = ctk.CTkLabel(
            self, 
            text="🔄 Переводы", 
            font=("Arial", 18, "bold"),
            text_color="white",
            anchor="w"
        )
        self.transfers_header.grid(row=2, column=1, sticky="sw", padx=(5, 15), pady=(0, 5))

        self.transactions_frame = TransactionsFrame(self, corner_radius=10, height=550)
        self.transactions_frame.grid(row=3, column=0, padx=(15, 7), pady=(5, 15), sticky="nsew")

        self.transfers_frame = TransfersFrame(self, corner_radius=10, height=550)
        self.transfers_frame.grid(row=3, column=1, padx=(7, 15), pady=(5, 15), sticky="nsew")
        
        self.current_filter_account = None

    def filter_by_account(self, account_name):
        """Фильтрует транзакции по счету"""
        self.current_filter_account = account_name
        self.transactions_frame.update_frame(account_name)

    def update_transactions(self):
        """Обновляет список транзакций (с учетом фильтра)"""
        self.transactions_frame.update_frame(self.current_filter_account)

    def update_transfers(self):
        self.transfers_frame.update_frame()

    def update_categories(self):
        """Обновление категорий (для совместимости)"""
        pass
    
    def update_accounts_filter(self):
        """Обновляет список счетов в фильтре (вызывается после создания/удаления счета)"""
        if hasattr(self, 'filter_panel') and self.filter_panel:
            self.filter_panel.update_accounts_list()