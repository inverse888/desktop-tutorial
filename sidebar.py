import customtkinter as ctk

from addition_classes import recolor_icon, app_color, resource_path
from transaction_creation import NewTransactionWindow

class SideBar(ctk.CTkFrame):
    def __init__(self, master, show_function, **kwargs):
        super().__init__(master, **kwargs)
        for i in range(8):  # Изменили с 7 на 8 для добавления новой кнопки
            self.grid_rowconfigure(i, weight=1)

        self.width = 60
        self.height = 60

        self.main_button = ctk.CTkButton(self, width=self.width, height=self.height, text="", command=lambda: show_function("main"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path("assets/icons/sidebar/house.png"),
                                                                app_color["light_blue"]), size=(40,40))))
        self.main_button.grid(row=0, column=0, padx=20, pady=20, sticky="we")

        self.expenses_button = ctk.CTkButton(self, width=self.width, height=self.height, text="", command=lambda: show_function("expenses"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path(
                "assets/icons/sidebar/money-transaction.png"), app_color["light_blue"]), size=(40,40))))
        self.expenses_button.grid(row=1, column=0, padx=20, pady=20, sticky="we")

        self.accounts_button = ctk.CTkButton(self, width=self.width, height=self.height, text="", command=lambda: show_function("accounts"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path(
                "assets/icons/sidebar/credit-card.png"), app_color["light_blue"]), size=(40,40))))
        self.accounts_button.grid(row=2, column=0, padx=20, pady=20, sticky="we")

        self.transactions_button = ctk.CTkButton(self, width=self.width, height=self.height, text="",
                                            command=lambda: show_function("transactions"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path(
                "assets/icons/sidebar/currency.png"), app_color["light_blue"]), size=(40, 40))))
        self.transactions_button.grid(row=3, column=0, padx=20, pady=20, sticky="we")

        # Новая кнопка настроек
        self.settings_button = ctk.CTkButton(self, width=self.width, height=self.height, text="", 
                                            command=lambda: show_function("settings"),
            image=(ctk.CTkImage(light_image=recolor_icon(resource_path(
                "assets/icons/sidebar/settings.png"), app_color["light_blue"]), size=(40, 40))))
        self.settings_button.grid(row=4, column=0, padx=20, pady=20, sticky="we")

        self.plus_button = ctk.CTkButton(self, width=self.width, height=self.height, text="",
                                         command=self.open_new_transaction,
                                         image=(ctk.CTkImage(light_image=recolor_icon(
                                             resource_path("assets/icons/sidebar/add.png"),
                                                app_color["light_blue"]), size=(40, 40))))
        self.plus_button.grid(row=5, column=0, padx=20, pady=20, sticky="swe")

        self.new_transaction = None

    def open_new_transaction(self):
        if self.new_transaction is None or not self.new_transaction.winfo_exists():
            self.new_transaction = NewTransactionWindow(self.master)
            self.new_transaction.attributes('-topmost', True)
        if self.new_transaction.winfo_exists():
            self.new_transaction.deiconify()

        self.new_transaction.update()
        self.new_transaction.focus()

        self.new_transaction.bind("<<DateSelected>>", lambda x: self.close_pop_up_window())

    def close_pop_up_window(self):
        self.new_transaction.destroy()