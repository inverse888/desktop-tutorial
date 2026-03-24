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
from transactions_redactions import TransactionActions, create_action_buttons


class FilterPanel(ctk.CTkFrame):
    """Панель фильтрации транзакций по счетам"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#949191")
        
        filter_label = ctk.CTkLabel(
            self, 
            text="Фильтр по счету:", 
            text_color="black",
            font=("Arial", 16, "bold")
        )
        filter_label.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        
        self.account_filter = ctk.CTkOptionMenu(
            self,
            values=["Загрузка..."],
            command=self.on_filter_change,
            text_color="black",
            fg_color="#d9d9d9",
            button_color="#8a8585",
            width=220,
            height=40,
            font=("Arial", 14)
        )
        self.account_filter.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        self.reset_button = ctk.CTkButton(
            self,
            text="Сбросить",
            command=self.reset_filter,
            text_color="black",
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            width=120,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.reset_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        
        self.update_accounts_list()
    
    def update_accounts_list(self):
        accounts_list = ["Все счета"]
        accounts = session.query(AccountsTable).order_by(AccountsTable.description).all()
        accounts_list.extend([acc.description for acc in accounts])
        
        current_value = self.account_filter.get()
        self.account_filter.configure(values=accounts_list)
        
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
        
        # Колонки
        self.grid_columnconfigure(0, weight=0, minsize=55)   # Счёт
        self.grid_columnconfigure(1, weight=0, minsize=70)   # Дата
        self.grid_columnconfigure(2, weight=0, minsize=60)   # Время
        self.grid_columnconfigure(3, weight=0, minsize=130)  # Категория
        self.grid_columnconfigure(4, weight=0, minsize=100)  # Сумма
        self.grid_columnconfigure(5, weight=2, minsize=200)  # Комментарий
        self.grid_columnconfigure(6, weight=0, minsize=70)   # Чек
        self.grid_columnconfigure(7, weight=0, minsize=96)   # Действия

        self.actions = TransactionActions(self)
        
        # Сохраняем ссылку на canvas для управления прокруткой
        self._canvas = None
        if hasattr(self, '_parent_canvas'):
            self._canvas = self._parent_canvas
        
        self.update_frame()
    
    def disable_scroll(self):
        """Отключает прокрутку фрейма (вызывается при открытии окна редактирования)"""
        if self._canvas:
            self._canvas.unbind_all("<MouseWheel>")
            self._canvas.unbind_all("<Button-4>")
            self._canvas.unbind_all("<Button-5>")
    
    def enable_scroll(self):
        """Включает прокрутку фрейма (вызывается при закрытии окна редактирования)"""
        if self._canvas:
            def on_mousewheel(e):
                self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            self._canvas.bind_all("<MouseWheel>", on_mousewheel)
            self._canvas.bind_all("<Button-4>", lambda e: self._canvas.yview_scroll(-1, "units"))
            self._canvas.bind_all("<Button-5>", lambda e: self._canvas.yview_scroll(1, "units"))

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
        for widget in self.winfo_children():
            widget.destroy()

        headers = ["Счёт", "Дата", "Время", "Категория", "Сумма", "Комментарий", "Чек", "Действия"]
        header_alignments = ["center", "center", "center", "w", "e", "w", "center", "center"]
        
        for col, (name, align) in enumerate(zip(headers, header_alignments)):
            label = ctk.CTkLabel(
                self, 
                text=name, 
                text_color="black",
                font=("Arial", 14, "bold"),
                anchor=align
            )
            label.grid(row=0, column=col, sticky="ew", padx=2, pady=8)

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
            empty_label.grid(row=1, column=0, columnspan=8, padx=20, pady=30)
            return

        for i, t in enumerate(transactions):
            row = i + 1
            
            # Счет
            try:
                icon_path = resource_path(f"assets/{t.account.icon_url}")
                if os.path.exists(icon_path):
                    icon_image = Image.open(icon_path)
                    account_label = ctk.CTkLabel(
                        self, 
                        image=ctk.CTkImage(light_image=icon_image, size=(30, 30)),
                        text="",
                        width=38
                    )
                else:
                    account_label = ctk.CTkLabel(self, text="💰", font=("Arial", 18))
            except:
                account_label = ctk.CTkLabel(self, text="💰", font=("Arial", 18))
            account_label.grid(row=row, column=0, padx=2, pady=6)
            
            # Дата
            date_label = ctk.CTkLabel(
                self, 
                text=t.transaction_date_time.strftime("%d.%m.%y"), 
                text_color="black", 
                font=("Arial", 13)
            )
            date_label.grid(row=row, column=1, padx=2, pady=6, sticky="ew")
            
            # Время
            time_label = ctk.CTkLabel(
                self, 
                text=t.transaction_date_time.strftime("%H:%M"), 
                text_color="black", 
                font=("Arial", 13)
            )
            time_label.grid(row=row, column=2, padx=2, pady=6, sticky="ew")
            
            # Категория
            cat_color = t.category.colour if t.category else "#808080"
            cat_name = t.category.category_name if t.category else "Без категории"
            
            category_label = ctk.CTkLabel(
                self, 
                text=cat_name, 
                text_color=cat_color, 
                font=("Arial", 13, "bold"),
                wraplength=120,
                justify="left"
            )
            category_label.grid(row=row, column=3, padx=2, pady=6, sticky="w")
            
            # Сумма
            amount_color = "red" if t.transaction_type == "Расход" else "green"
            amount_label = ctk.CTkLabel(
                self, 
                text=f"{t.amount:,.2f}", 
                text_color=amount_color, 
                font=("Arial", 13, "bold")
            )
            amount_label.grid(row=row, column=4, padx=2, pady=6, sticky="e")
            
            # Комментарий
            comment_text = t.description if t.description else "—"
            comment_label = ctk.CTkLabel(
                self, 
                text=comment_text, 
                text_color="black", 
                font=("Arial", 13),
                wraplength=180,
                justify="left",
                anchor="w"
            )
            comment_label.grid(row=row, column=5, padx=2, pady=6, sticky="w")
            
            # Чек
            if t.check_photo:
                try:
                    receipt_img = Image.open(resource_path("assets/icons/receipt.png"))
                    receipt_icon = ctk.CTkImage(
                        light_image=receipt_img, 
                        size=(28, 28)
                    )
                    receipt_button = ctk.CTkButton(
                        self, 
                        text="", 
                        image=receipt_icon,
                        width=36,
                        height=36,
                        fg_color="transparent",
                        hover_color="#d3d3d3",
                        command=lambda tid=t.transaction_id: self.actions.show_receipt(tid)
                    )
                    receipt_button.grid(row=row, column=6, padx=2, pady=2)
                except:
                    receipt_button = ctk.CTkButton(
                        self, 
                        text="📄", 
                        width=36,
                        height=36,
                        fg_color="transparent",
                        hover_color="#d3d3d3",
                        font=("Arial", 18),
                        command=lambda tid=t.transaction_id: self.actions.show_receipt(tid)
                    )
                    receipt_button.grid(row=row, column=6, padx=2, pady=2)
            else:
                try:
                    add_receipt_button = ctk.CTkButton(
                        self,
                        text="+",
                        width=36,
                        height=36,
                        fg_color="#4CAF50",
                        hover_color="#45a049",
                        text_color="white",
                        font=("Arial", 20, "bold"),
                        command=lambda tid=t.transaction_id: self.actions.add_receipt(tid)
                    )
                    add_receipt_button.grid(row=row, column=6, padx=2, pady=2)
                except:
                    no_receipt_label = ctk.CTkLabel(
                        self, 
                        text="—", 
                        text_color="gray", 
                        font=("Arial", 16),
                        width=36,
                        height=36
                    )
                    no_receipt_label.grid(row=row, column=6, padx=2, pady=6)
            
            # Кнопки действий
            actions_frame = create_action_buttons(self, t, self.actions)
            actions_frame.grid(row=row, column=7, padx=2, pady=2)


class TransfersFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        
        self.grid_columnconfigure(0, weight=0, minsize=55)   # Со счёта
        self.grid_columnconfigure(1, weight=0, minsize=55)   # На счёт
        self.grid_columnconfigure(2, weight=0, minsize=80)   # Дата
        self.grid_columnconfigure(3, weight=0, minsize=80)   # Время
        self.grid_columnconfigure(4, weight=0, minsize=110)  # Сумма
        self.grid_columnconfigure(5, weight=3, minsize=350)  # Комментарий
        
        # Сохраняем ссылку на canvas для управления прокруткой
        self._canvas = None
        if hasattr(self, '_parent_canvas'):
            self._canvas = self._parent_canvas

        self.update_frame()
    
    def disable_scroll(self):
        """Отключает прокрутку фрейма"""
        if self._canvas:
            self._canvas.unbind_all("<MouseWheel>")
            self._canvas.unbind_all("<Button-4>")
            self._canvas.unbind_all("<Button-5>")
    
    def enable_scroll(self):
        """Включает прокрутку фрейма"""
        if self._canvas:
            def on_mousewheel(e):
                self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            self._canvas.bind_all("<MouseWheel>", on_mousewheel)
            self._canvas.bind_all("<Button-4>", lambda e: self._canvas.yview_scroll(-1, "units"))
            self._canvas.bind_all("<Button-5>", lambda e: self._canvas.yview_scroll(1, "units"))

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
            label.grid(row=0, column=col, sticky="ew", padx=2, pady=8)

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
                from_icon = ctk.CTkImage(light_image=icon_from, size=(30, 30))
                from_label = ctk.CTkLabel(self, image=from_icon, text="", width=38)
                from_label.image = from_icon
            except:
                from_label = ctk.CTkLabel(self, text="⬆️", font=("Arial", 18))
            from_label.grid(row=row, column=0, padx=2, pady=6)
            
            try:
                icon_to = Image.open(resource_path(f"assets/{t.to_account_ref.icon_url}"))
                to_icon = ctk.CTkImage(light_image=icon_to, size=(30, 30))
                to_label = ctk.CTkLabel(self, image=to_icon, text="", width=38)
                to_label.image = to_icon
            except:
                to_label = ctk.CTkLabel(self, text="⬇️", font=("Arial", 18))
            to_label.grid(row=row, column=1, padx=2, pady=6)
            
            date_label = ctk.CTkLabel(
                self, 
                text=t.transfer_date_time.strftime("%d.%m.%y"), 
                text_color="black", 
                font=("Arial", 13)
            )
            date_label.grid(row=row, column=2, padx=2, pady=6, sticky="ew")
            
            time_label = ctk.CTkLabel(
                self, 
                text=t.transfer_date_time.strftime("%H:%M"), 
                text_color="black", 
                font=("Arial", 13)
            )
            time_label.grid(row=row, column=3, padx=2, pady=6, sticky="ew")
            
            amount_label = ctk.CTkLabel(
                self, 
                text=f"{t.amount:,.2f}", 
                text_color="black", 
                font=("Arial", 13, "bold")
            )
            amount_label.grid(row=row, column=4, padx=2, pady=6, sticky="e")
            
            comment_text = t.description if t.description else "—"
            comment_label = ctk.CTkLabel(
                self, 
                text=comment_text, 
                text_color="black", 
                font=("Arial", 13),
                wraplength=320,
                justify="left",
                anchor="w"
            )
            comment_label.grid(row=row, column=5, padx=2, pady=6, sticky="w")


class TransactionsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=6)
        self.grid_columnconfigure(1, weight=4)

        self.main_label = ctk.CTkLabel(
            self, 
            text="Транзакции и переводы", 
            font=("Arial", 26, "bold"),
            text_color="white"
        )
        self.main_label.grid(row=0, column=0, columnspan=2, sticky="nw", padx=15, pady=(15, 5))

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
        self.current_filter_account = account_name
        self.transactions_frame.update_frame(account_name)

    def update_transactions(self):
        self.transactions_frame.update_frame(self.current_filter_account)

    def update_transfers(self):
        self.transfers_frame.update_frame()

    def update_categories(self):
        pass
    
    def update_accounts_filter(self):
        if hasattr(self, 'filter_panel') and self.filter_panel:
            self.filter_panel.update_accounts_list()
    
    def disable_all_scroll(self):
        """Отключает прокрутку всех скроллируемых фреймов на странице"""
        if hasattr(self, 'transactions_frame'):
            self.transactions_frame.disable_scroll()
        if hasattr(self, 'transfers_frame'):
            self.transfers_frame.disable_scroll()
    
    def enable_all_scroll(self):
        """Включает прокрутку всех скроллируемых фреймов на странице"""
        if hasattr(self, 'transactions_frame'):
            self.transactions_frame.enable_scroll()
        if hasattr(self, 'transfers_frame'):
            self.transfers_frame.enable_scroll()