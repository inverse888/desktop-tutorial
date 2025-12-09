import datetime
import os
import sys
import tkinter as tk
from pathlib import Path

import numpy as np

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image

from db_management import session, CategoriesTable, TransactionsTable

def to_path_obj(relative_path: str) -> Path:
    parts = relative_path.split('/')
    return Path(parts[0]).joinpath(*parts[1:])

def resource_path(relative_path: str):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, to_path_obj(relative_path))

def get_expense_data(start_date, end_date, period: str):
    categories = {c.category_id: {"name": c.category_name, "color": c.colour}
                  for c in session.query(CategoriesTable).all()}

    expenses = session.query(TransactionsTable).filter(
        TransactionsTable.transaction_type == "Расход",
        TransactionsTable.transaction_date_time >= start_date,
        TransactionsTable.transaction_date_time <= end_date
    ).all()

    days = (end_date - start_date).days + 1

    result = {}
    for t in expenses:
        category = categories.get(t.category_id)
        if not category:
            continue

        cat_name = category["name"]
        cat_color = category["color"]
        day_index = (t.transaction_date_time.date() - start_date).days


        if cat_name not in result:
            result[cat_name] = {
                "color": cat_color,
                "values": [0.0] * days
            }
        if 0 <= day_index < days:
            result[cat_name]["values"][day_index] += float(t.amount)
    return result

app_color = {
    "light_blue" : "#90abd1",
    "dark_blue" : "#08375c",
    "blue" : "#1f6aa5"
}

def hex_to_rgb(color: str):
    if color.startswith("#"):
        color = color.lstrip('#')
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    else:
        root = tk.Tk()
        root.withdraw()
        rgb_color = root.winfo_rgb(color)
        root.destroy()
        return tuple(v // 256 for v in rgb_color)

def name_to_hex(name: str):
    root = tk.Tk()
    root.withdraw()
    hex_color = root.winfo_rgb(name)
    root.destroy()
    return hex_color

def recolor_icon(image_path: str, fg_color: str, bg_color: str = None):
    fg_rgb = hex_to_rgb(fg_color)
    bg_rgb = hex_to_rgb(bg_color) if bg_color else None

    img = Image.open(image_path).convert("RGBA")
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                if bg_rgb:
                    pixels[x, y] = (*bg_rgb, 255)
            else:
                pixels[x, y] = (*fg_rgb, a)
    return img

class PeriodButtons(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        for i in range(3):
            self.grid_columnconfigure(i, weight=1)

        self.selected_period = "week"
        self.selected_style = {"fg_color": "#08375c", "text_color" : "white",  "hover_color" : "#10304a"}
        self.deselected_style = {"fg_color": "#1f6aa5", "text_color" : "black", "hover_color" : "#144870"}

        self.month_button = ctk.CTkButton(self, text="За месяц",
                                          command=lambda: self.toggle(master, "month"),
                                          **self.deselected_style)
        self.week_button = ctk.CTkButton(self, text="За неделю",
                                         command=lambda: self.toggle(master, "week"),
                                         **self.selected_style)
        self.day_button = ctk.CTkButton(self, text="За день",
                                        command=lambda: self.toggle(master, "day"),
                                        **self.deselected_style)

        self.period_buttons = [self.month_button, self.week_button, self.day_button]

        for i, bnnt in enumerate(self.period_buttons):
            bnnt.grid(row=0, column=i, sticky="nsew", padx=20, pady=(20, 10))

    def toggle(self, master, period: str):
        if period not in ["month", "week", "day"]:
            raise TypeError("Unexpected period")
        match period:
            case "day":
                master.update_delta(0)
            case "week":
                master.update_delta(6)
            case "month":
                master.update_delta(30)
        master.update_chart(master.transaction_date, period)

        if period == self.selected_period:
            return
        self.selected_period = period

        if period == "month":
            self.month_button.configure(**self.selected_style)
            self.week_button.configure(**self.deselected_style)
            self.day_button.configure(**self.deselected_style)
        elif period == "week":
            self.month_button.configure(**self.deselected_style)
            self.week_button.configure(**self.selected_style)
            self.day_button.configure(**self.deselected_style)
        else:
            self.month_button.configure(**self.deselected_style)
            self.week_button.configure(**self.deselected_style)
            self.day_button.configure(**self.selected_style)


class FormattedEntry(ctk.CTkEntry):
    def __init__(self, master, accepted: str, formatting=True, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(validate="key", validatecommand=(self.register(self._validate_input), '%P'))

        self.formatting = formatting
        self.amount = 0.0
        self.accepted = accepted
        self.bind_var = "<Return>" if self.accepted == "number" else "<FocusIn>"

        self.bind(self.bind_var, self._update_display)

    def _validate_input(self, text: str) -> bool:
        if self.accepted == "number":
            if text == "":
                return True
            if text.count(".") > 1:
                return False
            if text.startswith('.'):
                return False

            parts = text.split('.')
            for part in parts:
                if part and not part.isdigit():
                    return False

            return text.isdigit() or "." in text or text == ""

        elif self.accepted == "color":
            if text.startswith("#"):
                text = text[1:]
            return all(c in '0123456789ABCDEFabcdef' for c in text)

        return True


    def _update_display(self, event=None):
        self.original_text = self.get()
        self.unbind(self.bind_var)

        self.configure(validate="none")
        self.delete(0, "end")

        new_text = self._format_text(self.original_text) if self.formatting else self.original_text
        self.insert(0, new_text)

        self.configure(validate="key")
        self.bind(self.bind_var, self._update_display)

    def _format_text(self, text):
        self.amount = text
        if self.accepted == "number":
            return f"{float(text):,.2f}"
        elif self.accepted == "color":
            if not text.startswith('#'):
                return f"#{text}"
        return text

class ToggleButton(ctk.CTkButton):
    def __init__(self, master, command=None, **kwargs):
        self.is_selected = False
        self.default_color = kwargs.pop("fg_color", app_color["blue"])
        self.selected_color = kwargs.pop("selected_color", app_color["dark_blue"])
        super().__init__(master, fg_color=self.default_color, **kwargs)

        self.configure(command=self.toggle)
        self.custom_command = command

    def toggle(self):
        if not self.is_selected:
            self.select()
            if self.custom_command:
                self.custom_command()

    def select(self):
        self.is_selected = True
        self.configure(fg_color=self.selected_color)

    def deselect(self):
        self.is_selected = False
        self.configure(fg_color=self.default_color)


class MainPagePie(ctk.CTkFrame):
    def __init__(self, master, values, labels, colors, title, **kwargs):
        super().__init__(master, **kwargs)

        self.values = values
        self.labels = labels
        self.colors = colors
        self.title = title

        self.configure(fg_color="#949191")
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(7, 5), dpi=110)
        self.fig.patch.set_facecolor('#949191')
        self.ax.set_facecolor('#949191')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.create_pie_chart(values, labels, colors, title)

    def create_pie_chart(self, values, labels, colors, title):
        self.ax.clear()
        
        if not values:
            self.ax.text(
                0.5, 0.5, "Нет данных за выбранный период",
                fontsize=14, ha="center", va="center", transform=self.ax.transAxes,
                color="gray"
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])
        else:
            # Преобразуем decimal.Decimal в float
            values_float = [float(value) for value in values]
            total = sum(values_float)
            threshold = total * 0.02
            
            filtered_values = []
            filtered_labels = []
            filtered_colors = []
            other_value = 0.0
            other_count = 0
            
            for value, label, color in zip(values_float, labels, colors):
                if value >= threshold:
                    filtered_values.append(value)
                    filtered_labels.append(label)
                    filtered_colors.append(color)
                else:
                    other_value += value
                    other_count += 1
            
            # Добавляем категорию "Другие" если есть мелкие сегменты
            if other_value > 0:
                filtered_values.append(other_value)
                filtered_labels.append(f'Другие ({other_count})')
                filtered_colors.append('#CCCCCC')
            
            # Создаем диаграмму без подписей, но с процентами
            wedges, texts, autotexts = self.ax.pie(
                filtered_values,
                colors=filtered_colors,
                startangle=90,
                autopct=lambda pct: f'{pct:.1f}%' if pct >= 3 else '',
                pctdistance=0.8,
                textprops={'fontsize': 9, 'color': 'white', 'weight': 'bold'}
            )
            
            # Создаем легенду с подробной информацией
            legend_labels = []
            for label, value in zip(filtered_labels, filtered_values):
                percentage = (value / total) * 100
                legend_labels.append(f'{label}: {value:,.2f} ({percentage:.1f}%)')
            
            # Размещаем легенду справа от диаграммы
            self.ax.legend(
                wedges,
                legend_labels,
                title="Категории расходов",
                loc="center left",
                bbox_to_anchor=(1.1, 0, 0.5, 1),
                fontsize=9
            )
            
            self.ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
            self.ax.axis('equal')
        
        self.fig.tight_layout()
        self.canvas.draw()


class ExpensesPageStackedBar(ctk.CTkFrame):
    def __init__(self, master, dates, title="", **kwargs):
        super().__init__(master, **kwargs)

        self.title = title
        self.master = master
        self.data_dict = get_expense_data(dates[0], dates[1], "week")

        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=6)
        self.labels = [(start_date + datetime.timedelta(days=i)).strftime("%d") for i in range(7)]

        self.configure(fg_color="#949191")
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.fig.patch.set_facecolor(self.cget("bg_color"))
        self.ax.set_facecolor(self.cget("bg_color"))
        for spine in self.ax.spines.values():
            spine.set_color(self.cget("bg_color"))

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.create_stacked_bar()
        self.canvas.get_tk_widget().grid(row=0, column=0)

    def show_single_category(self, category_name: str):
        self.ax.clear()

        if not category_name in self.data_dict.keys():
            self.ax.set_facecolor(self.cget("bg_color"))
            for spine in self.ax.spines.values():
                spine.set_color(self.cget("bg_color"))

            self.ax.text(
                0.5, 0.5, "Нет данных за выбранный период",
                fontsize=14, ha="center", va="center", transform=self.ax.transAxes,
                color="gray"
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.draw()
        else:
            bottoms = np.zeros(len(self.labels))
            info = self.data_dict[category_name]
            values = info["values"]
            color = info["color"]

            self.ax.bar(
                self.labels,
                values,
                bottom=bottoms,
                label=category_name,
                color=color,
                width=0.5
            )

            self.ax.set_title(self.title)
            self.ax.tick_params(axis='x', rotation=90)

        self.canvas.draw()

    def create_stacked_bar(self):
        self.ax.clear()

        if len(self.labels) == 1:
            self.create_bar_for_single_day(len(self.data_dict) == 1)
        else:
            bottoms = np.zeros(len(self.labels))

            for category, info in self.data_dict.items():
                values = info["values"]
                color = info["color"]
                self.ax.bar(
                    self.labels,
                    values,
                    bottom=bottoms,
                    label=category,
                    color=color,
                    width=0.5
                )
                bottoms += np.array(values)

            self.ax.set_title(self.title)
            self.ax.tick_params(axis='x', rotation=90)

        self.canvas.draw()

    def create_bar_for_single_day(self, one_cat: bool):
        self.ax.clear()

        categories = list(self.data_dict.keys())
        values = [info["values"][0] for info in self.data_dict.values()]
        colors = [info["color"] for info in self.data_dict.values()]

        self.ax.set_xlim(-0.5, 0.5) if one_cat else None
        bars = self.ax.bar(categories, values, color=colors, width=0.1)

        self.ax.set_ylim(0, max(values) * 1.2 if any(values) else 1)
        self.ax.tick_params(axis='x', rotation=0)

    def update_data(self, new_data, period, date_from, date_to):
        self.data_dict = new_data

        delta_days = (date_to - date_from).days + 1
        self.labels = [(date_from + datetime.timedelta(days=i)).strftime("%d") for i in range(delta_days)]

        if not any(info["values"] for info in new_data.values()):
            self.ax.clear()
            self.ax.set_facecolor(self.cget("bg_color"))
            for spine in self.ax.spines.values():
                spine.set_color(self.cget("bg_color"))

            self.ax.text(
                0.5, 0.5, "Нет данных за выбранный период",
                fontsize=14, ha="center", va="center", transform=self.ax.transAxes,
                color="gray"
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.draw()
        else:
            self.create_stacked_bar()