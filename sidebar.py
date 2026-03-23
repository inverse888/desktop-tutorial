import customtkinter as ctk

from addition_classes import recolor_icon, app_color, resource_path
from transaction_creation import NewTransactionWindow

class SideBar(ctk.CTkFrame):
    def __init__(self, master, show_function, **kwargs):
        super().__init__(master, **kwargs)
        for i in range(8):
            self.grid_rowconfigure(i, weight=1)

        self.width = 60
        self.height = 60
        self.show_function = show_function
        self.current_page = "main"  # Текущая активная страница

        # Стили для кнопок
        self.active_style = {
            "fg_color": app_color["dark_blue"],  # Темно-синий для активной
            "hover_color": app_color["dark_blue"]
        }
        self.inactive_style = {
            "fg_color": "transparent",  # Прозрачный для неактивной
            "hover_color": app_color["blue"]
        }

        # Кнопка "Главная"
        self.main_button = ctk.CTkButton(self, width=self.width, height=self.height, text="", 
            command=lambda: self._on_button_click("main"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path("assets/icons/sidebar/house.png"),
                                app_color["light_blue"]), size=(40,40))),
            **self.active_style)  # По умолчанию активна главная
        self.main_button.grid(row=0, column=0, padx=20, pady=20, sticky="we")

        # Кнопка "Расходы"
        self.expenses_button = ctk.CTkButton(self, width=self.width, height=self.height, text="", 
            command=lambda: self._on_button_click("expenses"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path(
                "assets/icons/sidebar/money-transaction.png"), app_color["light_blue"]), size=(40,40))),
            **self.inactive_style)
        self.expenses_button.grid(row=1, column=0, padx=20, pady=20, sticky="we")

        # Кнопка "Счета"
        self.accounts_button = ctk.CTkButton(self, width=self.width, height=self.height, text="", 
            command=lambda: self._on_button_click("accounts"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path(
                "assets/icons/sidebar/credit-card.png"), app_color["light_blue"]), size=(40,40))),
            **self.inactive_style)
        self.accounts_button.grid(row=2, column=0, padx=20, pady=20, sticky="we")

        # Кнопка "Транзакции"
        self.transactions_button = ctk.CTkButton(self, width=self.width, height=self.height, text="",
            command=lambda: self._on_button_click("transactions"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path(
                "assets/icons/sidebar/currency.png"), app_color["light_blue"]), size=(40, 40))),
            **self.inactive_style)
        self.transactions_button.grid(row=3, column=0, padx=20, pady=20, sticky="we")

        # Кнопка "Настройки"
        self.settings_button = ctk.CTkButton(self, width=self.width, height=self.height, text="", 
            command=lambda: self._on_button_click("settings"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path(
                "assets/icons/sidebar/settings.png"), app_color["light_blue"]), size=(40, 40))),
            **self.inactive_style)
        self.settings_button.grid(row=4, column=0, padx=20, pady=20, sticky="we")

        # Кнопка "+" для создания транзакции (не подсвечивается)
        self.plus_button = ctk.CTkButton(self, width=self.width, height=self.height, text="",
                                         command=self.open_new_transaction,
                                         image=(ctk.CTkImage(light_image=recolor_icon(
                                             resource_path("assets/icons/sidebar/add.png"),
                                                app_color["light_blue"]), size=(40, 40))),
                                         fg_color="transparent",
                                         hover_color=app_color["blue"])
        self.plus_button.grid(row=5, column=0, padx=20, pady=20, sticky="swe")

        self.new_transaction = None
        self.buttons = {
            "main": self.main_button,
            "expenses": self.expenses_button,
            "accounts": self.accounts_button,
            "transactions": self.transactions_button,
            "settings": self.settings_button
        }

    def _on_button_click(self, page_name):
        """Обработчик нажатия на кнопку"""
        self.set_active_button(page_name)
        self.show_function(page_name)

    def set_active_button(self, page_name):
        """Устанавливает активную кнопку"""
        # Сбрасываем все кнопки на неактивный стиль
        for name, button in self.buttons.items():
            button.configure(**self.inactive_style)
        
        # Устанавливаем активную кнопку
        if page_name in self.buttons:
            self.buttons[page_name].configure(**self.active_style)
            self.current_page = page_name

    def open_new_transaction(self):
        try:
            # Проверяем существует ли окно и не уничтожено ли оно
            if self.new_transaction is not None:
                try:
                    if self.new_transaction.winfo_exists():
                        self.new_transaction.deiconify()
                        self.new_transaction.lift()
                        self.new_transaction.focus_force()
                        return
                except:
                    self.new_transaction = None
            
            # Создаем новое окно
            self.new_transaction = NewTransactionWindow(self.master)
            self.new_transaction.attributes('-topmost', True)
            self.new_transaction.deiconify()
            self.new_transaction.lift()
            self.new_transaction.focus_force()
            
            # Привязываем событие закрытия
            self.new_transaction.protocol("WM_DELETE_WINDOW", self.close_pop_up_window)
            
        except Exception as e:
            print(f"Ошибка при открытии окна: {e}")
            self.new_transaction = None

    def close_pop_up_window(self):
        try:
            if self.new_transaction is not None:
                if self.new_transaction.winfo_exists():
                    self.new_transaction.destroy()
                self.new_transaction = None
        except:
            self.new_transaction = None