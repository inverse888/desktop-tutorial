import customtkinter as ctk
from datetime import date

from addition_classes import resource_path


class CalendarFrame(ctk.CTkFrame):
    def __init__(self, master, two_dates: bool, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#aba6a6")
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=2)
        for i in range(1, 8):
            self.grid_rowconfigure(i, weight=1)
        for i in range(7):
            self.grid_columnconfigure(i, weight=1)

        self.cur_year = date.today().year
        self.cur_month = date.today().month
        self.date_range = [None, None]
        self.two_dates = two_dates
        self.weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        self.months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

        # отображение месяца, года и стрелок перелистывания
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=7, sticky="nsew", padx=10, pady=10)
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.header_frame.grid_columnconfigure(2, weight=11)
        self.header_frame.grid_columnconfigure(3, weight=2)
        self.header_frame.grid_rowconfigure(0, weight=1)
        self.header_frame.grid_rowconfigure(1, weight=1)

        self.date_label = ctk.CTkLabel(self.header_frame, text_color='black', font=("Arial", 28),
                                       text=f"{self.months[self.cur_month - 1]} {self.cur_year}")
        self.date_label.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=10)

        self.left_month_button = ctk.CTkButton(self.header_frame, text_color="black", text="<", font=("Arial", 14),
                                               corner_radius=0, width=20, height=20, command=lambda: self.change_date("left"))
        self.left_month_button.grid(row=0, column=0, rowspan=2, sticky="e")

        self.right_month_button = ctk.CTkButton(self.header_frame, text_color="black", text=">", font=("Arial", 14),
                                                corner_radius=0, width=20, height=20, command=lambda: self.change_date("right"))
        self.right_month_button.grid(row=0, column=1, rowspan=2, sticky="w", padx=0, pady=10)

        self.top_year_button = ctk.CTkButton(self.header_frame, text_color="black", text="↑", font=("Arial", 14),
                                       corner_radius=0, width=20, height=20, command=lambda: self.change_date("up"))
        self.top_year_button.grid(row=0, column=6, sticky="s", padx=10, pady=0)

        self.bottom_year_button = ctk.CTkButton(self.header_frame, text_color="black", text="↓", font=("Arial", 14),
                                       corner_radius=0, width=20, height=20, command=lambda: self.change_date("bottom"))
        self.bottom_year_button.grid(row=1, column=6, sticky="n", padx=10, pady=0)


        # отображение названий дней недели
        for i, weekday in enumerate(self.weekdays):
            (ctk.CTkLabel(self, text=weekday, text_color='black')).grid(row=1, column=i)

        (ctk.CTkLabel(self, text="", text_color='black')).grid(row=7, column=6)

        self.days_buttons = []
        self.show_days_buttons()

    def show_days_buttons(self):
        if len(self.days_buttons) != 0:
            for button in self.days_buttons:
                button.destroy()

        first_day = date(self.cur_year, self.cur_month, 1)
        cur_row = 2
        cur_column = first_day.weekday()

        for day_id in range(1, self.days_in_month(self.cur_month, self.cur_year)+1):
            button = ctk.CTkButton(self, corner_radius=3, text=str(day_id), fg_color='transparent',
                       text_color='black', hover_color="blue")

            button.configure(command=lambda b=button, d=day_id: self.on_button_click(
                        b, date(self.cur_year, self.cur_month, d)))

            if (self.date_range[0] is not None and
                    date(self.cur_year, self.cur_month, day_id) == self.date_range[0]):
                button.configure(fg_color="blue")

            button.grid(row=cur_row, column=cur_column, padx=3, pady=5, sticky="nsew")
            self.days_buttons.append(button)

            cur_column += 1
            if cur_column > 6:
                cur_column = 0
                cur_row += 1

    def days_in_month(self, month: int = date.today().month, year: int = date.today().year) -> int:
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        current_month = date(year, month, 1)
        return (next_month - current_month).days

    def create_date_range(self, chosen_date):
        if self.date_range[0] is None:
            self.date_range[0] = chosen_date
        else:
            self.date_range[1] = chosen_date

    def on_button_click(self, button, chosen_date):
        self.create_date_range(chosen_date)

        current_color = button.cget("fg_color")
        new_color = "blue" if current_color != "blue" else "transparent"
        button.configure(fg_color=new_color)

        if not self.two_dates and self.date_range[0] is not None or self.date_range[1] is not None:
            self.event_generate("<<DateSelected>>")

    def change_date(self, direction: str):
        if direction == "left":
            if self.cur_month == 1:
                self.cur_month = 12
                self.cur_year -= 1
            else:
                self.cur_month -= 1
        elif direction == "right":
            if self.cur_month == 12:
                self.cur_month = 1
                self.cur_year += 1
            else:
                self.cur_month += 1
        elif direction == "up":
            self.cur_year += 1
        elif direction == "bottom":
            self.cur_year -= 1
        else:
            raise TypeError("Invalid direction")
        self.date_label.configure(text=f"{self.months[self.cur_month - 1]} {self.cur_year}")
        self.show_days_buttons()


class PopUpCalendar(ctk.CTkToplevel):
    def __init__(self, two_dates: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Календарь")
        self.geometry("400x400+1200+100")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.after(250, lambda: self.iconbitmap(resource_path("assets/icons/calendar.ico")))

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=8)
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Выберите диапазон дат", font=("Arial", 20, "bold"))
        self.label.grid(padx=5, pady=10)
        self.frame = CalendarFrame(self, two_dates)
        self.frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        self.frame.bind("<<DateSelected>>", self.bind("<<DateSelected>>"))

