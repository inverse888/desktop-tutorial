import os
import sys
from pathlib import Path

import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox
from PIL import Image, ImageColor

from addition_classes import ToggleButton, FormattedEntry, resource_path
from db_management import session, CategoriesTable
from transaction_creation import ButtonsFrame


def get_icon_names(folder_path: str) -> list[str]:
    icons = []
    full_path = resource_path(folder_path)

    if not os.path.exists(full_path):
        return []

    for filename in os.listdir(full_path):
        if filename.endswith(".png"):
            name = os.path.splitext(filename)[0]
            icons.append(name)
    return icons

categories_icons = get_icon_names("assets/icons/categories")

class IconsListFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.buttons_in_row = 3
        self.categories_icons = categories_icons
        self.selected_name = None

        self.configure(fg_color="#aba6a6")
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.categories_buttons: list[ToggleButton] = []

        for image_name in self.categories_icons:
            image = ctk.CTkImage(light_image=Image.open(resource_path(f"assets/icons/categories/{image_name}.png")), size=(40, 40))
            button = ToggleButton(self, text_color="black", text="", width=50, height=50, image=image,
                                  fg_color="transparent", command=lambda n=image_name: self.select_single(n))
            self.categories_buttons.append(button)
        self.update_display()
        master.color_entry.bind("<Return>", lambda e: self.update_icons_color(master.color_entry.get()))

    def select_single(self, selected_name):
        for btn, name in zip(self.categories_buttons, categories_icons):
            if name == selected_name:
                btn.select()
                self.selected_name = selected_name
            else:
                btn.deselect()

    def update_display(self):
        for i, button in enumerate(self.categories_buttons):
            row = (i // self.buttons_in_row) * 2
            col = i % self.buttons_in_row

            button.grid(row=row, column=col, padx=5, pady=(10, 0))

    def update_icons_color(self, color: str):
        if color.startswith('#') and len(color) == 7:
            for button, icon_name in zip(self.categories_buttons, self.categories_icons):
                new_icon = self.recolor_icon(f"assets/icons/categories/{icon_name}.png", color)
                button.configure(image=new_icon)
                button.image = new_icon

    @staticmethod
    def recolor_icon(path: str, color: str) -> ctk.CTkImage:
        img = Image.open(path).convert("RGBA")
        rgb = ImageColor.getrgb(color)

        r, g, b = Image.new("RGB", img.size, rgb).split()
        alpha = img.getchannel("A")
        recolored = Image.merge("RGBA", (r, g, b, alpha))
        return ctk.CTkImage(light_image=recolored, size=(40, 40))


class CategoryCreationPage(ctk.CTkToplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("600x400+100+100")
        self.title("Создание категории")
        self.configure(fg_color="#aba6a6")

        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(250, lambda: self.iconbitmap("assets/icons/options.ico"))

        self.master = master

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Название: ", placeholder_text_color="grey")
        self.name_entry.grid(row=1, column=1, sticky="nwe", padx=10, pady=(10, 0))

        self.color_entry = FormattedEntry(self, accepted="color",
                                          placeholder_text="Цвет: ", placeholder_text_color="grey")
        self.color_entry.grid(row=1, column=1, sticky="swe", padx=10, pady=(0, 10))

        self.icons_list = IconsListFrame(self)
        self.icons_list.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=10, pady=10)

        self.add_category_button = ctk.CTkButton(self, text="Добавить", text_color="black", font=("Arial", 18),
                                                 command=self.add_category)
        self.add_category_button.grid(row=3, column=1, sticky="nsew", padx=10, pady=10)

        self.exp_inc_buttons = ButtonsFrame(self, income_button_text="Доход", expenses_button_text="Расход")
        self.exp_inc_buttons.grid(row=2, column=1, sticky="ew", padx=10, pady=10)

        self.color_entry.bind("<Return>", lambda e: self.apply_color_to_icons(e))

    def add_category(self):
        new_name = self.name_entry.get()
        new_category_type = self.exp_inc_buttons.status
        new_icon_name = self.icons_list.selected_name
        new_color = self.color_entry.get()

        if not new_icon_name:
            CTkMessagebox.messagebox(title="Ошибка!", text="Выберите иконку для категории!")
            return
        if not new_name:
            CTkMessagebox.messagebox(title="Ошибка!", text="Введите название категории!")
            return
        if not new_color:
            CTkMessagebox.messagebox(title="Ошибка!", text="Укажите цвет для категории!")
            return

        existing = session.query(CategoriesTable).filter_by(category_name=new_name).first()
        if existing:
            CTkMessagebox.messagebox(title="Ошибка!", text="Категория с таким названием уже существует!")
            return

        category = CategoriesTable(
            category_name=new_name,
            transaction_type=new_category_type,
            colour=new_color,
            icon_url=f"icons/categories/{new_icon_name}.png"
        )
        session.add(category)
        session.commit()

        # Обновляем категории в главном приложении
        if hasattr(self.master, 'update_categories'):
            self.master.update_categories()
        elif hasattr(self.master.master, 'update_categories'):
            self.master.master.update_categories()
            
        self.destroy()

    def on_close(self):
        self.destroy()

    def apply_color_to_icons(self, event=None):
        color = self.color_entry.get()
        if color.startswith("#"):
            self.icons_list.update_icons_color(color)
        else:
            print("Неверный формат цвета")