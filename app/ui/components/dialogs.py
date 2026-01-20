"""
Диалоговые окна для ввода данных и сообщений.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional, Callable
from typing import List, Dict, Optional



def show_error(parent, message: str, title: str = "Ошибка"):
    """Показать диалог ошибки."""
    messagebox.showerror(title, message, parent=parent)


def show_info(parent, message: str, title: str = "Информация"):
    """Показать информационное сообщение."""
    messagebox.showinfo(title, message, parent=parent)


def show_warning(parent, message: str, title: str = "Предупреждение"):
    """Показать предупреждение."""
    messagebox.showwarning(title, message, parent=parent)


def ask_confirm(parent, message: str, title: str = "Подтверждение") -> bool:
    """Запросить подтверждение."""
    return messagebox.askyesno(title, message, parent=parent)


def ask_save_file(parent, default_filename: str = "report.xml", 
                  filetypes: list = None) -> Optional[str]:
    """Диалог сохранения файла."""
    if filetypes is None:
        filetypes = [("XML files", "*.xml"), ("All files", "*.*")]
    return filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".xml",
        filetypes=filetypes,
        initialfile=default_filename
    )


class DateEntry(ttk.Frame):
    """Виджет для ввода даты в формате YYYY-MM-DD."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        self.month_var = tk.StringVar(value=str(datetime.now().month).zfill(2))
        self.day_var = tk.StringVar(value=str(datetime.now().day).zfill(2))
        
        ttk.Label(self, text="Год:").grid(row=0, column=0, padx=2)
        ttk.Entry(self, textvariable=self.year_var, width=6).grid(row=0, column=1, padx=2)
        
        ttk.Label(self, text="Месяц:").grid(row=0, column=2, padx=2)
        ttk.Entry(self, textvariable=self.month_var, width=4).grid(row=0, column=3, padx=2)
        
        ttk.Label(self, text="День:").grid(row=0, column=4, padx=2)
        ttk.Entry(self, textvariable=self.day_var, width=4).grid(row=0, column=5, padx=2)
    
    def get_date(self) -> Optional[str]:
        """Получить дату в формате YYYY-MM-DD или None при ошибке."""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            date = datetime(year, month, day)
            return date.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return None
    
    def set_date(self, date_str: str):
        """Установить дату из строки YYYY-MM-DD."""
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            self.year_var.set(str(date.year))
            self.month_var.set(str(date.month).zfill(2))
            self.day_var.set(str(date.day).zfill(2))
        except (ValueError, TypeError):
            pass


class InputDialog(tk.Toplevel):
    """Базовый диалог ввода данных."""
    
    def __init__(self, parent, title: str, fields: List[Dict], 
                 initial_data: Optional[Dict] = None):
        """
        Args:
            parent: Родительское окно
            title: Заголовок диалога
            fields: Список полей [{'label': str, 'key': str, 'type': str, ...}]
            initial_data: Начальные данные для заполнения
        """
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.fields = fields
        self.vars = {}
        
        # Создаём поля
        for i, field in enumerate(fields):
            label = ttk.Label(self, text=field['label'] + ":")
            label.grid(row=i, column=0, padx=5, pady=5, sticky='e')
            
            if field.get('type') == 'date':
                entry = DateEntry(self)
                if initial_data and field['key'] in initial_data:
                    entry.set_date(initial_data[field['key']])
            elif field.get('type') == 'combobox':
                var = tk.StringVar()
                entry = ttk.Combobox(self, textvariable=var, 
                                    values=field.get('values', []), 
                                    state='readonly' if field.get('readonly') else 'normal')
                if initial_data and field['key'] in initial_data:
                    var.set(initial_data[field['key']])
            elif field.get('type') == 'text':
                var = tk.StringVar()
                entry = ttk.Entry(self, textvariable=var, width=30)
                if initial_data and field['key'] in initial_data:
                    var.set(str(initial_data[field['key']]))
            else:
                var = tk.StringVar()
                entry = ttk.Entry(self, textvariable=var, width=30)
                if initial_data and field['key'] in initial_data:
                    var.set(str(initial_data[field['key']]))
            
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            self.vars[field['key']] = entry if field.get('type') == 'date' else var
        
        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        # Центрируем окно
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def ok(self):
        """Обработчик кнопки OK."""
        self.result = {}
        for field in self.fields:
            key = field['key']
            if field.get('type') == 'date':
                value = self.vars[key].get_date()
            else:
                value = self.vars[key].get()
            
            if field.get('required') and not value:
                show_error(self, f"Поле '{field['label']}' обязательно для заполнения")
                return
            
            self.result[key] = value
        
        self.destroy()
    
    def cancel(self):
        """Обработчик кнопки Отмена."""
        self.result = None
        self.destroy()
