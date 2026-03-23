import os
import sys
import shutil
from pathlib import Path
import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox
from sqlalchemy import func
from PIL import Image, ImageDraw, ImageColor
import tkinter.messagebox as tkmsg

from db_management import session, CategoriesTable, TransactionsTable
from addition_classes import recolor_icon, resource_path
from category_creation import CategoryCreationPage, get_icon_names


class IconsManagementFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="#aba6a6")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="Управление иконками", 
                                       font=("Arial", 24, "bold"), text_color="black")
        self.title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        self.icons_info_label = ctk.CTkLabel(self, text="", font=("Arial", 12), text_color="black")
        self.icons_info_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))
        
        self.add_icons_button = ctk.CTkButton(self, text="Добавить иконки", font=("Arial", 16), 
                                             text_color="black", command=self.add_icons_from_files, height=40)
        self.add_icons_button.grid(row=0, column=0, sticky="e", padx=20, pady=(20, 10))
        
        self.icons_preview_frame = ctk.CTkScrollableFrame(self, fg_color="#949191")
        self.icons_preview_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.icons_preview_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        self.update_icons_info()
        self.update_icons_preview()

    def update_icons_info(self):
        icons_path = resource_path("assets/icons/categories")
        if os.path.exists(icons_path):
            icons = [f for f in os.listdir(icons_path) if f.endswith('.png')]
            self.icons_info_label.configure(text=f"Текущее количество иконок: {len(icons)}")
        else:
            self.icons_info_label.configure(text="Папка с иконками не найдена")

    def update_icons_preview(self):
        for widget in self.icons_preview_frame.winfo_children():
            widget.destroy()
        
        icons_path = resource_path("assets/icons/categories")
        if not os.path.exists(icons_path):
            no_icons_label = ctk.CTkLabel(self.icons_preview_frame, text="Папка с иконками не найдена", 
                                        font=("Arial", 16), text_color="black")
            no_icons_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
            return
        
        icons = [f for f in os.listdir(icons_path) if f.endswith('.png')]
        icons.sort()
        
        if not icons:
            no_icons_label = ctk.CTkLabel(self.icons_preview_frame, text="Нет иконок для отображения", 
                                        font=("Arial", 16), text_color="black")
            no_icons_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
            return
        
        columns = 5
        for i, icon_file in enumerate(icons):
            row = i // columns
            col = i % columns
            
            icon_path = os.path.join(icons_path, icon_file)
            try:
                icon_container = ctk.CTkFrame(self.icons_preview_frame, fg_color="#d9d9d9",
                                            corner_radius=12, border_width=2, border_color="#4a4a4a")
                icon_container.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
                icon_container.grid_propagate(False)
                icon_container.configure(width=160, height=210)
                icon_container.grid_columnconfigure(0, weight=1)
                
                inner_container = ctk.CTkFrame(icon_container, fg_color="transparent")
                inner_container.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
                inner_container.grid_columnconfigure(0, weight=1)
                inner_container.grid_rowconfigure(0, weight=0)
                inner_container.grid_rowconfigure(1, weight=0)
                inner_container.grid_rowconfigure(2, weight=1)
                
                original_image = Image.open(icon_path)
                resized_image = original_image.resize((80, 80), Image.Resampling.LANCZOS)
                
                if original_image.mode == 'RGBA':
                    final_image = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
                    final_image.paste(resized_image, (0, 0), resized_image)
                else:
                    final_image = resized_image
                
                icon_image = ctk.CTkImage(light_image=final_image, size=(80, 80), dark_image=final_image)
                
                icon_label = ctk.CTkLabel(inner_container, image=icon_image, text="")
                icon_label.grid(row=0, column=0, pady=(15, 8))
                icon_label.image = icon_image
                
                icon_name = icon_file.replace('.png', '')
                name_label = ctk.CTkLabel(inner_container, text=icon_name, font=("Arial", 12, "bold"),
                                        text_color="black", wraplength=140, justify="center")
                name_label.grid(row=1, column=0, pady=(5, 12), sticky="ew")
                
                buttons_frame = ctk.CTkFrame(inner_container, fg_color="transparent")
                buttons_frame.grid(row=2, column=0, pady=(0, 15), sticky="ew")
                buttons_frame.grid_columnconfigure(0, weight=1)
                buttons_frame.grid_columnconfigure(1, weight=0)
                buttons_frame.grid_columnconfigure(2, weight=1)
                
                rename_button = ctk.CTkButton(buttons_frame, text="✏️", width=48, height=48,
                                            font=("Arial", 20), fg_color="#4CAF50", hover_color="#45a049",
                                            text_color="white", corner_radius=10, border_width=0)
                rename_button.configure(command=lambda f=icon_file, n=icon_name: self._rename_icon(f, n))
                rename_button.grid(row=0, column=0, padx=5)
                
                empty_label = ctk.CTkLabel(buttons_frame, text="", width=12)
                empty_label.grid(row=0, column=1)
                
                delete_button = ctk.CTkButton(buttons_frame, text="🗑️", width=48, height=48,
                                            font=("Arial", 20), fg_color="#FF6B6B", hover_color="#FF5252",
                                            text_color="white", corner_radius=10, border_width=0)
                delete_button.configure(command=lambda f=icon_file: self._delete_icon(f))
                delete_button.grid(row=0, column=2, padx=5)
                
            except Exception as e:
                print(f"Ошибка загрузки иконки {icon_file}: {e}")
                continue
        
        self.update_icons_info()
        self._update_category_creation_icons()

    def _rename_icon(self, icon_filename, old_name):
        rename_window = ctk.CTkToplevel(self)
        rename_window.title("Переименование иконки")
        rename_window.geometry("550x650")
        rename_window.resizable(False, False)
        rename_window.transient(self)
        rename_window.grab_set()
        
        rename_window.grid_columnconfigure(0, weight=1)
        rename_window.grid_rowconfigure(0, weight=1)
        
        main_container = ctk.CTkFrame(rename_window, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)
        
        icons_path = resource_path("assets/icons/categories")
        icon_path = os.path.join(icons_path, icon_filename)
        
        try:
            original_image = Image.open(icon_path)
            resized_image = original_image.resize((100, 100), Image.Resampling.LANCZOS)
            
            if original_image.mode == 'RGBA':
                final_image = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
                final_image.paste(resized_image, (0, 0), resized_image)
            else:
                final_image = resized_image
            
            icon_image = ctk.CTkImage(light_image=final_image, size=(100, 100), dark_image=final_image)
            icon_display = ctk.CTkLabel(main_container, image=icon_image, text="")
            icon_display.grid(row=0, column=0, pady=(30, 15))
            icon_display.image = icon_image
        except:
            icon_display = ctk.CTkLabel(main_container, text="🖼️", font=("Arial", 80))
            icon_display.grid(row=0, column=0, pady=(30, 15))
        
        info_label = ctk.CTkLabel(main_container, text="Переименование иконки", font=("Arial", 20, "bold"), justify="center")
        info_label.grid(row=1, column=0, pady=(0, 10))
        
        old_name_label = ctk.CTkLabel(main_container, text=f"Текущее имя: '{old_name}'", 
                                     font=("Arial", 16), text_color="#4CAF50", justify="center")
        old_name_label.grid(row=2, column=0, pady=(0, 15))
        
        name_entry = ctk.CTkEntry(main_container, placeholder_text="Введите новое имя", font=("Arial", 16), width=400, height=50)
        name_entry.grid(row=3, column=0, pady=15, padx=40)
        name_entry.insert(0, old_name)
        name_entry.select_range(0, 'end')
        name_entry.focus()
        
        warning_label = ctk.CTkLabel(main_container, text="⚠ Изменение имени иконки затронет категории,\nиспользующие эту иконку.",
                                    font=("Arial", 12), text_color="#FF6B6B", justify="center")
        warning_label.grid(row=4, column=0, pady=(20, 25))
        
        spacer = ctk.CTkFrame(main_container, fg_color="transparent", height=30)
        spacer.grid(row=5, column=0, sticky="ew", pady=10)
        
        buttons_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        buttons_frame.grid(row=6, column=0, padx=40, pady=(0, 40), sticky="ew")
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        def confirm_rename():
            new_name = name_entry.get().strip()
            if not new_name:
                self._show_error_dialog("Ошибка", "Имя не может быть пустым!")
                return
            
            invalid_chars = r'<>:"/\|?*'
            if any(c in invalid_chars for c in new_name):
                self._show_error_dialog("Ошибка", "Имя содержит недопустимые символы!")
                return
            
            success, message = self._perform_rename(icon_filename, new_name)
            
            if success:
                rename_window.destroy()
                self._show_success_dialog("Успех", message)
                self.update_icons_preview()
                self._update_all_categories_in_app()
            else:
                self._show_error_dialog("Ошибка", message)
        
        def cancel_rename():
            rename_window.destroy()
        
        ok_button = ctk.CTkButton(buttons_frame, text="Да, изменить", command=confirm_rename,
                                 font=("Arial", 16, "bold"), height=52, width=200,
                                 fg_color="#4CAF50", hover_color="#45a049", corner_radius=8)
        ok_button.grid(row=0, column=0, padx=15, pady=10)
        
        cancel_button = ctk.CTkButton(buttons_frame, text="Отмена", command=cancel_rename,
                                     font=("Arial", 16, "bold"), height=52, width=200,
                                     fg_color="#FF6B6B", hover_color="#FF5252", corner_radius=8)
        cancel_button.grid(row=0, column=1, padx=15, pady=10)
        
        name_entry.bind("<Return>", lambda e: confirm_rename())
        
        rename_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - rename_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - rename_window.winfo_height()) // 2
        rename_window.geometry(f"+{x}+{y}")

    def _perform_rename(self, old_filename, new_name):
        icons_path = resource_path("assets/icons/categories")
        old_path = os.path.join(icons_path, old_filename)
        new_filename = f"{new_name}.png"
        new_path = os.path.join(icons_path, new_filename)
        
        if os.path.exists(new_path):
            return False, f"Иконка с именем '{new_name}' уже существует!"
        
        try:
            os.rename(old_path, new_path)
            
            old_icon_url = f"icons/categories/{old_filename.replace('.png', '')}.png"
            new_icon_url = f"icons/categories/{new_name}.png"
            
            categories = session.query(CategoriesTable).filter(CategoriesTable.icon_url == old_icon_url).all()
            
            if categories:
                for category in categories:
                    category.icon_url = new_icon_url
                session.commit()
                return True, f"Иконка переименована в '{new_name}'. Обновлено {len(categories)} категорий."
            else:
                return True, f"Иконка переименована в '{new_name}'."
        except Exception as e:
            session.rollback()
            return False, f"Не удалось переименовать: {str(e)}"

    def _delete_icon(self, icon_filename):
        icon_name = icon_filename.replace('.png', '')
        icon_url = f"icons/categories/{icon_name}.png"
        categories_using = session.query(CategoriesTable).filter(CategoriesTable.icon_url == icon_url).all()
        
        if categories_using:
            warning_text = f"Иконка '{icon_name}' используется в {len(categories_using)} категориях:\n\n"
            for cat in categories_using[:5]:
                warning_text += f"• {cat.category_name} ({cat.transaction_type})\n"
            if len(categories_using) > 5:
                warning_text += f"...и еще {len(categories_using) - 5} категориях"
            warning_text += "\n\nУдаление иконки может нарушить отображение этих категорий."
            self._show_warning_dialog("Невозможно удалить иконку", warning_text)
            return
        
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Подтверждение удаления")
        confirm_window.geometry("550x380")
        confirm_window.resizable(False, False)
        confirm_window.transient(self)
        confirm_window.grab_set()
        
        confirm_window.grid_columnconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(1, weight=0)
        
        main_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        main_frame.grid_columnconfigure(0, weight=1)
        
        icon_label = ctk.CTkLabel(main_frame, text="❓", font=("Arial", 56))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        confirm_text = ctk.CTkLabel(main_frame, text="Вы уверены, что хотите удалить иконку?", 
                                   font=("Arial", 18, "bold"), justify="center")
        confirm_text.grid(row=1, column=0, pady=(0, 10))
        
        icon_name_label = ctk.CTkLabel(main_frame, text=f"'{icon_name}'", font=("Arial", 20, "bold"),
                                      text_color="#FF6B6B", justify="center")
        icon_name_label.grid(row=2, column=0, pady=(0, 20))
        
        warning_text = ctk.CTkLabel(main_frame, text="Это действие нельзя отменить!", 
                                   font=("Arial", 14), text_color="#FF6B6B", justify="center")
        warning_text.grid(row=3, column=0, pady=10)
        
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=4, column=0, pady=30)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        def confirm_delete():
            try:
                icons_path = resource_path("assets/icons/categories")
                file_path = os.path.join(icons_path, icon_filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    confirm_window.destroy()
                    self._show_success_dialog("Успех", f"Иконка '{icon_name}' успешно удалена")
                    self.update_icons_preview()
            except Exception as e:
                confirm_window.destroy()
                self._show_error_dialog("Ошибка", f"Не удалось удалить иконку: {str(e)}")
        
        def cancel_delete():
            confirm_window.destroy()
        
        yes_button = ctk.CTkButton(buttons_frame, text="Да, удалить", command=confirm_delete,
                                  font=("Arial", 16, "bold"), fg_color="#FF6B6B", hover_color="#FF5252", height=45, width=150)
        yes_button.grid(row=0, column=0, padx=10)
        
        no_button = ctk.CTkButton(buttons_frame, text="Отмена", command=cancel_delete,
                                 font=("Arial", 16, "bold"), height=45, width=150)
        no_button.grid(row=0, column=1, padx=10)
        
        confirm_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - confirm_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - confirm_window.winfo_height()) // 2
        confirm_window.geometry(f"+{x}+{y}")

    def _show_warning_dialog(self, title, message):
        warning_window = ctk.CTkToplevel(self)
        warning_window.title(title)
        warning_window.geometry("650x500")
        warning_window.resizable(False, False)
        warning_window.transient(self)
        warning_window.grab_set()
        
        warning_window.grid_columnconfigure(0, weight=1)
        warning_window.grid_rowconfigure(0, weight=1)
        warning_window.grid_rowconfigure(1, weight=0)
        
        text_frame = ctk.CTkFrame(warning_window, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        icon_label = ctk.CTkLabel(text_frame, text="⚠️", font=("Arial", 56))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        error_text = ctk.CTkTextbox(text_frame, wrap="word", font=("Arial", 14), height=250, width=500, activate_scrollbars=True)
        error_text.grid(row=1, column=0, sticky="nsew", pady=10)
        error_text.insert("1.0", message)
        error_text.configure(state="disabled")
        
        ok_button = ctk.CTkButton(warning_window, text="OK", command=warning_window.destroy,
                                 font=("Arial", 16, "bold"), height=45, width=150)
        ok_button.grid(row=1, column=0, pady=30)
        
        warning_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - warning_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - warning_window.winfo_height()) // 2
        warning_window.geometry(f"+{x}+{y}")

    def _show_success_dialog(self, title, message):
        success_window = ctk.CTkToplevel(self)
        success_window.title(title)
        success_window.geometry("600x350")
        success_window.resizable(False, False)
        success_window.transient(self)
        success_window.grab_set()
        
        success_window.grid_columnconfigure(0, weight=1)
        success_window.grid_rowconfigure(0, weight=1)
        success_window.grid_rowconfigure(1, weight=0)
        
        content_frame = ctk.CTkFrame(success_window, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        content_frame.grid_columnconfigure(0, weight=1)
        
        icon_label = ctk.CTkLabel(content_frame, text="✅", font=("Arial", 56))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        success_text = ctk.CTkLabel(content_frame, text=message, font=("Arial", 16),
                                   wraplength=500, justify="center")
        success_text.grid(row=1, column=0, pady=10)
        
        ok_button = ctk.CTkButton(success_window, text="OK", command=success_window.destroy,
                                 font=("Arial", 16, "bold"), height=45, width=150)
        ok_button.grid(row=1, column=0, pady=30)
        
        success_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - success_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - success_window.winfo_height()) // 2
        success_window.geometry(f"+{x}+{y}")

    def _show_error_dialog(self, title, message):
        error_window = ctk.CTkToplevel(self)
        error_window.title(title)
        error_window.geometry("650x400")
        error_window.resizable(False, False)
        error_window.transient(self)
        error_window.grab_set()
        
        error_window.grid_columnconfigure(0, weight=1)
        error_window.grid_rowconfigure(0, weight=1)
        error_window.grid_rowconfigure(1, weight=0)
        
        content_frame = ctk.CTkFrame(error_window, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        content_frame.grid_columnconfigure(0, weight=1)
        
        icon_label = ctk.CTkLabel(content_frame, text="❌", font=("Arial", 56))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        error_text = ctk.CTkLabel(content_frame, text=message, font=("Arial", 16),
                                 wraplength=550, justify="center", text_color="#FF6B6B")
        error_text.grid(row=1, column=0, pady=10)
        
        ok_button = ctk.CTkButton(error_window, text="OK", command=error_window.destroy,
                                 font=("Arial", 16, "bold"), height=45, width=150)
        ok_button.grid(row=1, column=0, pady=30)
        
        error_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - error_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - error_window.winfo_height()) // 2
        error_window.geometry(f"+{x}+{y}")

    def _update_category_creation_icons(self):
        current = self.master
        while current:
            if hasattr(current, 'update_icons_in_category_creation'):
                current.update_icons_in_category_creation()
                break
            current = current.master

    def _update_all_categories_in_app(self):
        current = self.master
        while current:
            if hasattr(current, 'update_categories'):
                current.update_categories()
                break
            current = current.master

    def add_icons_from_files(self):
        file_paths = ctk.filedialog.askopenfilenames(
            title="Выберите файлы иконок (PNG)",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not file_paths:
            return
        
        try:
            self._process_files_addition(file_paths)
        except Exception as e:
            self._show_error_dialog("Ошибка при добавлении иконок", str(e))

    def _process_files_addition(self, file_paths):
        icons_dir = resource_path("assets/icons/categories")
        
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir)
        
        png_files = [f for f in file_paths if f.lower().endswith('.png')]
        
        if not png_files:
            raise ValueError("Не выбрано ни одного PNG файла")
        
        added_count = 0
        replaced_count = 0
        skipped_count = 0
        added_icons = []
        replaced_icons = []
        skipped_icons = []
        
        for file_path in png_files:
            file_name = os.path.basename(file_path)
            dst_path = os.path.join(icons_dir, file_name)
            
            if os.path.exists(dst_path):
                src_size = os.path.getsize(file_path)
                dst_size = os.path.getsize(dst_path)
                
                if src_size != dst_size:
                    shutil.copy2(file_path, dst_path)
                    replaced_count += 1
                    replaced_icons.append(file_name)
                else:
                    skipped_count += 1
                    skipped_icons.append(file_name)
            else:
                shutil.copy2(file_path, dst_path)
                added_count += 1
                added_icons.append(file_name)
        
        result_message = []
        if added_count > 0:
            result_message.append(f"✅ Добавлено новых иконок: {added_count}")
            if added_count <= 10:
                result_message.append("Новые иконки:")
                result_message.extend([f"  • {icon}" for icon in added_icons])
        
        if replaced_count > 0:
            result_message.append(f"🔄 Заменено существующих иконок: {replaced_count}")
            if replaced_count <= 10:
                result_message.append("Замененные иконки:")
                result_message.extend([f"  • {icon}" for icon in replaced_icons])
        
        if skipped_count > 0:
            result_message.append(f"⏭️ Пропущено (уже есть такие же): {skipped_count}")
        
        if not result_message:
            result_message = ["Не было добавлено или заменено ни одной иконки"]
        
        result_message.insert(0, f"📊 Всего обработано файлов: {len(png_files)}")
        
        self.update_icons_info()
        self.update_icons_preview()
        self._update_category_creation_icons()
        self._update_all_categories_in_app()
        self._show_success_dialog("Результат добавления иконок", "\n".join(result_message))


def create_color_square(color_hex, size=(30, 30)):
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), size], fill=color_hex, outline="black", width=1)
    return img


class CategoriesManagementFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="#aba6a6")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="Категории", font=("Arial", 24, "bold"), text_color="black")
        self.title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        self.add_category_button = ctk.CTkButton(self, text="Добавить новую категорию", font=("Arial", 18),
                                               text_color="black", command=self._create_category, height=50)
        self.add_category_button.grid(row=0, column=0, sticky="e", padx=20, pady=(20, 10))
        
        self.categories_frame = ctk.CTkScrollableFrame(self, fg_color="#949191")
        self.categories_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.categories_frame.grid_columnconfigure(0, weight=1)
        
        self.new_category = None
        self.update_categories_list()

    def _update_all_pages(self):
        """Обновляет все страницы через главное приложение"""
        current = self.master
        while current:
            if hasattr(current, 'force_update_all'):
                current.force_update_all()
                break
            current = current.master

    def _create_category(self):
        if not self.new_category or not self.new_category.winfo_exists():
            self.new_category = CategoryCreationPage(self.master)
            self.new_category.save_callback = self.on_category_saved
            self.new_category.protocol("WM_DELETE_WINDOW", self.on_category_window_close)
        
        self.new_category.attributes('-topmost', True)
        self.new_category.deiconify()
        self.new_category.update()
        self.new_category.focus()

    def on_category_saved(self):
        self.update_categories_list()
        self._update_all_pages()

    def on_category_window_close(self):
        if self.new_category:
            self.new_category.destroy()
            self.new_category = None
        self.update_categories_list()

    def update_categories_list(self):
        for widget in self.categories_frame.winfo_children():
            widget.destroy()
        
        categories = session.query(CategoriesTable).order_by(CategoriesTable.transaction_type, 
                                                           CategoriesTable.category_name).all()
        
        if not categories:
            no_categories_label = ctk.CTkLabel(self.categories_frame, text="Категории не найдены", 
                                             font=("Arial", 16), text_color="black")
            no_categories_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
            return
        
        expense_categories = [cat for cat in categories if cat.transaction_type == "Расход"]
        income_categories = [cat for cat in categories if cat.transaction_type == "Доход"]
        
        row = 0
        
        if expense_categories:
            expense_label = ctk.CTkLabel(self.categories_frame, text="Категории расходов:",
                                       font=("Arial", 20, "bold"), text_color="black")
            expense_label.grid(row=row, column=0, sticky="w", padx=20, pady=(10, 5))
            row += 1
            
            for i, category in enumerate(expense_categories):
                self._create_category_row(category, row + i)
            row += len(expense_categories)
        
        if income_categories:
            income_label = ctk.CTkLabel(self.categories_frame, text="Категории доходов:",
                                      font=("Arial", 20, "bold"), text_color="black")
            income_label.grid(row=row, column=0, sticky="w", padx=20, pady=(10, 5))
            row += 1
            
            for i, category in enumerate(income_categories):
                self._create_category_row(category, row + i)

    def _create_category_row(self, category, row):
        category_frame = ctk.CTkFrame(self.categories_frame, fg_color="#aba6a6")
        category_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        category_frame.grid_columnconfigure(0, weight=0)
        category_frame.grid_columnconfigure(1, weight=1)
        category_frame.grid_columnconfigure(2, weight=0)
        category_frame.grid_columnconfigure(3, weight=0)
        category_frame.grid_columnconfigure(4, weight=0)
        category_frame.grid_columnconfigure(5, weight=0)
        
        try:
            icon_path = resource_path(f"assets/{category.icon_url}")
            original_icon = Image.open(icon_path)
            resized_icon = original_icon.resize((40, 40), Image.Resampling.LANCZOS)
            
            recolored = self._recolor_icon_from_pil(resized_icon, category.colour)
            
            icon_image = ctk.CTkImage(light_image=recolored, size=(40, 40), dark_image=recolored)
            icon_label = ctk.CTkLabel(category_frame, image=icon_image, text="")
            icon_label.image = icon_image
            icon_label.grid(row=0, column=0, padx=(10, 5), pady=5)
        except Exception as e:
            print(f"Ошибка загрузки иконки для категории {category.category_name}: {e}")
            icon_label = ctk.CTkLabel(category_frame, text="📁", font=("Arial", 20))
            icon_label.grid(row=0, column=0, padx=(10, 5), pady=5)
        
        name_label = ctk.CTkLabel(category_frame, text=category.category_name, font=("Arial", 16), text_color="black")
        name_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        type_label = ctk.CTkLabel(category_frame, text=f"Тип: {category.transaction_type}",
                                 font=("Arial", 12), text_color="black")
        type_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        
        try:
            color_square_image = ctk.CTkImage(light_image=create_color_square(category.colour, size=(30, 30)), size=(30, 30))
            color_button = ctk.CTkButton(category_frame, image=color_square_image, text="", width=30, height=30,
                                        fg_color="transparent", hover_color="#8a8585",
                                        command=lambda c=category: self._change_category_color(c))
            color_button.grid(row=0, column=3, padx=(5, 10), pady=5)
        except Exception as e:
            fallback_button = ctk.CTkButton(category_frame, text=category.colour, font=("Arial", 10),
                                           text_color="black", width=30, height=30, fg_color="transparent",
                                           hover_color="#8a8585", command=lambda c=category: self._change_category_color(c))
            fallback_button.grid(row=0, column=3, padx=(5, 10), pady=5)
        
        try:
            edit_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/edit.png")), size=(20, 20))
            edit_button = ctk.CTkButton(category_frame, image=edit_icon, text="", width=30, height=30,
                                       fg_color="transparent", hover_color="#8a8585",
                                       command=lambda c=category: self._edit_category(c))
        except:
            edit_button = ctk.CTkButton(category_frame, text="✏️", width=30, height=30,
                                       fg_color="transparent", hover_color="#8a8585",
                                       command=lambda c=category: self._edit_category(c))
        edit_button.grid(row=0, column=4, padx=2, pady=5)
        
        try:
            delete_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/delete.png")), size=(20, 20))
            delete_button = ctk.CTkButton(category_frame, image=delete_icon, text="", width=30, height=30,
                                         fg_color="transparent", hover_color="#8a8585",
                                         command=lambda c=category: self._delete_category(c))
        except:
            delete_button = ctk.CTkButton(category_frame, text="🗑️", width=30, height=30,
                                         fg_color="transparent", hover_color="#8a8585",
                                         command=lambda c=category: self._delete_category(c))
        delete_button.grid(row=0, column=5, padx=(2, 10), pady=5)

    def _recolor_icon_from_pil(self, img, color):
        img = img.convert("RGBA")
        rgb = ImageColor.getrgb(color)
        pixels = img.load()
        
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    pixels[x, y] = (*rgb, a)
        return img

    def _get_app_instance(self):
        current = self.master
        while current:
            if hasattr(current, 'pages') and hasattr(current, 'update_categories'):
                return current
            current = current.master
        return None

    def _change_category_color(self, category):
        color_window = ctk.CTkToplevel(self)
        color_window.title(f"Изменение цвета для категории: {category.category_name}")
        color_window.geometry("500x450")
        color_window.transient(self)
        color_window.grab_set()
        
        color_window.grid_columnconfigure(0, weight=1)
        color_window.grid_rowconfigure(0, weight=0)
        color_window.grid_rowconfigure(1, weight=1)
        color_window.grid_rowconfigure(2, weight=0)
        color_window.grid_rowconfigure(3, weight=0)
        
        title_label = ctk.CTkLabel(color_window, text=f"Выберите новый цвет для категории\n'{category.category_name}'",
                                  font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        color_palette_frame = ctk.CTkFrame(color_window, fg_color="#aba6a6")
        color_palette_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        color_palette_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        color_palette = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
            "#F8C471", "#82E0AA", "#F1948A", "#85C1E9", "#D7BDE2",
            "#F9E79F", "#ABEBC6", "#AED6F1", "#E8DAEF", "#FAD7A0"
        ]
        
        selected_color = ctk.StringVar(value=category.colour)
        
        for i, color in enumerate(color_palette):
            row = i // 5
            col = i % 5
            
            color_button = ctk.CTkButton(color_palette_frame, text="", width=40, height=40,
                                        fg_color=color, hover_color=color,
                                        command=lambda c=color: selected_color.set(c))
            color_button.grid(row=row, column=col, padx=5, pady=5)
        
        color_preview_frame = ctk.CTkFrame(color_window, fg_color="transparent", height=40)
        color_preview_frame.grid(row=2, column=0, sticky="nwe", padx=20, pady=10)
        color_preview_frame.grid_propagate(False)
        color_preview_frame.grid_columnconfigure(0, weight=0)
        color_preview_frame.grid_columnconfigure(1, weight=1)
        color_preview_frame.grid_rowconfigure(0, weight=1)
        
        color_display = ctk.CTkLabel(color_preview_frame, text="", width=40, height=30,
                                    fg_color=category.colour, corner_radius=5)
        color_display.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        color_entry = ctk.CTkEntry(color_preview_frame, placeholder_text="Введите HEX цвета (например: #FF6B6B)",
                                  placeholder_text_color="white", justify="center", font=("Arial", 12))
        color_entry.grid(row=0, column=1, sticky="ew", padx=(0, 0))
        color_entry.insert(0, category.colour)
        
        def update_preview(*args):
            color = selected_color.get()
            color_display.configure(fg_color=color)
            color_entry.delete(0, "end")
            color_entry.insert(0, color)
        
        selected_color.trace_add("write", update_preview)
        
        def on_color_entry_changed(event=None):
            color_text = color_entry.get().strip()
            if not color_text:
                return
            
            if not color_text.startswith("#") and len(color_text) in [3, 6, 8]:
                color_text = "#" + color_text
                color_entry.delete(0, "end")
                color_entry.insert(0, color_text)
            
            if self._validate_hex_color(color_text):
                try:
                    color_display.configure(fg_color=color_text)
                    selected_color.set(color_text)
                except ValueError:
                    pass
        
        color_entry.bind("<KeyRelease>", on_color_entry_changed)
        color_entry.bind("<FocusOut>", on_color_entry_changed)
        
        buttons_frame = ctk.CTkFrame(color_window, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, pady=20)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        def save_color():
            new_color = selected_color.get()
            
            if not self._validate_hex_color(new_color):
                self._show_error_dialog("Ошибка", "Введите корректный цвет в формате HEX!")
                return
            
            try:
                category.colour = new_color
                session.commit()
                color_window.destroy()
                self.update_categories_list()
                self._update_all_pages()
                self._show_success_dialog("Успех", f"Цвет категории '{category.category_name}' успешно изменен!")
            except Exception as e:
                session.rollback()
                self._show_error_dialog("Ошибка", f"Не удалось изменить цвет категории: {str(e)}")
        
        save_button = ctk.CTkButton(buttons_frame, text="Сохранить", command=save_color,
                                   font=("Arial", 14, "bold"), height=40, width=120)
        save_button.grid(row=0, column=0, padx=10)
        
        cancel_button = ctk.CTkButton(buttons_frame, text="Отмена", command=color_window.destroy,
                                     font=("Arial", 14, "bold"), height=40, width=120)
        cancel_button.grid(row=0, column=1, padx=10)
        
        color_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - color_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - color_window.winfo_height()) // 2
        color_window.geometry(f"+{x}+{y}")

    def _validate_hex_color(self, color_text):
        if not color_text:
            return False
        if not color_text.startswith("#"):
            return False
        if len(color_text) not in [4, 7, 9]:
            return False
        valid_chars = set("#0123456789abcdefABCDEF")
        if not all(c in valid_chars for c in color_text[1:]):
            return False
        try:
            ImageColor.getrgb(color_text)
            return True
        except ValueError:
            return False

    def _edit_category(self, category):
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Редактирование категории: {category.category_name}")
        edit_window.geometry("650x750")
        edit_window.resizable(False, False)
        edit_window.transient(self)
        edit_window.grab_set()
        
        window_closed = False
        
        def on_window_close():
            nonlocal window_closed
            window_closed = True
            if edit_window.winfo_exists():
                edit_window.destroy()
        
        edit_window.protocol("WM_DELETE_WINDOW", on_window_close)
        edit_window.grid_columnconfigure(0, weight=1)
        edit_window.grid_rowconfigure(0, weight=1)
        
        main_container = ctk.CTkFrame(edit_window, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)
        
        try:
            icon_path = resource_path(f"assets/{category.icon_url}")
            original_icon = Image.open(icon_path)
            resized_icon = original_icon.resize((100, 100), Image.Resampling.LANCZOS)
            recolored = self._recolor_icon_from_pil(resized_icon, category.colour)
            icon_image = ctk.CTkImage(light_image=recolored, size=(100, 100), dark_image=recolored)
            icon_display = ctk.CTkLabel(main_container, image=icon_image, text="")
            icon_display.grid(row=0, column=0, pady=(30, 15))
            icon_display.image = icon_image
        except:
            icon_display = ctk.CTkLabel(main_container, text="📁", font=("Arial", 80))
            icon_display.grid(row=0, column=0, pady=(30, 15))
        
        title_label = ctk.CTkLabel(main_container, text="Редактирование категории", font=("Arial", 20, "bold"))
        title_label.grid(row=1, column=0, padx=30, pady=(0, 15), sticky="w")
        
        current_name_label = ctk.CTkLabel(main_container, text=f"Текущее название: {category.category_name}", font=("Arial", 14))
        current_name_label.grid(row=2, column=0, padx=30, pady=(0, 10), sticky="w")
        
        type_label = ctk.CTkLabel(main_container, text=f"Тип: {category.transaction_type}", font=("Arial", 14),
                                 text_color="#4CAF50" if category.transaction_type == "Доход" else "#FF6B6B")
        type_label.grid(row=3, column=0, padx=30, pady=(0, 15), sticky="w")
        
        name_entry = ctk.CTkEntry(main_container, placeholder_text="Введите новое название", font=("Arial", 16), width=550, height=45)
        name_entry.grid(row=4, column=0, padx=30, pady=10)
        name_entry.insert(0, category.category_name)
        name_entry.select_range(0, 'end')
        
        edit_window.after(100, lambda: name_entry.focus() if edit_window.winfo_exists() else None)
        
        transactions_count = session.query(TransactionsTable).filter(
            TransactionsTable.category_id == category.category_id
        ).count()
        
        if transactions_count > 0:
            info_label = ctk.CTkLabel(main_container, text=f"⚠️ Категория используется в {transactions_count} транзакциях.\n"
                                     "При переименовании транзакции обновятся автоматически.",
                                     font=("Arial", 13), text_color="#FF6B6B", wraplength=550, justify="left")
            info_label.grid(row=5, column=0, padx=30, pady=(15, 30), sticky="w")
        
        spacer = ctk.CTkFrame(main_container, fg_color="transparent", height=40)
        spacer.grid(row=6, column=0, sticky="ew", pady=15)
        
        buttons_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        buttons_frame.grid(row=7, column=0, padx=30, pady=(0, 40), sticky="ew")
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        def save_changes():
            nonlocal window_closed
            if window_closed or not edit_window.winfo_exists():
                return
                
            new_name = name_entry.get().strip()
            if not new_name:
                self._show_error_dialog("Ошибка", "Название категории не может быть пустым!")
                return
            
            if new_name != category.category_name:
                existing = session.query(CategoriesTable).filter(
                    CategoriesTable.category_name == new_name,
                    CategoriesTable.category_id != category.category_id
                ).first()
                
                if existing:
                    self._show_error_dialog("Ошибка", "Категория с таким названием уже существует!")
                    return
                
                try:
                    category.category_name = new_name
                    session.commit()
                    
                    if edit_window.winfo_exists():
                        edit_window.destroy()
                    
                    self.update_categories_list()
                    self._update_all_pages()
                    self._show_success_dialog("Успех", f"Категория успешно переименована в '{new_name}'")
                except Exception as e:
                    session.rollback()
                    self._show_error_dialog("Ошибка", f"Не удалось переименовать категорию: {str(e)}")
            else:
                if edit_window.winfo_exists():
                    edit_window.destroy()
        
        def cancel_changes():
            nonlocal window_closed
            window_closed = True
            if edit_window.winfo_exists():
                edit_window.destroy()
        
        save_button = ctk.CTkButton(buttons_frame, text="Сохранить", command=save_changes,
                                   font=("Arial", 16, "bold"), height=52, width=200,
                                   fg_color="#4CAF50", hover_color="#45a049", corner_radius=8)
        save_button.grid(row=0, column=0, padx=20, pady=10)
        
        cancel_button = ctk.CTkButton(buttons_frame, text="Отмена", command=cancel_changes,
                                     font=("Arial", 16, "bold"), height=52, width=200,
                                     fg_color="#FF6B6B", hover_color="#FF5252", corner_radius=8)
        cancel_button.grid(row=0, column=1, padx=20, pady=10)
        
        name_entry.bind("<Return>", lambda e: save_changes())
        
        edit_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - edit_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - edit_window.winfo_height()) // 2
        edit_window.geometry(f"+{x}+{y}")

    def _delete_category(self, category):
        transactions_count = session.query(TransactionsTable).filter(
            TransactionsTable.category_id == category.category_id
        ).count()
        
        if transactions_count > 0:
            warning_text = f"Категория '{category.category_name}' используется в {transactions_count} транзакциях.\n\n"
            warning_text += "Удаление категории невозможно, пока существуют транзакции с этой категорией.\n"
            warning_text += "Сначала перенесите транзакции в другую категорию или удалите их."
            self._show_warning_dialog("Невозможно удалить категорию", warning_text)
            return
        
        self._show_confirmation_dialog(category)
    
    def _show_warning_dialog(self, title, message):
        warning_window = ctk.CTkToplevel(self)
        warning_window.title(title)
        warning_window.geometry("600x400")
        warning_window.resizable(False, False)
        warning_window.transient(self)
        warning_window.grab_set()
        
        warning_window.grid_columnconfigure(0, weight=1)
        warning_window.grid_rowconfigure(0, weight=1)
        warning_window.grid_rowconfigure(1, weight=0)
        
        text_frame = ctk.CTkFrame(warning_window, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        icon_label = ctk.CTkLabel(text_frame, text="⚠️", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        error_text = ctk.CTkTextbox(text_frame, wrap="word", font=("Arial", 14), height=150, activate_scrollbars=True)
        error_text.grid(row=1, column=0, sticky="nsew", pady=10)
        error_text.insert("1.0", message)
        error_text.configure(state="disabled")
        
        ok_button = ctk.CTkButton(warning_window, text="OK", command=warning_window.destroy,
                                 font=("Arial", 14, "bold"), height=45, width=150)
        ok_button.grid(row=1, column=0, pady=20)
        
        warning_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - warning_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - warning_window.winfo_height()) // 2
        warning_window.geometry(f"+{x}+{y}")
    
    def _show_confirmation_dialog(self, category):
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Подтверждение удаления")
        confirm_window.geometry("550x350")
        confirm_window.resizable(False, False)
        confirm_window.transient(self)
        confirm_window.grab_set()
        
        confirm_window.grid_columnconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(0, weight=1)
        confirm_window.grid_rowconfigure(1, weight=0)
        
        main_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        main_frame.grid_columnconfigure(0, weight=1)
        
        icon_label = ctk.CTkLabel(main_frame, text="❓", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        confirm_text = ctk.CTkLabel(main_frame, text=f"Вы уверены, что хотите удалить категорию\n'{category.category_name}'?",
                                   font=("Arial", 16), wraplength=450, justify="center")
        confirm_text.grid(row=1, column=0, pady=10)
        
        warning_text = ctk.CTkLabel(main_frame, text="Это действие нельзя отменить!", font=("Arial", 12),
                                   text_color="#FF6B6B", wraplength=450, justify="center")
        warning_text.grid(row=2, column=0, pady=10)
        
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, pady=20)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        def confirm_delete():
            confirm_window.destroy()
            self._perform_deletion(category)
        
        def cancel_delete():
            confirm_window.destroy()
        
        yes_button = ctk.CTkButton(buttons_frame, text="Да, удалить", command=confirm_delete,
                                  font=("Arial", 14, "bold"), fg_color="#FF6B6B", hover_color="#FF5252", height=45, width=150)
        yes_button.grid(row=0, column=0, padx=10)
        
        no_button = ctk.CTkButton(buttons_frame, text="Отмена", command=cancel_delete,
                                 font=("Arial", 14, "bold"), height=45, width=150)
        no_button.grid(row=0, column=1, padx=10)
        
        confirm_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - confirm_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - confirm_window.winfo_height()) // 2
        confirm_window.geometry(f"+{x}+{y}")
    
    def _perform_deletion(self, category):
        try:
            session.delete(category)
            session.commit()
            self.update_categories_list()
            self._update_all_pages()
            self._show_success_dialog("Успех", f"Категория '{category.category_name}' успешно удалена")
        except Exception as e:
            session.rollback()
            self._show_error_dialog("Ошибка", f"Не удалось удалить категорию: {str(e)}")
    
    def _show_success_dialog(self, title, message):
        success_window = ctk.CTkToplevel(self)
        success_window.title(title)
        success_window.geometry("550x300")
        success_window.resizable(False, False)
        success_window.transient(self)
        success_window.grab_set()
        
        success_window.grid_columnconfigure(0, weight=1)
        success_window.grid_rowconfigure(0, weight=1)
        success_window.grid_rowconfigure(1, weight=0)
        
        content_frame = ctk.CTkFrame(success_window, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        content_frame.grid_columnconfigure(0, weight=1)
        
        icon_label = ctk.CTkLabel(content_frame, text="✅", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        success_text = ctk.CTkLabel(content_frame, text=message, font=("Arial", 16),
                                   wraplength=450, justify="center")
        success_text.grid(row=1, column=0, pady=10)
        
        ok_button = ctk.CTkButton(success_window, text="OK", command=success_window.destroy,
                                 font=("Arial", 14, "bold"), height=45, width=150)
        ok_button.grid(row=1, column=0, pady=20)
        
        success_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - success_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - success_window.winfo_height()) // 2
        success_window.geometry(f"+{x}+{y}")
    
    def _show_error_dialog(self, title, message):
        error_window = ctk.CTkToplevel(self)
        error_window.title(title)
        error_window.geometry("600x350")
        error_window.resizable(False, False)
        error_window.transient(self)
        error_window.grab_set()
        
        error_window.grid_columnconfigure(0, weight=1)
        error_window.grid_rowconfigure(0, weight=1)
        error_window.grid_rowconfigure(1, weight=0)
        
        content_frame = ctk.CTkFrame(error_window, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        content_frame.grid_columnconfigure(0, weight=1)
        
        icon_label = ctk.CTkLabel(content_frame, text="❌", font=("Arial", 48))
        icon_label.grid(row=0, column=0, pady=(0, 20))
        
        error_text = ctk.CTkLabel(content_frame, text=message, font=("Arial", 14),
                                 wraplength=500, justify="center", text_color="#FF6B6B")
        error_text.grid(row=1, column=0, pady=10)
        
        ok_button = ctk.CTkButton(error_window, text="OK", command=error_window.destroy,
                                 font=("Arial", 14, "bold"), height=45, width=150)
        ok_button.grid(row=1, column=0, pady=20)
        
        error_window.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - error_window.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - error_window.winfo_height()) // 2
        error_window.geometry(f"+{x}+{y}")


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.tabview = ctk.CTkTabview(self, fg_color="#aba6a6")
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        self.tabview.add("Категории")
        self.tabview.add("Иконки")
        
        self.tabview.tab("Категории").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Категории").grid_rowconfigure(0, weight=1)
        
        self.categories_management = CategoriesManagementFrame(self.tabview.tab("Категории"))
        self.categories_management.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.tabview.tab("Иконки").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Иконки").grid_rowconfigure(0, weight=1)
        
        self.icons_management = IconsManagementFrame(self.tabview.tab("Иконки"))
        self.icons_management.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def update_categories(self):
        self.categories_management.update_categories_list()
    
    def update_icons_in_category_creation(self):
        if hasattr(self.categories_management, 'new_category') and self.categories_management.new_category:
            if self.categories_management.new_category.winfo_exists():
                self.categories_management.new_category.force_update_icons()