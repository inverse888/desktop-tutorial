import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox
from PIL import Image

from addition_classes import resource_path
from db_management import session, AccountsTable
from category_creation import get_icon_names


class AccountCreationWindow(ctk.CTkToplevel):
    def __init__(self, master, app_instance, **kwargs):
        super().__init__(**kwargs)
        
        self.geometry("600x550+400+100")
        self.title("Создание счета")
        self.resizable(False, False)
        self.configure(fg_color="#aba6a6")
        
        self.master = master
        self.app_instance = app_instance
        self._destroying = False
        self._creation_in_progress = False
        
        # Создаем все виджеты
        self._create_widgets()
        
        # Загружаем иконки
        self.load_icons()
        
        self.protocol("WM_DELETE_WINDOW", self.safe_destroy)
        
        # Откладываем установку фокуса
        self.after(100, self._safe_focus_entry)
    
    def _safe_focus_entry(self):
        """Безопасная установка фокуса на поле ввода"""
        if not self._destroying and not self._creation_in_progress:
            try:
                if self.winfo_exists() and self.name_entry and self.name_entry.winfo_exists():
                    self.name_entry.focus_set()
            except:
                pass
    
    def _create_widgets(self):
        """Создает все виджеты окна"""
        # Настройка сетки
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=0)
        self.grid_columnconfigure(0, weight=1)
        
        # Тип счета
        self.type_label = ctk.CTkLabel(
            self, 
            text="Тип счета", 
            font=("Arial", 16, "bold"),
            text_color="black"
        )
        self.type_label.grid(row=0, column=0, sticky="w", padx=30, pady=(20, 5))
        
        self.account_type = ctk.CTkOptionMenu(
            self,
            values=["Обычный", "Кредитный", "Накопительный"],
            font=("Arial", 14),
            fg_color="#d9d9d9",
            button_color="#8a8585",
            text_color="black"
        )
        self.account_type.grid(row=0, column=0, sticky="ew", padx=30, pady=(5, 10))
        self.account_type.set("Обычный")
        
        # Название счета
        self.name_label = ctk.CTkLabel(
            self, 
            text="Название счета", 
            font=("Arial", 16, "bold"),
            text_color="black"
        )
        self.name_label.grid(row=1, column=0, sticky="w", padx=30, pady=(10, 5))
        
        self.name_entry = ctk.CTkEntry(
            self,
            placeholder_text="Например: Наличные, Карта, Сбережения...",
            placeholder_text_color="gray",
            text_color="white",
            font=("Arial", 14),
            height=40
        )
        self.name_entry.grid(row=1, column=0, sticky="ew", padx=30, pady=(5, 10))
        
        # Начальный баланс
        self.balance_label = ctk.CTkLabel(
            self, 
            text="Начальный баланс", 
            font=("Arial", 16, "bold"),
            text_color="black"
        )
        self.balance_label.grid(row=2, column=0, sticky="w", padx=30, pady=(10, 5))
        
        self.balance_entry = ctk.CTkEntry(
            self,
            placeholder_text="0.00",
            placeholder_text_color="gray",
            text_color="white",
            font=("Arial", 14),
            height=40
        )
        self.balance_entry.grid(row=2, column=0, sticky="ew", padx=30, pady=(5, 10))
        
        # Иконки
        self.icons_label = ctk.CTkLabel(
            self, 
            text="Выберите иконку", 
            font=("Arial", 16, "bold"),
            text_color="black"
        )
        self.icons_label.grid(row=3, column=0, sticky="w", padx=30, pady=(10, 5))
        
        self.icons_frame = ctk.CTkScrollableFrame(self, fg_color="#949191", height=200)
        self.icons_frame.grid(row=3, column=0, sticky="nsew", padx=30, pady=(5, 10))
        self.icons_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        self.selected_icon = None
        self.icon_buttons = []
        
        # Кнопки
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.grid(row=4, column=0, sticky="ew", padx=30, pady=20)
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.create_button = ctk.CTkButton(
            self.buttons_frame,
            text="Создать счет",
            command=self.create_account,
            font=("Arial", 16, "bold"),
            height=45,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        self.create_button.grid(row=0, column=0, padx=10, pady=5)
        
        self.cancel_button = ctk.CTkButton(
            self.buttons_frame,
            text="Отмена",
            command=self.safe_destroy,
            font=("Arial", 16, "bold"),
            height=45,
            fg_color="#FF6B6B",
            hover_color="#FF5252"
        )
        self.cancel_button.grid(row=0, column=1, padx=10, pady=5)
    
    def load_icons(self):
        """Загружает иконки из папки assets/icons/categories"""
        if self._destroying or not self.winfo_exists():
            return
            
        icon_names = get_icon_names("assets/icons/categories")
        
        if not icon_names:
            empty_label = ctk.CTkLabel(
                self.icons_frame,
                text="Иконки не найдены.\nДобавьте иконки в папку assets/icons/categories/",
                font=("Arial", 14),
                text_color="gray",
                justify="center"
            )
            empty_label.grid(row=0, column=0, columnspan=5, padx=20, pady=20)
            return
        
        for i, icon_name in enumerate(icon_names):
            row = i // 5
            col = i % 5
            
            icon_path = resource_path(f"assets/icons/categories/{icon_name}.png")
            
            try:
                icon_image = ctk.CTkImage(
                    light_image=Image.open(icon_path),
                    size=(50, 50)
                )
                
                icon_container = ctk.CTkFrame(
                    self.icons_frame,
                    fg_color="transparent",
                    corner_radius=8
                )
                icon_container.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
                
                icon_button = ctk.CTkButton(
                    icon_container,
                    image=icon_image,
                    text="",
                    width=60,
                    height=60,
                    fg_color="transparent",
                    hover_color="#8a8585",
                    command=lambda n=icon_name, c=icon_container: self.select_icon(n, c)
                )
                icon_button.pack(pady=(5, 2))
                
                name_label = ctk.CTkLabel(
                    icon_container,
                    text=icon_name,
                    font=("Arial", 10),
                    text_color="black"
                )
                name_label.pack()
                
                self.icon_buttons.append({
                    "name": icon_name,
                    "button": icon_button,
                    "container": icon_container
                })
                
            except Exception as e:
                print(f"Ошибка загрузки иконки {icon_name}: {e}")
                continue
    
    def select_icon(self, icon_name, container):
        """Выбирает иконку"""
        if self._destroying:
            return
            
        for icon in self.icon_buttons:
            try:
                if icon["container"].winfo_exists():
                    icon["container"].configure(fg_color="transparent")
            except:
                pass
        
        try:
            if container.winfo_exists():
                container.configure(fg_color="#4CAF50")
                self.selected_icon = icon_name
        except:
            pass
    
    def create_account(self):
        """Создает новый счет"""
        if self._destroying or self._creation_in_progress:
            return
        
        self._creation_in_progress = True
        
        # Отключаем кнопку, чтобы избежать повторных нажатий
        self.create_button.configure(state="disabled", text="Создание...")
        
        try:
            account_type = self.account_type.get()
            account_name = self.name_entry.get().strip()
            balance_str = self.balance_entry.get().strip()
            
            if not account_name:
                CTkMessagebox.messagebox(title="Ошибка!", text="Введите название счета!")
                return
            
            if not self.selected_icon:
                CTkMessagebox.messagebox(title="Ошибка!", text="Выберите иконку для счета!")
                return
            
            existing = session.query(AccountsTable).filter_by(
                description=account_name
            ).first()
            
            if existing:
                CTkMessagebox.messagebox(title="Ошибка!", text=f"Счет '{account_name}' уже существует!")
                return
            
            try:
                if not balance_str:
                    balance = 0.0
                else:
                    balance_str = balance_str.replace(',', '.')
                    balance = float(balance_str)
            except ValueError:
                CTkMessagebox.messagebox(title="Ошибка!", text="Некорректный формат суммы!")
                return
            
            # Создаем счет
            new_account = AccountsTable(
                type=account_type,
                amount=balance,
                icon_url=f"icons/categories/{self.selected_icon}.png",
                description=account_name
            )
            
            session.add(new_account)
            session.commit()
            
            # Показываем сообщение об успехе
            CTkMessagebox.messagebox(title="Успех!", text=f"Счет '{account_name}' успешно создан!")
            
            # Обновляем интерфейс с задержкой
            if self.app_instance:
                self.after(100, self._update_interface)
            
            # Закрываем окно с задержкой
            self.after(200, self.safe_destroy)
            
        except Exception as e:
            session.rollback()
            CTkMessagebox.messagebox(title="Ошибка!", text=f"Не удалось создать счет: {str(e)}")
            self.create_button.configure(state="normal", text="Создать счет")
            self._creation_in_progress = False
    
    def _update_interface(self):
        """Обновляет интерфейс после создания счета"""
        try:
            if self.app_instance:
                # Обновляем страницу счетов
                if hasattr(self.app_instance.pages["accounts"], 'update_frame'):
                    self.app_instance.pages["accounts"].update_frame()
                
                # Обновляем фильтр на странице транзакций
                if hasattr(self.app_instance.pages["transactions"], 'update_accounts_filter'):
                    self.app_instance.pages["transactions"].update_accounts_filter()
                
                # Принудительно обновляем все страницы
                if hasattr(self.app_instance, 'schedule_full_update'):
                    self.app_instance.schedule_full_update()
        except Exception as e:
            print(f"Ошибка при обновлении интерфейса: {e}")
    
    def safe_destroy(self):
        """Безопасное уничтожение окна"""
        if self._destroying:
            return
        
        self._destroying = True
        
        try:
            # Убираем флаг topmost
            try:
                self.attributes('-topmost', False)
            except:
                pass
            
            # Отвязываем все обработчики
            try:
                self.unbind_all("<<DateSelected>>")
            except:
                pass
            
            # Отключаем все виджеты, чтобы предотвратить дальнейшие события
            for widget in [self.name_entry, self.balance_entry, self.create_button, self.cancel_button]:
                try:
                    if widget and widget.winfo_exists():
                        widget.configure(state="disabled")
                except:
                    pass
            
            # Уничтожаем окно
            if self.winfo_exists():
                self.destroy()
        except Exception as e:
            print(f"Ошибка при уничтожении окна: {e}")