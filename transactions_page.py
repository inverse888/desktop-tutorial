import customtkinter as ctk
from PIL import Image
import tempfile
import os
import platform
import subprocess

from addition_classes import resource_path
from db_management import session, TransactionsTable, TransfersTable


class TransactionsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        self.grid_rowconfigure(0, weight=1)

        self.update_frame()

    def show_receipt(self, transaction_id):
        """Показывает чек для указанной транзакции"""
        # SQL запрос на поиск транзакции
        transaction = session.query(TransactionsTable).filter_by(transaction_id=transaction_id).first()
        
        if transaction and transaction.check_photo:
            try:
                # Создаем временный файл для просмотра
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(transaction.check_photo)
                    temp_path = temp_file.name
                
                # Открываем изображение средствами системы
                if platform.system() == 'Darwin':  # macOS
                    subprocess.call(('open', temp_path))
                elif platform.system() == 'Windows':  # Windows
                    os.startfile(temp_path)
                else:  # linux variants
                    subprocess.call(('xdg-open', temp_path))
                    
            except Exception as e:
                from CustomTkinterMessagebox import CTkMessagebox
                CTkMessagebox.messagebox(title="Ошибка!", text=f"Не удалось открыть чек: {str(e)}")
        else:
            from CustomTkinterMessagebox import CTkMessagebox
            CTkMessagebox.messagebox(title="Информация", text="Чек не найден")
            

    def update_frame(self):
        transactions = (
            session.query(TransactionsTable)
            .order_by(TransactionsTable.transaction_date_time.desc())
            .all()
        )
        transactions_history = [
            {
                 "transaction_id": t.transaction_id,
                "Счёт": t.account.icon_url,
                "Дата": t.transaction_date_time.strftime("%d.%m.%y"),
                "Категория": {
                    "Имя" : t.category.category_name,
                    "Цвет": t.category.colour
                },
                "Сумма": {
                    "Количество" : float(t.amount),
                    "Тип": t.transaction_type
                },
                "Комментарий": t.description or "",
                "Чек": t.check_photo is not None  # Есть ли чек
            }
            for t in transactions
        ]

        if not transactions_history:
            ctk.CTkLabel(self, text="Нет транзакций за выбранный период", font=("Arial", 20)).pack(padx=20, pady=20)
            return
        # Заголовки таблицы
        headers = list(transactions_history[0].keys())
        headers.remove("transaction_id")  # Убираем ID из заголовков
        headers.append("Действия")  # Добавляем колонку для действий

        for col, name in enumerate(headers):
            label = ctk.CTkLabel(self, text=name, text_color="black", font=("Arial", 16, "bold"))
            label.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)

        # Данные транзакций
        for i, tr in enumerate(transactions_history):
            row = i + 1
            col = 0
            
            # Проходим по всем полям кроме transaction_id
            for key, value in tr.items():
                if key == "transaction_id":
                    continue
                    
                text_color = "black"

                if key == "Сумма":
                    text_color = "red" if value["Тип"] == "Расход" else "green"
                    value = f"{value['Количество']:,.2f}"

                if key == "Категория":
                    text_color = value["Цвет"]
                    value = value["Имя"]

                if key == "Счёт":
                    icon_image = Image.open(resource_path(f"assets/{tr['Счёт']}"))
                    label = ctk.CTkLabel(self, image=ctk.CTkImage(light_image=icon_image, size=(30, 30)), text="",
                                         compound="left", font=("Arial", 16))
                elif key == "Чек":
                    # Показываем иконку вместо текста
                    if value:  # Если чек есть
                        receipt_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/receipt.png")), size=(20, 20))
                        label = ctk.CTkLabel(self, image=receipt_icon, text="", font=("Arial", 16))
                    else:  # Если чека нет
                        label = ctk.CTkLabel(self, text="—", text_color="gray", font=("Arial", 16))
                else:
                    label = ctk.CTkLabel(self, text=value, text_color=text_color, font=("Arial", 16), wraplength=200)
                
                label.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
                col += 1

            # Колонка "Действия" - кнопка просмотра чека
            if tr["Чек"]:  # Если чек есть
                receipt_btn = ctk.CTkButton(
                    self, 
                    text="Просмотреть чек", 
                    width=100,
                    height=30,
                    font=("Arial", 12),
                    command=lambda tid=tr["transaction_id"]: self.show_receipt(tid)
                )
            else:  # Если чека нет
                receipt_btn = ctk.CTkButton(
                    self, 
                    text="Нет чека", 
                    width=100,
                    height=30,
                    font=("Arial", 12),
                    state="disabled",
                    fg_color="gray"
                )
            
            receipt_btn.grid(row=row, column=col, sticky="", padx=10, pady=10)
       


class TransfersFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        self.grid_rowconfigure(0, weight=1)

        self.update_frame()


    
            
            
    def update_frame(self):
        transfers = (
            session.query(TransfersTable)
            .order_by(TransfersTable.transfer_date_time.desc())
            .all()
        )
        transfers_history = [
            {
                "С": t.from_account_ref.icon_url,
                "На": t.to_account_ref.icon_url,
                "Дата": t.transfer_date_time.strftime("%d.%m.%y"),
                "Сумма": float(t.amount),
                "Комментарий": t.description or ""
            }
            for t in transfers
        ]

        if not transfers_history:
            ctk.CTkLabel(self, text="Нет переводов за выбранный период", font=("Arial", 20)).pack(padx=20, pady=20)
            return

        for col, name in enumerate(transfers_history[0].keys()):
            label = ctk.CTkLabel(self, text=name, text_color="black", font=("Arial", 16, "bold"))
            label.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)

        for i, tr in enumerate(transfers_history):
            for j, (key, value) in enumerate(tr.items()):
                if key == "Сумма":
                    value = f"{value:,.2f}"

                if key == "С" or key == "На":
                    icon_image = Image.open(resource_path(f"assets/{tr[key]}"))
                    label = ctk.CTkLabel(self, image=ctk.CTkImage(light_image=icon_image, size=(30, 30)), text="",
                                         compound="left", font=("Arial", 16))
                else:
                    label = ctk.CTkLabel(self, text=value, text_color="black", font=("Arial", 16), wraplength=170)

                label.grid(row=i+1, column=j, sticky="nsew", padx=10, pady=10)


class TransactionsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)

        self.main_label = ctk.CTkLabel(self, text="Транзакции", font=("Arial", 28))
        self.main_label.grid(row=0, column=0, sticky="nw", padx=20, pady=20)

        self.transactions_frame = TransactionsFrame(self, corner_radius=10)
        self.transactions_frame.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="nsew")

        self.transfers_frame = TransfersFrame(self, corner_radius=10)
        self.transfers_frame.grid(row=1, column=1, padx=(5, 10), pady=10, sticky="nsew")

    def update_transactions(self):
        self.transactions_frame.update_frame()

    def update_transfers(self):
        self.transfers_frame.update_frame()
