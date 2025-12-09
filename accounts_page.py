from datetime import date

import customtkinter as ctk
from PIL import Image
from sqlalchemy import desc

from addition_classes import recolor_icon
from category_creation import resource_path
from db_management import session, AccountsTable, TransactionsTable, CategoriesTable
from transfer_creation import NewTransferWindow

acc_index = 0

class CategoriesLabelsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#949191")
        self.grid_propagate(False)
        for i in range(5):
            self.grid_rowconfigure(i, weight=1)
        for i in range(3):
            self.grid_columnconfigure(i, weight=1)

        categories = [("Продукты", "40%", "#5A6ACF"),
                      ("Жильё", "32%", "#8593ED"),
                      ("Досуг", "28%", "#FF81C5"),]

        for i, (label, amount, color) in enumerate(categories):
            (ctk.CTkLabel(self, text=label, text_color="black")
             .grid(row=i, column=0, sticky="w", padx=(20, 10), pady=10))
            (ctk.CTkLabel(self, text=amount, text_color="black")
             .grid(row=i, column=1, sticky="e", padx=(10, 20), pady=10))


class CanvasFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#949191")
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.category_labels_frame = CategoriesLabelsFrame(self)
        self.category_labels_frame.grid(row=1, column=1, sticky="w", padx=20, pady=20)


class AccountEntityFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, data : list[AccountsTable], **kwargs):
        global acc_index
        super().__init__(master, **kwargs)
        self.configure(fg_color="#d9d9d9")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)
        self.grid_columnconfigure(2, weight=3)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=4)
        self.grid_rowconfigure(2, weight=4)
        self.grid_rowconfigure(3, weight=4)
        self.grid_rowconfigure(4, weight=4)

        # обычные/кредитные/накопительные
        self.label = ctk.CTkLabel(self, text=data[0].type, text_color="black", font=("Arial", 20, "bold"))
        self.label.grid(row=0, column=0, sticky="w", padx=20, pady=(10, 0))

        for i, acc in enumerate(data):
            icon_image = ctk.CTkImage(light_image=Image.open(resource_path(
                f"assets/{acc.icon_url}")), size=(50,50))
            icon_label = ctk.CTkLabel(self, image=icon_image, text="")
            icon_label.grid(row=i+1, column=0, padx=(20, 0), pady=10, sticky="w")

            acc_name = ctk.CTkLabel(self, text=acc.description, text_color="black", font=("Arial", 18), wraplength=300)
            acc_name.grid(row=i+1, column=1, padx=0, pady=10, sticky="we")

            amount = ctk.CTkLabel(self, text=f"{acc.amount:,.2f}", text_color="black", font=("Arial", 18))
            amount.grid(row=i+1, column=2, padx=0, pady=10, sticky="e")
            acc_index += 1



class AccountsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=4)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.app_instance = app_instance
        self.new_transfer = NewTransferWindow(app_instance)
        self.new_transfer.withdraw()

        self.update_frame()

    def update_frame(self):
        accounts_sum = sum(float(acc.amount) for acc in session.query(AccountsTable).all())

        label = ctk.CTkLabel(self, text_color="black", text="Счета", font=("Arial", 24, "bold"))
        label.grid(row=0, column=0, sticky="w", padx=20, pady=20)

        amount_sum = ctk.CTkLabel(self, text=f"Итого: {accounts_sum:,.2f}", text_color="black",
                                       font=("Arial", 20, "bold"))
        amount_sum.grid(row=0, column=1, sticky="we", padx=20, pady=40)

        create_transfer_button = ctk.CTkButton(self, text_color="black", text="Добавить перевод",
                                               command=self._create_transfer)
        create_transfer_button.grid(row=0, column=2, sticky="e", padx=20, pady=20)

        standard_accounts = AccountEntityFrame(self, session.query(AccountsTable).filter_by(type="Обычный").all())
        standard_accounts.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)

        cred_accounts = AccountEntityFrame(self, session.query(AccountsTable).filter_by(type="Кредитный").all())
        cred_accounts.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)

        accum_accounts = AccountEntityFrame(self, session.query(AccountsTable).filter_by(type="Накопительный").all())
        accum_accounts.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)

    def _create_transfer(self):
        if not self.new_transfer.winfo_exists():
            self.new_transfer = NewTransferWindow(master=self.master, app_instance=self.app_instance)

        self.new_transfer.attributes('-topmost', True)
        self.new_transfer.deiconify()
        self.new_transfer.update()
        self.new_transfer.focus()

        self.new_transfer.bind("<<DateSelected>>", lambda x: self.new_transfer.destroy())

class TransactionsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        self.grid_rowconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text_color="black", text="Транзакции", font=("Arial", 18, "bold"))
        self.label.grid(row=0, column=0, padx=20, pady=20)

        self.update_frame()

    def update_frame(self):
        trans_cat_model = session.query(CategoriesTable, TransactionsTable
                                ).join(TransactionsTable, TransactionsTable.category_id == CategoriesTable.category_id
                                ).order_by(desc(TransactionsTable.transaction_date_time)).all()

        for i, (cat, trans) in enumerate(trans_cat_model):
            icon_image = ctk.CTkImage(light_image=recolor_icon(resource_path(
                f"assets/{cat.icon_url}"), cat.colour), size=(40, 40))
            icon_label = ctk.CTkLabel(self, image=icon_image, text="", width=50, height=50)
            icon_label.grid(row=i+1, column=0, padx=(10, 0), pady=10, sticky="nwe")

            transaction_name = ctk.CTkLabel(self, text_color="black", font=("Arial", 14), wraplength=120, justify="left",
                                            text=trans.description if trans.description != "" else "<без комментария>")
            transaction_name.grid(row=i+1, column=1, padx=5, pady=10, sticky="nw")

            date_label = ctk.CTkLabel(self, text=f"{trans.transaction_date_time.day}"
                                                 f".0{trans.transaction_date_time.month}",
                                      text_color="black", font=("Arial", 14))
            date_label.grid(row=i+1, column=2, padx=(5, 0), pady=10, sticky="nw")

            amount_label = ctk.CTkLabel(self, text=f"{trans.amount:,.2f}", font=("Arial", 14),
                                        text_color="green" if cat.transaction_type == "Доход" else "red")
            amount_label.grid(row=i+1, column=3, padx=(10, 0), pady=10, sticky="nw")


class AccountsPage(ctk.CTkFrame):
    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.accounts_frame = AccountsFrame(self, app_instance)
        self.accounts_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)

        self.transactions_frame = TransactionsFrame(self, orientation="vertical")
        self.transactions_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)

    def update_transactions(self):
        self.transactions_frame.update_frame()
        self.accounts_frame.update_frame()

    def update_transfers(self):
        self.accounts_frame.update_frame()