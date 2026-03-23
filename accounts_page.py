from datetime import date
import tempfile
import os
import platform
import subprocess

import customtkinter as ctk
from PIL import Image
from sqlalchemy import desc
from CustomTkinterMessagebox import CTkMessagebox

from addition_classes import recolor_icon
from category_creation import resource_path
from db_management import session, AccountsTable, TransactionsTable, CategoriesTable, TransfersTable
from transfer_creation import NewTransferWindow
from account_creation import AccountCreationWindow

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


class AccountEntityFrame(ctk.CTkFrame):
    def __init__(self, master, data : list[AccountsTable], **kwargs):
        global acc_index
        super().__init__(master, **kwargs)
        self.configure(fg_color="#d9d9d9")
        self.data = data
        self.master_ref = master

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)
        self.grid_columnconfigure(2, weight=3)
        self.grid_columnconfigure(3, weight=0)  # Колонка для кнопки удаления
        
        row_height = 70
        total_rows = len(data) + 1
        self.configure(height=row_height * total_rows)

        if data and len(data) > 0:
            self.label = ctk.CTkLabel(self, text=data[0].type, text_color="black", font=("Arial", 20, "bold"))
            self.label.grid(row=0, column=0, sticky="w", padx=20, pady=(10, 0))

            for i, acc in enumerate(data):
                # Иконка счета
                icon_image = ctk.CTkImage(light_image=Image.open(resource_path(
                    f"assets/{acc.icon_url}")), size=(50,50))
                icon_label = ctk.CTkLabel(self, image=icon_image, text="")
                icon_label.grid(row=i+1, column=0, padx=(20, 0), pady=10, sticky="w")

                # Название счета
                acc_name = ctk.CTkLabel(self, text=acc.description, text_color="black", font=("Arial", 18), wraplength=300)
                acc_name.grid(row=i+1, column=1, padx=0, pady=10, sticky="we")

                # Сумма
                amount = ctk.CTkLabel(self, text=f"{acc.amount:,.2f}", text_color="black", font=("Arial", 18))
                amount.grid(row=i+1, column=2, padx=(0, 10), pady=10, sticky="e")
                
                # Кнопка удаления счета
                try:
                    delete_icon = ctk.CTkImage(
                        light_image=Image.open(resource_path("assets/icons/delete.png")),
                        size=(24, 24)
                    )
                    delete_button = ctk.CTkButton(
                        self,
                        text="",
                        image=delete_icon,
                        width=35,
                        height=35,
                        fg_color="#FF6B6B",
                        hover_color="#FF5252",
                        command=lambda a=acc: self._delete_account(a)
                    )
                except:
                    delete_button = ctk.CTkButton(
                        self,
                        text="🗑️",
                        width=35,
                        height=35,
                        fg_color="#FF6B6B",
                        hover_color="#FF5252",
                        command=lambda a=acc: self._delete_account(a)
                    )
                delete_button.grid(row=i+1, column=3, padx=(10, 20), pady=10, sticky="e")
                
                acc_index += 1
    
    def _delete_account(self, account):
        """Удаляет счет с подтверждением"""
        # Проверяем, есть ли транзакции на этом счете
        transactions_count = session.query(TransactionsTable).filter_by(
            account_id=account.account_id
        ).count()
        
        if transactions_count > 0:
            CTkMessagebox.messagebox(
                title="Невозможно удалить счет", 
                text=f"На счете '{account.description}' есть {transactions_count} транзакций.\n\n"
                     f"Сначала удалите или перенесите все транзакции с этого счета."
            )
            return
        
        # Проверяем, есть ли переводы с этого счета или на этот счет
        transfers_from_count = session.query(TransfersTable).filter_by(
            from_account=account.account_id
        ).count()
        
        transfers_to_count = session.query(TransfersTable).filter_by(
            to_account=account.account_id
        ).count()
        
        if transfers_from_count > 0 or transfers_to_count > 0:
            CTkMessagebox.messagebox(
                title="Невозможно удалить счет", 
                text=f"Счет '{account.description}' участвует в {transfers_from_count + transfers_to_count} переводах.\n\n"
                     f"Сначала удалите все переводы с этого счета и на этот счет."
            )
            return
        
        # Создаем кастомное окно подтверждения
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Подтверждение удаления")
        confirm_window.geometry("400x250")
        confirm_window.resizable(False, False)
        confirm_window.transient(self)
        confirm_window.grab_set()
        
        confirm_window.grid_columnconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(1, weight=0)
        confirm_window.grid_rowconfigure(2, weight=0)
        
        # Основной фрейм
        main_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Иконка вопроса
        icon_label = ctk.CTkLabel(main_frame, text="❓", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 15))
        
        # Текст вопроса
        question_label = ctk.CTkLabel(
            main_frame,
            text=f"Вы уверены, что хотите удалить счет\n'{account.description}'?",
            font=("Arial", 16),
            justify="center"
        )
        question_label.grid(row=1, column=0, pady=10)
        
        # Предупреждение
        warning_label = ctk.CTkLabel(
            main_frame,
            text="Это действие нельзя отменить!",
            font=("Arial", 12),
            text_color="#FF6B6B",
            justify="center"
        )
        warning_label.grid(row=2, column=0, pady=10)
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        buttons_frame.grid(row=1, column=0, pady=20)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        result = [False]  # Используем список для изменения значения внутри замыкания
        
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
            font=("Arial", 14, "bold"),
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            width=120,
            height=40
        )
        yes_button.grid(row=0, column=0, padx=10)
        
        no_button = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            command=on_no,
            font=("Arial", 14, "bold"),
            width=120,
            height=40
        )
        no_button.grid(row=0, column=1, padx=10)
        
        # Ждем закрытия окна
        confirm_window.wait_window()
        
        if result[0]:
            try:
                session.delete(account)
                session.commit()
                
                CTkMessagebox.messagebox(title="Успех!", text=f"Счет '{account.description}' успешно удален!")
                
                # Обновляем фильтр на странице транзакций
                if hasattr(self.master_ref, 'app_instance') and hasattr(self.master_ref.app_instance, 'pages'):
                    if 'transactions' in self.master_ref.app_instance.pages:
                        self.master_ref.app_instance.pages['transactions'].update_accounts_filter()
                
                # Обновляем страницу счетов
                self.master_ref.update_frame()
                
            except Exception as e:
                session.rollback()
                CTkMessagebox.messagebox(title="Ошибка!", text=f"Не удалось удалить счет: {str(e)}")


class AccountsFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.app_instance = app_instance
        self.new_transfer = NewTransferWindow(app_instance)
        self.new_transfer.withdraw()
        self.new_account_window = None

        self.update_frame()

    def update_frame(self):
        """Обновляет фрейм со счетами"""
        try:
            # Сохраняем ссылку на окно создания счета, если оно открыто
            existing_window = self.new_account_window if hasattr(self, 'new_account_window') else None
            window_exists = existing_window and existing_window.winfo_exists() if existing_window else False
            
            # Очищаем виджеты
            for widget in self.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass
            
            # Восстанавливаем окно создания счета, если оно было открыто
            if window_exists and existing_window and not existing_window.winfo_exists():
                self.new_account_window = None

            accounts_sum = sum(float(acc.amount) for acc in session.query(AccountsTable).all())

            label = ctk.CTkLabel(self, text_color="black", text="Счета", font=("Arial", 24, "bold"))
            label.grid(row=0, column=0, sticky="w", padx=20, pady=20)

            amount_sum = ctk.CTkLabel(self, text=f"Итого: {accounts_sum:,.2f}", text_color="black",
                                           font=("Arial", 20, "bold"))
            amount_sum.grid(row=0, column=1, sticky="we", padx=20, pady=40)

            # Создаем фрейм для кнопок
            buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
            buttons_frame.grid(row=0, column=2, sticky="e", padx=20, pady=20)

            # Кнопка "Новый счет" с иконкой кошелька с плюсом
            try:
                wallet_icon = ctk.CTkImage(
                    light_image=Image.open(resource_path("assets/icons/sidebar/wallet_add.png")),
                    size=(24, 24)
                )
                new_account_button = ctk.CTkButton(
                    buttons_frame, 
                    text="  Новый счет",
                    text_color="black",
                    font=("Arial", 14, "bold"),
                    command=self._create_account,
                    fg_color="#4CAF50",
                    hover_color="#45a049",
                    width=140,
                    height=40,
                    image=wallet_icon,
                    compound="left"
                )
            except:
                # Если иконка не найдена, показываем текстовую кнопку
                new_account_button = ctk.CTkButton(
                    buttons_frame, 
                    text="💰  Новый счет", 
                    text_color="black",
                    font=("Arial", 14, "bold"),
                    command=self._create_account,
                    fg_color="#4CAF50",
                    hover_color="#45a049",
                    width=140,
                    height=40
                )
            new_account_button.pack(side="left", padx=(0, 10))

            # Кнопка "Добавить перевод"
            create_transfer_button = ctk.CTkButton(
                buttons_frame, 
                text="Добавить перевод", 
                text_color="black",
                command=self._create_transfer,
                width=150,
                height=40
            )
            create_transfer_button.pack(side="left")

            standard_data = session.query(AccountsTable).filter_by(type="Обычный").all()
            if standard_data:
                standard_accounts = AccountEntityFrame(self, standard_data)
                standard_accounts.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
                standard_accounts.grid_propagate(False)

            cred_data = session.query(AccountsTable).filter_by(type="Кредитный").all()
            if cred_data:
                cred_accounts = AccountEntityFrame(self, cred_data)
                cred_accounts.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
                cred_accounts.grid_propagate(False)

            accum_data = session.query(AccountsTable).filter_by(type="Накопительный").all()
            if accum_data:
                accum_accounts = AccountEntityFrame(self, accum_data)
                accum_accounts.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
                accum_accounts.grid_propagate(False)
                
        except Exception as e:
            print(f"Ошибка при обновлении фрейма счетов: {e}")

    def _create_transfer(self):
        if not self.new_transfer.winfo_exists():
            self.new_transfer = NewTransferWindow(master=self.master, app_instance=self.app_instance)

        self.new_transfer.attributes('-topmost', True)
        self.new_transfer.deiconify()
        self.new_transfer.update()
        self.new_transfer.focus()

        self.new_transfer.bind("<<DateSelected>>", lambda x: self.new_transfer.destroy())

    def _create_account(self):
        """Открывает окно создания нового счета"""
        try:
            if self.new_account_window is None or not self.new_account_window.winfo_exists():
                self.new_account_window = AccountCreationWindow(
                    master=self.master,
                    app_instance=self.app_instance
                )

            self.new_account_window.attributes('-topmost', True)
            self.new_account_window.deiconify()
            self.new_account_window.update()
            self.new_account_window.focus()
        except Exception as e:
            print(f"Ошибка при открытии окна создания счета: {e}")
            self.new_account_window = None


class TransactionsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        
        self.grid_columnconfigure(0, weight=0, minsize=50)
        self.grid_columnconfigure(1, weight=4, minsize=200)
        self.grid_columnconfigure(2, weight=0, minsize=60)
        self.grid_columnconfigure(3, weight=0, minsize=80)
        self.grid_columnconfigure(4, weight=1, minsize=100)

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
                from CustomTkinterMessagebox import CTkMessagebox
                CTkMessagebox.messagebox(title="Ошибка!", text=f"Не удалось открыть чек: {str(e)}")
        else:
            from CustomTkinterMessagebox import CTkMessagebox
            CTkMessagebox.messagebox(title="Информация", text="Чек не найден")

    def update_frame(self):
        """Обновляет список последних транзакций"""
        try:
            for widget in self.winfo_children():
                widget.destroy()

            self.label = ctk.CTkLabel(self, text_color="black", text="Последние транзакции", 
                                       font=("Arial", 18, "bold"))
            self.label.grid(row=0, column=0, columnspan=5, padx=20, pady=20, sticky="w")

            headers = ["Категория", "Описание", "Дата", "Время", "Сумма"]
            header_colors = ["black", "black", "black", "black", "black"]
            header_font = ("Arial", 14, "bold")
            header_alignments = ["w", "w", "center", "center", "e"]
            
            for col, (header, color, align) in enumerate(zip(headers, header_colors, header_alignments)):
                header_label = ctk.CTkLabel(
                    self, 
                    text=header, 
                    text_color=color, 
                    font=header_font,
                    anchor=align
                )
                header_label.grid(row=1, column=col, padx=10, pady=(5, 10), sticky="ew")

            # Получаем последние 20 транзакций со всеми счетами
            trans_cat_model = session.query(CategoriesTable, TransactionsTable
                                    ).join(TransactionsTable, TransactionsTable.category_id == CategoriesTable.category_id
                                    ).order_by(desc(TransactionsTable.transaction_date_time)).limit(20).all()

            for i, (cat, trans) in enumerate(trans_cat_model):
                row = i + 2
                
                icon_image = ctk.CTkImage(light_image=recolor_icon(resource_path(
                    f"assets/{cat.icon_url}"), cat.colour), size=(35, 35))
                icon_label = ctk.CTkLabel(self, image=icon_image, text="", width=40, height=40)
                icon_label.grid(row=row, column=0, padx=(10, 5), pady=8, sticky="w")

                if trans.description and trans.description.strip() != "":
                    comment_text = trans.description
                else:
                    comment_text = cat.category_name
                    
                transaction_name = ctk.CTkLabel(
                    self, 
                    text_color="black", 
                    font=("Arial", 13), 
                    text=comment_text,
                    wraplength=200,
                    justify="left",
                    anchor="w"
                )
                transaction_name.grid(row=row, column=1, padx=(5, 10), pady=8, sticky="w")

                date_str = f"{trans.transaction_date_time.day}.{trans.transaction_date_time.month:02d}"
                date_label = ctk.CTkLabel(
                    self, 
                    text=date_str,
                    text_color="black", 
                    font=("Arial", 13),
                    anchor="center"
                )
                date_label.grid(row=row, column=2, padx=5, pady=8, sticky="ew")

                time_str = trans.transaction_date_time.strftime("%H:%M:%S")
                time_label = ctk.CTkLabel(
                    self, 
                    text=time_str,
                    text_color="black", 
                    font=("Arial", 13),
                    anchor="center"
                )
                time_label.grid(row=row, column=3, padx=5, pady=8, sticky="ew")

                amount_color = "green" if cat.transaction_type == "Доход" else "red"
                amount_label = ctk.CTkLabel(
                    self, 
                    text=f"{trans.amount:,.2f}", 
                    font=("Arial", 13, "bold"),
                    text_color=amount_color,
                    anchor="e"
                )
                amount_label.grid(row=row, column=4, padx=(5, 15), pady=8, sticky="e")
                
        except Exception as e:
            print(f"Ошибка при обновлении списка транзакций: {e}")


class AccountsPage(ctk.CTkFrame):
    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
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

    def update_categories(self):
        """Обновление категорий (для совместимости)"""
        pass
    
    def update_frame(self):
        """Обновляет фрейм счетов"""
        if hasattr(self, 'accounts_frame') and self.accounts_frame:
            self.accounts_frame.update_frame()