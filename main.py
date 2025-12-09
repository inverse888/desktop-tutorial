import matplotlib.pyplot as plt
import customtkinter as ctk

from category_creation import resource_path
from sidebar import SideBar
from main_page import MainPage
from expenses_page import ExpensesPage
from accounts_page import AccountsPage
from transactions_page import TransactionsPage
from settings_page import SettingsPage  # Добавляем импорт

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.geometry("1400x700+200+100")
        self.resizable(False, False)

        self.title("Система учёта финансов")
        ico_path = resource_path("assets/icons/asset-management.ico")
        self.iconbitmap(ico_path)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = SideBar(self, self.show_page, width=150)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.main_area = ctk.CTkFrame(self)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid(row=0, column=1, sticky="nsew")

        self.pages = {
            "main": MainPage(self.main_area),
            "expenses": ExpensesPage(self.main_area),
            "accounts": AccountsPage(self.main_area, self),
            "transactions": TransactionsPage(self.main_area),
            "settings": SettingsPage(self.main_area)  # Добавляем страницу настроек
        }
        self.show_page("main")

    def show_page(self, page_name: str) -> None:
        for page in self.pages.values():
            page.grid_remove()
        self.pages[page_name].grid(row=0, column=0, sticky="nsew")
        self.pages[page_name].update_idletasks()

    def on_close(self):
        plt.close('all')
        self.quit()
        self.destroy()

    def update_transactions(self):
        for page in self.pages.values():
            if hasattr(page, 'update_transactions'):
                page.update_transactions()

    def update_transfers(self):
        self.pages["accounts"].update_transfers()
        self.pages["transactions"].update_transfers()

    def update_categories(self):
        """Метод для обновления категорий во всех страницах"""
        for page in self.pages.values():
            if hasattr(page, 'update_categories'):
                page.update_categories()

if __name__ == '__main__':
    app = App()
    app.mainloop()