"""
Компонент таблицы на основе ttk.Treeview.
Упрощает создание и работу с таблицами данных.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Optional, Callable


class DataTable(ttk.Frame):
    """Таблица данных с прокруткой."""
    
    def __init__(self, parent, columns: List[Dict], data: Optional[List] = None, 
                 on_select: Optional[Callable] = None, **kwargs):
        """
        Args:
            parent: Родительский виджет
            columns: Список словарей с ключами 'name' (заголовок) и 'width' (ширина)
            data: Начальные данные (список словарей)
            on_select: Функция-обработчик выбора строки
        """
        super().__init__(parent, **kwargs)
        
        self.columns = columns
        self.on_select = on_select
        self.selected_item = None
        
        # Создаём Treeview с прокруткой
        self.tree = ttk.Treeview(self, columns=[col['name'] for col in columns], show='headings')
        
        # Настраиваем колонки
        for col in columns:
            self.tree.heading(col['name'], text=col['name'])
            self.tree.column(col['name'], width=col.get('width', 100), anchor=col.get('anchor', 'w'))
        
        # Прокрутка
        scrollbar_y = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Размещение
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Обработчик выбора
        if on_select:
            self.tree.bind('<<TreeviewSelect>>', self._on_select)
        
        # Загружаем данные если есть
        if data:
            self.load_data(data)
    
    def _on_select(self, event):
        """Обработчик выбора строки."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_item = item['values']
            if self.on_select:
                self.on_select(item['values'])
    
    def load_data(self, data: List[Dict]):
        """Загрузить данные в таблицу."""
        self.clear()
        for row in data:
            values = [row.get(col['name'], '') for col in self.columns]
            self.tree.insert('', 'end', values=values)
    
    def clear(self):
        """Очистить таблицу."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.selected_item = None
    
    def get_selected(self):
        """Получить выбранную строку."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            return item['values']
        return None
    
    def get_selected_index(self):
        """Получить индекс выбранной строки."""
        selection = self.tree.selection()
        if selection:
            return self.tree.index(selection[0])
        return None
