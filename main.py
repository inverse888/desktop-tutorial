import tkinter as tk
import warnings
import matplotlib.pyplot as plt
import customtkinter as ctk

# Полностью отключаем автоматическую установку фокуса для всех виджетов
original_focus_set = tk.Widget.focus_set
original_focus_force = tk.Widget.focus_force if hasattr(tk.Widget, 'focus_force') else None

def safe_focus_set(self):
    """Безопасная установка фокуса"""
    try:
        if self and self.winfo_exists():
            try:
                if self.winfo_ismapped():
                    original_focus_set(self)
            except:
                pass
    except (tk.TclError, RuntimeError, AttributeError):
        pass

def safe_focus_force(self):
    """Безопасная принудительная установка фокуса"""
    try:
        if self and self.winfo_exists():
            try:
                if self.winfo_ismapped():
                    if original_focus_force:
                        original_focus_force(self)
                    else:
                        original_focus_set(self)
            except:
                pass
    except (tk.TclError, RuntimeError, AttributeError):
        pass

# Применяем патчи
tk.Widget.focus_set = safe_focus_set
if original_focus_force:
    tk.Widget.focus_force = safe_focus_force

# Игнорируем предупреждения
warnings.filterwarnings("ignore")

from category_creation import resource_path
from sidebar import SideBar
from main_page import MainPage
from expenses_page import ExpensesPage
from accounts_page import AccountsPage
from transactions_page import TransactionsPage
from settings_page import SettingsPage


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.geometry("1600x900+200+100")
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
            "settings": SettingsPage(self.main_area)
        }
        self.show_page("main")
        
        self._update_lock = False
        self._pending_update = False

    def show_page(self, page_name: str) -> None:
        for page in self.pages.values():
            page.grid_remove()
        self.pages[page_name].grid(row=0, column=0, sticky="nsew")
        self.pages[page_name].update_idletasks()

    def on_close(self):
        plt.close('all')
        self.quit()
        self.destroy()

    def _perform_full_update(self):
        """Выполняет полное обновление всех страниц (оптимизированная версия)"""
        try:
            # Обновляем страницу счетов
            if hasattr(self.pages["accounts"], 'update_frame'):
                self.pages["accounts"].update_frame()
            
            # Обновляем список транзакций на странице счетов
            if hasattr(self.pages["accounts"], 'transactions_frame'):
                if hasattr(self.pages["accounts"].transactions_frame, 'update_frame'):
                    self.pages["accounts"].transactions_frame.update_frame()
            
            # Обновляем транзакции на странице транзакций
            if hasattr(self.pages["transactions"], 'update_transactions'):
                self.pages["transactions"].update_transactions()
            
            # Обновляем фильтр на странице транзакций
            if hasattr(self.pages["transactions"], 'update_accounts_filter'):
                self.pages["transactions"].update_accounts_filter()
            
            # Обновляем переводы
            if hasattr(self.pages["transactions"], 'update_transfers'):
                self.pages["transactions"].update_transfers()
            
            # Обновляем главную страницу (круговая диаграмма)
            if hasattr(self.pages["main"], 'update_transactions'):
                self.pages["main"].update_transactions()
            
            # Обновляем график расходов
            if hasattr(self.pages["expenses"], 'force_refresh'):
                self.pages["expenses"].force_refresh()
            
            # Обновляем список доходов
            if hasattr(self.pages["expenses"], 'income_frame'):
                if hasattr(self.pages["expenses"].income_frame, 'update_frame'):
                    self.pages["expenses"].income_frame.update_frame()
            
            # Обновляем категории расходов
            if hasattr(self.pages["expenses"], 'categories_frame'):
                if hasattr(self.pages["expenses"].categories_frame, 'update_categories'):
                    self.pages["expenses"].categories_frame.update_categories()
            
            # Принудительно обновляем отображение только один раз
            self.update_idletasks()
                
        except Exception as e:
            print(f"Ошибка при обновлении: {e}")

    def schedule_full_update(self):
        """Планирует полное обновление с debounce"""
        if self._update_lock:
            self._pending_update = True
            return
        
        self._update_lock = True
        self._pending_update = False
        
        self.after(200, self._execute_full_update)
    
    def _execute_full_update(self):
        """Выполняет запланированное обновление"""
        try:
            self._perform_full_update()
        finally:
            self._update_lock = False
            if self._pending_update:
                self._pending_update = False
                self.schedule_full_update()

    def update_transactions(self):
        """Обновляет транзакции (вызывается извне)"""
        self.schedule_full_update()

    def update_transfers(self):
        """Обновляет переводы (вызывается извне)"""
        self.schedule_full_update()

    def update_categories(self):
        """Обновляет категории (вызывается извне)"""
        self.schedule_full_update()

    def update_accounts_filter(self):
        """Обновляет фильтр счетов на странице транзакций"""
        if hasattr(self.pages, 'transactions') and hasattr(self.pages['transactions'], 'update_accounts_filter'):
            self.pages['transactions'].update_accounts_filter()

    def force_update_all(self):
        """Принудительное полное обновление всех страниц"""
        self.schedule_full_update()


if __name__ == '__main__':
    app = App()
    app.mainloop()