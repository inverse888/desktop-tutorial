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

    from sqlalchemy import cast, Date
    expenses = session.query(TransactionsTable).filter(
        TransactionsTable.transaction_type == "Расход",
        cast(TransactionsTable.transaction_date_time, Date) >= start_date,
        cast(TransactionsTable.transaction_date_time, Date) <= end_date
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
    """Преобразует HEX цвет в RGB кортеж"""
    if not color:
        return (0, 0, 0)
    
    try:
        if color.startswith("#"):
            color = color.lstrip('#')
        
        if len(color) == 6:
            return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        elif len(color) == 3:
            return tuple(int(c*2, 16) for c in color)
        elif len(color) == 8:
            return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        else:
            return (0, 0, 0)
    except (ValueError, TypeError):
        return (0, 0, 0)

def name_to_hex(name: str):
    root = tk.Tk()
    root.withdraw()
    hex_color = root.winfo_rgb(name)
    root.destroy()
    return hex_color

def recolor_icon(image_path: str, fg_color: str, bg_color: str = None):
    """Перекрашивает иконку в заданный цвет"""
    if not fg_color:
        fg_color = "#144870"
    
    fg_rgb = hex_to_rgb(fg_color)
    bg_rgb = hex_to_rgb(bg_color) if bg_color else None

    try:
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
    except Exception as e:
        print(f"Ошибка при перекрашивании иконки {image_path}: {e}")
        return Image.open(image_path).convert("RGBA")

class PeriodButtons(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        for i in range(3):
            self.grid_columnconfigure(i, weight=1)

        self.selected_period = "week"
        self.selected_style = {"fg_color": "#08375c", "text_color" : "white",  "hover_color" : "#10304a"}
        self.deselected_style = {"fg_color": "#1f6aa5", "text_color" : "black", "hover_color" : "#144870"}
        
        self._update_lock = False

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
        if self._update_lock:
            return
        
        self._update_lock = True
        
        try:
            if period not in ["month", "week", "day"]:
                raise TypeError("Unexpected period")
            
            match period:
                case "day":
                    master.update_delta(0)
                case "week":
                    master.update_delta(6)
                case "month":
                    master.update_delta(30)
            
            master.after(50, lambda: master.update_chart(master.transaction_date, period))

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
        finally:
            master.after(100, lambda: setattr(self, '_update_lock', False))


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
        
        self.configure(width=750, height=550)
        
        self.fixed_width = 9
        self.fixed_height = 6
        self.fixed_dpi = 100
        
        self.fig, self.ax = plt.subplots(figsize=(self.fixed_width, self.fixed_height), dpi=self.fixed_dpi)
        self.fig.patch.set_facecolor('#949191')
        self.ax.set_facecolor('#949191')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        
        self.canvas.get_tk_widget().configure(
            width=int(self.fixed_width * self.fixed_dpi),
            height=int(self.fixed_height * self.fixed_dpi)
        )
        
        self.layout_params = {
            'tight_layout': {'pad': 2.5, 'rect': [-0.12, 0, 0.7, 1]},
            'subplots_adjust': {'left': -0.12, 'right': 0.7, 'bottom': 0.1, 'top': 0.9}
        }
        
        self.create_pie_chart(values, labels, colors, title)

    def apply_fixed_layout(self):
        try:
            self.update_idletasks()
            self.fig.tight_layout(**self.layout_params['tight_layout'])
            self.fig.subplots_adjust(**self.layout_params['subplots_adjust'])
            self.canvas.draw()
            self.canvas.flush_events()
            self.update_idletasks()
            if self.winfo_toplevel():
                self.winfo_toplevel().update_idletasks()
            self.canvas.get_tk_widget().update()
        except Exception as e:
            print(f"apply_fixed_layout error: {e}")

    def create_pie_chart(self, values, labels, colors, title):
        self.ax.clear()
        
        self.fig.set_size_inches(self.fixed_width, self.fixed_height, forward=True)
        self.fig.set_dpi(self.fixed_dpi)
        
        if self.ax.get_legend():
            self.ax.get_legend().remove()
        
        if not values:
            self.ax.text(
                0.5, 0.5, "Нет данных за выбранный период",
                fontsize=14, ha="center", va="center", transform=self.ax.transAxes,
                color="gray"
            )
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.axis('off')
        else:
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
            
            if other_value > 0:
                filtered_values.append(other_value)
                filtered_labels.append(f'Другие ({other_count})')
                filtered_colors.append('#CCCCCC')
            
            wedges, texts, autotexts = self.ax.pie(
                filtered_values,
                colors=filtered_colors,
                startangle=90,
                autopct=lambda pct: f'{pct:.1f}%' if pct >= 3 else '',
                pctdistance=0.7,
                textprops={'fontsize': 8, 'color': 'white', 'weight': 'bold'},
                radius=0.85
            )
            
            legend_labels = []
            for label, value in zip(filtered_labels, filtered_values):
                percentage = (value / total) * 100
                legend_labels.append(f'{label}: {value:,.2f} ({percentage:.1f}%)')
            
            self.ax.legend(
                wedges,
                legend_labels,
                title="Категории расходов",
                loc="center left",
                bbox_to_anchor=(0.87, 0.5),
                fontsize=8,
                frameon=True,
                facecolor='#f0f0f0',
                edgecolor='#cccccc',
                handlelength=1.5,
                handletextpad=0.5
            )
            
            self.ax.set_title(title, fontsize=11, fontweight='bold', pad=15)
            self.ax.axis('equal')
        
        self.fig.tight_layout(**self.layout_params['tight_layout'])
        self.fig.subplots_adjust(**self.layout_params['subplots_adjust'])
        
        self.canvas.draw()
        self.canvas.flush_events()


class ExpensesPageStackedBar(ctk.CTkFrame):
    def __init__(self, master, dates, title="", **kwargs):
        super().__init__(master, **kwargs)

        self.title = title
        self.master = master
        self._update_lock = False
        self._pending_update = False
        self._current_category_names = []
        
        self.data_dict = get_expense_data(dates[0], dates[1], "week")
        delta_days = (dates[1] - dates[0]).days + 1
        self.labels = [(dates[0] + datetime.timedelta(days=i)).strftime("%d") for i in range(delta_days)]

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

    def schedule_update(self):
        """Планирует отложенное обновление графика"""
        if self._update_lock:
            self._pending_update = True
            return
        
        self._update_lock = True
        self._pending_update = False
        
        self.after(50, self._perform_update)
    
    def _perform_update(self):
        """Выполняет обновление графика"""
        try:
            if self._current_category_names:
                self._show_multiple_categories_internal(self._current_category_names)
            else:
                self._create_stacked_bar_internal()
            
            self.canvas.draw()
            self.canvas.flush_events()
            
        except Exception as e:
            print(f"Ошибка при обновлении графика: {e}")
        finally:
            self._update_lock = False
            
            if self._pending_update:
                self._pending_update = False
                self.schedule_update()

    def _create_stacked_bar_internal(self):
        """Внутренний метод создания stacked bar"""
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

            self.ax.set_title("")
            self.ax.tick_params(axis='x', rotation=90)
            # Убираем легенду - не добавляем legend()

        self.canvas.draw()
        self.canvas.flush_events()

    def _show_multiple_categories_internal(self, category_names: list):
        """Внутренний метод показа нескольких категорий"""
        self.ax.clear()

        filtered_data = {}
        for cat_name in category_names:
            if cat_name in self.data_dict:
                filtered_data[cat_name] = self.data_dict[cat_name]
        
        if not filtered_data:
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
            return

        if len(self.labels) == 1:
            self._create_bar_for_multiple_categories_single_day(filtered_data)
        else:
            bottoms = np.zeros(len(self.labels))
            
            for category, info in filtered_data.items():
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
            
            self.ax.set_title("")
            self.ax.tick_params(axis='x', rotation=90)
            # Убираем легенду

        self.canvas.draw()
        self.canvas.flush_events()

    def create_stacked_bar(self):
        """Показывает все категории"""
        self._current_category_names = []
        self.schedule_update()

    def show_multiple_categories(self, category_names: list):
        """Показывает несколько выбранных категорий"""
        self._current_category_names = category_names.copy()
        self.schedule_update()

    def _create_bar_for_multiple_categories_single_day(self, filtered_data):
        """Создает горизонтальный бар-чарт для нескольких категорий за один день"""
        categories = list(filtered_data.keys())
        values = [info["values"][0] for info in filtered_data.values()]
        colors = [info["color"] for info in filtered_data.values()]
        
        sorted_items = sorted(zip(categories, values, colors), key=lambda x: x[1], reverse=True)
        if sorted_items:
            categories, values, colors = zip(*sorted_items)
        else:
            categories, values, colors = [], [], []
        
        y_pos = range(len(categories))
        bars = self.ax.barh(y_pos, values, color=colors, height=0.6)
        
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(categories, fontsize=10)
        self.ax.set_xlabel("Сумма расхода", fontsize=11)
        self.ax.set_title("")
        
        for i, (bar, value) in enumerate(zip(bars, values)):
            self.ax.text(value, bar.get_y() + bar.get_height()/2, 
                        f' {value:,.2f}', va='center', fontsize=9)
        
        self.ax.invert_yaxis()
        self.ax.grid(True, axis='x', alpha=0.3)

    def create_bar_for_single_day(self, one_cat: bool):
        """Создает график для одного дня"""
        self.ax.clear()

        categories = list(self.data_dict.keys())
        values = [info["values"][0] for info in self.data_dict.values()]
        colors = [info["color"] for info in self.data_dict.values()]

        self.ax.set_xlim(-0.5, 0.5) if one_cat else None
        bars = self.ax.bar(categories, values, color=colors, width=0.1)

        self.ax.set_ylim(0, max(values) * 1.2 if any(values) else 1)
        self.ax.tick_params(axis='x', rotation=0)
        self.ax.set_title("")

    def update_data(self, new_data, period, date_from, date_to):
        """Обновляет данные графика"""
        self.data_dict = new_data

        delta_days = (date_to - date_from).days + 1
        self.labels = [(date_from + datetime.timedelta(days=i)).strftime("%d") for i in range(delta_days)]

        self.ax.clear()
        
        if not any(info["values"] for info in new_data.values()):
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
            self._current_category_names = []
            self._create_stacked_bar_internal()
            self.canvas.draw()
            self.canvas.flush_events()