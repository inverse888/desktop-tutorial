import datetime
from PIL import Image
import customtkinter as ctk
from customtkinter import CTkFrame
from sqlalchemy import desc, func, cast, Date

from db_management import session, CategoriesTable, TransactionsTable
from pop_up_calendar import PopUpCalendar
from addition_classes import MainPagePie, PeriodButtons, recolor_icon, resource_path


def change_background(image_path, bg_color, lines_color):
    img = Image.open(image_path).convert("RGBA")
    new_background = Image.new("RGBA", img.size, bg_color)

    result = Image.alpha_composite(new_background, img)
    return result

def open_pop_up_calendar(frame_instance, two_dates: bool):
    if not frame_instance.pop_up_calendar.winfo_exists():
        frame_instance.pop_up_calendar = PopUpCalendar(two_dates)
        frame_instance.pop_up_calendar.attributes('-topmost', True)

    frame_instance.pop_up_calendar.deiconify()
    frame_instance.pop_up_calendar.update()
    frame_instance.pop_up_calendar.focus()

    frame_instance.pop_up_calendar.bind("<<DateSelected>>", lambda x: on_date_selected(frame_instance))

def on_date_selected(frame_instance):
    frame_instance.transaction_date = frame_instance.pop_up_calendar.frame.date_range

    if hasattr(frame_instance, 'update_text'):
        frame_instance.update_text()

    close_calendar(frame_instance)

def close_calendar(main_page_instance):
    main_page_instance.pop_up_calendar.destroy()

    main_page_instance.transaction_date = main_page_instance.pop_up_calendar.frame.date_range
    if None not in main_page_instance.transaction_date:
        main_page_instance.transaction_date.sort()

    if hasattr(main_page_instance, 'update_chart'):
        main_page_instance.update_chart(main_page_instance.transaction_date)

    if hasattr(main_page_instance, 'stats_frame'):
        if hasattr(main_page_instance.stats_frame, 'show_in_date_label'):
            main_page_instance.stats_frame.show_in_date_label(main_page_instance)


class CategoriesFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#949191")
        for i in range(5):
            self.grid_rowconfigure(i, weight=1)
        for i in range(3):
            self.grid_columnconfigure(i, weight=1)

        self.update_frame()

    def update_frame(self):
        for i, (cat, trans) in enumerate(session.query(CategoriesTable, TransactionsTable
                                ).join(TransactionsTable, TransactionsTable.category_id == CategoriesTable.category_id
                                ).order_by(desc(TransactionsTable.transaction_date_time)).all()):
            image = ctk.CTkLabel(self, text="", image=ctk.CTkImage(light_image=recolor_icon(resource_path(
                                 f"assets/{cat.icon_url}"), cat.colour),
                size=(40, 40)))
            image.grid(row=i, column=0, padx=(20, 10), pady=5, sticky="w")

            label = ctk.CTkLabel(self, text=cat.category_name, font=("Arial", 16),
                                    text_color="black")
            label.grid(row=i, column=1, padx=(10, 10), pady=5, sticky="nsew")

            amount = ctk.CTkLabel(self, text=f"{trans.amount:,.2f}", font=("Arial", 16),
                                    text_color="black")
            amount.grid(row=i, column=2, padx=(10, 20), pady=5, sticky="e")


class StatsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(fg_color="#aba6a6")
        self.grid_propagate(False)
        self.days_delta = 7

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=4)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.period_button = ctk.CTkButton(self, text="Траты за период", font=("Arial", 18, "bold"), height=50)
        self.period_button.grid(row=0, column=0, sticky="w", padx=20, pady=20)

        self.data_frame = CTkFrame(self, bg_color="#949191")
        self.data_frame.grid(row=0, column=1, sticky="e", padx=20, pady=(10, 20))

        self.date_label = ctk.CTkLabel(self.data_frame, font=("Arial", 24, "bold"))
        self.show_in_date_label(master)
        self.date_label.grid(sticky="nsew", padx=20, pady=20)

        self.results = (
            session.query(
                CategoriesTable.category_name,
                CategoriesTable.icon_url,
                CategoriesTable.colour,
                func.sum(TransactionsTable.amount).label("total_amount")
            )
            .join(TransactionsTable, TransactionsTable.category_id == CategoriesTable.category_id)
            .filter(
                TransactionsTable.transaction_type == 'Расход',
                TransactionsTable.transaction_date_time >=
                                        datetime.datetime.now() - datetime.timedelta(days=self.days_delta)
            )
            .group_by(CategoriesTable.category_id)
            .order_by(func.sum(TransactionsTable.amount).desc())
        ).all()
        categories_val = [row.total_amount for row in self.results]
        categories_labels = [row.category_name for row in self.results]
        categories_colors = [row.colour for row in self.results]


        self.pie = MainPagePie(self, categories_val, categories_labels, categories_colors, "")
        self.pie.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)

    def show_in_date_label(self, master):
        if master.transaction_date[0] == master.transaction_date[1]:
            self.date_label.configure(
                text=f"{str(master.transaction_date[0].day).zfill(2)}.{str(master.transaction_date[0].month).zfill(2)}."
                     f"{master.transaction_date[0].year}")

        elif (master.transaction_date[0].day != master.transaction_date[1].day
            and master.transaction_date[0].month == master.transaction_date[1].month):
            self.date_label.configure(
                text=f"{str(master.transaction_date[0].day).zfill(2)} - {str(master.transaction_date[1].day).zfill(2)}."
                     f"{str(master.transaction_date[1].month).zfill(2)}.{master.transaction_date[1].year}")

        elif master.transaction_date[0].year == master.transaction_date[1].year:
            self.date_label.configure(
                text=f"{str(master.transaction_date[0].day).zfill(2)}.{str(master.transaction_date[0].month).zfill(2)} - "
                     f"{str(master.transaction_date[1].day).zfill(2)}.{str(master.transaction_date[1].month).zfill(2)}."
                     f"{master.transaction_date[1].year}")

        else:
            self.date_label.configure(
                text=f"{str(master.transaction_date[0].day).zfill(2)}.{str(master.transaction_date[0].month).zfill(2)}."
                     f"{master.transaction_date[0].year} - "
                     f"{str(master.transaction_date[1].day).zfill(2)}.{str(master.transaction_date[1].month).zfill(2)}."
                     f"{master.transaction_date[1].year}")


class MainPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=20)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        today = datetime.date.today()
        self.transaction_date: list[datetime.date] | list[None] = [today - datetime.timedelta(days=6), today]

        self.stats_frame = StatsFrame(self)
        self.stats_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(10, 20))
        self.stats_frame.period_button.configure(command=lambda: open_pop_up_calendar(self, True))

        self.categories_frame = CategoriesFrame(self)
        self.categories_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(10, 20), pady=20)

        self.period_buttons = PeriodButtons(self)
        self.period_buttons.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=(20, 10))

        self.pop_up_calendar = PopUpCalendar(True)
        self.pop_up_calendar.withdraw()

    def update_chart(self, dates: list[datetime.date], period=None):
        date_from = dates[0]
        date_to = dates[1]
        results = (
            session.query(
                CategoriesTable.category_name,
                CategoriesTable.icon_url,
                CategoriesTable.colour,
                func.sum(TransactionsTable.amount).label("total_amount")
            )
            .join(TransactionsTable, TransactionsTable.category_id == CategoriesTable.category_id)
            .filter(
                TransactionsTable.transaction_type == 'Расход',
                cast(TransactionsTable.transaction_date_time, Date) >= date_from,
                cast(TransactionsTable.transaction_date_time, Date) <= date_to
            )
            .group_by(CategoriesTable.category_id)
            .order_by(func.sum(TransactionsTable.amount).desc())
            .all()
        )

        values = [float(row.total_amount) for row in results] 
        labels = [row.category_name for row in results]
        colors = [row.colour for row in results]

        self.stats_frame.pie.create_pie_chart(values, labels, colors, "")

    def update_delta(self, days):
        self.stats_frame.days_delta = days

        today = datetime.date.today()
        self.transaction_date = [today - datetime.timedelta(days=days), today]
        self.stats_frame.show_in_date_label(self)

    def update_transactions(self):
        self.update_chart(self.transaction_date, "Same")
        self.categories_frame.update_frame()

