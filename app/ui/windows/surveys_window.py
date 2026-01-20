"""
Окно для управления опросами (OPROS) - CRUD.
"""

import tkinter as tk
from tkinter import ttk
from app.repositories import surveys
from app.ui.components.table import DataTable
from app.ui.components.dialogs import InputDialog, show_error, show_info, ask_confirm


class SurveysWindow(ttk.Frame):
    """Окно управления опросами."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Настройка интерфейса."""
        # Панель кнопок
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Создать", command=self.create_survey).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_survey).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_survey).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Активировать", command=self.activate_survey).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Закрыть", command=self.close_survey).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_data).pack(side=tk.LEFT, padx=2)
        
        # Таблица
        columns = [
            {'name': 'ID', 'width': 50},
            {'name': 'Тема', 'width': 200},
            {'name': 'Начало', 'width': 100},
            {'name': 'Окончание (план)', 'width': 120},
            {'name': 'Окончание (факт)', 'width': 120},
            {'name': 'Мин. участников', 'width': 120},
            {'name': 'Статус', 'width': 100},
            {'name': 'Участников', 'width': 100}
        ]
        
        self.table = DataTable(self, columns)
        self.table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def refresh_data(self):
        """Обновить данные в таблице."""
        try:
            from app.repositories.reports import get_all_surveys_list
            surveys_list = get_all_surveys_list()
            
            # Форматируем данные для таблицы
            table_data = []
            for item in surveys_list:
                table_data.append({
                    'ID': item['id_oprosa'],
                    'Тема': item['tema'],
                    'Начало': str(item['data_nachala']),
                    'Окончание (план)': str(item['data_okonch_pln']),
                    'Окончание (факт)': str(item['data_okonch_fakt']) if item['data_okonch_fakt'] else '',
                    'Мин. участников': item.get('min_kol_otvetov', 0),
                    'Статус': item['status'],
                    'Участников': item['participants_count']
                })
            
            self.table.load_data(table_data)
        except Exception as e:
            show_error(self, f"Ошибка загрузки данных: {e}")
    
    def create_survey(self):
        """Создать новый опрос."""
        fields = [
            {'label': 'Тема', 'key': 'tema', 'type': 'text', 'required': True},
            {'label': 'Описание', 'key': 'opisanie', 'type': 'text', 'required': False},
            {'label': 'Дата начала', 'key': 'data_nachala', 'type': 'date', 'required': True},
            {'label': 'Дата окончания (план)', 'key': 'data_okonch_pln', 'type': 'date', 'required': True},
            {'label': 'Мин. участников', 'key': 'min_kol_otvetov', 'type': 'text', 'required': True},
            {'label': 'Статус', 'key': 'status', 'type': 'combobox', 
             'values': ['draft', 'active', 'closed'], 'required': True}
        ]
        
        dialog = InputDialog(self, "Создать опрос", fields)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                min_kol = int(dialog.result['min_kol_otvetov'])
                if min_kol <= 0:
                    show_error(self, "Минимальное количество участников должно быть больше 0")
                    return
                
                if dialog.result['data_nachala'] > dialog.result['data_okonch_pln']:
                    show_error(self, "Дата начала должна быть раньше даты окончания")
                    return
                
                opros_id = surveys.create(
                    dialog.result['tema'],
                    dialog.result.get('opisanie', ''),
                    dialog.result['data_nachala'],
                    dialog.result['data_okonch_pln'],
                    min_kol,
                    dialog.result['status']
                )
                
                if opros_id:
                    show_info(self, f"Опрос создан с ID: {opros_id}")
                    self.refresh_data()
                else:
                    show_error(self, "Не удалось создать опрос")
            except ValueError as e:
                show_error(self, f"Неверный формат числа для минимального количества участников: {e}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                show_error(self, f"Ошибка создания опроса: {e}")
    
    def edit_survey(self):
        """Редактировать опрос."""
        selected = self.table.get_selected()
        if not selected:
            show_error(self, "Выберите опрос для редактирования")
            return
        
        opros_id = int(selected[0])
        opros = surveys.get_by_id(opros_id)
        
        if not opros:
            show_error(self, "Опрос не найден")
            return
        
        fields = [
            {'label': 'Тема', 'key': 'tema', 'type': 'text', 'required': True},
            {'label': 'Описание', 'key': 'opisanie', 'type': 'text', 'required': False},
            {'label': 'Дата начала', 'key': 'data_nachala', 'type': 'date', 'required': True},
            {'label': 'Дата окончания (план)', 'key': 'data_okonch_pln', 'type': 'date', 'required': True},
            {'label': 'Мин. участников', 'key': 'min_kol_otvetov', 'type': 'text', 'required': True},
            {'label': 'Статус', 'key': 'status', 'type': 'combobox', 
             'values': ['draft', 'active', 'closed'], 'required': True}
        ]
        
        initial_data = {
            'tema': opros['tema'],
            'opisanie': opros.get('opisanie', '') or '',
            'data_nachala': str(opros['data_nachala']),
            'data_okonch_pln': str(opros['data_okonch_pln']),
            'min_kol_otvetov': str(opros['min_kol_otvetov']),
            'status': opros['status']
        }
        
        dialog = InputDialog(self, "Редактировать опрос", fields, initial_data)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                min_kol = int(dialog.result['min_kol_otvetov'])
                if min_kol <= 0:
                    show_error(self, "Минимальное количество участников должно быть больше 0")
                    return
                
                if dialog.result['data_nachala'] > dialog.result['data_okonch_pln']:
                    show_error(self, "Дата начала должна быть раньше даты окончания")
                    return
                
                success = surveys.update(
                    opros_id,
                    dialog.result['tema'],
                    dialog.result.get('opisanie', ''),
                    dialog.result['data_nachala'],
                    dialog.result['data_okonch_pln'],
                    min_kol,
                    dialog.result['status']
                )
                
                if success:
                    show_info(self, "Опрос обновлён")
                    self.refresh_data()
            except ValueError:
                show_error(self, "Неверный формат числа для минимального количества участников")
            except Exception as e:
                show_error(self, f"Ошибка обновления опроса: {e}")
    
    def delete_survey(self):
        """Удалить опрос."""
        selected = self.table.get_selected()
        if not selected:
            show_error(self, "Выберите опрос для удаления")
            return
        
        opros_id = int(selected[0])
        
        if ask_confirm(self, f"Удалить опрос ID {opros_id}?"):
            try:
                success = surveys.delete(opros_id)
                if success:
                    show_info(self, "Опрос удалён")
                    self.refresh_data()
            except Exception as e:
                show_error(self, f"Ошибка удаления опроса: {e}")
    
    def activate_survey(self):
        """Активировать опрос."""
        selected = self.table.get_selected()
        if not selected:
            show_error(self, "Выберите опрос для активации")
            return
        
        opros_id = int(selected[0])
        
        try:
            success = surveys.activate(opros_id)
            if success:
                show_info(self, "Опрос активирован")
                self.refresh_data()
        except Exception as e:
            show_error(self, f"Ошибка активации опроса: {e}")
    
    def close_survey(self):
        """Закрыть опрос (может быть продлён триггером)."""
        selected = self.table.get_selected()
        if not selected:
            show_error(self, "Выберите опрос для закрытия")
            return
        
        opros_id = int(selected[0])
        
        if ask_confirm(self, f"Закрыть опрос ID {opros_id}? (Может быть продлён при недостатке участников)"):
            try:
                success = surveys.close(opros_id)
                if success:
                    show_info(self, "Попытка закрытия опроса выполнена. Проверьте статус.")
                    self.refresh_data()
            except Exception as e:
                show_error(self, f"Ошибка закрытия опроса: {e}")
