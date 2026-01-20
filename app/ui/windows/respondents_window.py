"""
Окно для управления респондентами (RESPONDENT) - CRUD.
Использует справочники POL, REGION, UROVEN_OBRAZOVANIYA.
"""

import tkinter as tk
from tkinter import ttk
from app.repositories import respondents
from app.ui.components.table import DataTable
from app.ui.components.dialogs import InputDialog, show_error, show_info, ask_confirm


class RespondentsWindow(ttk.Frame):
    """Окно управления респондентами."""
    
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
        
        ttk.Button(btn_frame, text="Создать", command=self.create_respondent).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_respondent).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_respondent).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_data).pack(side=tk.LEFT, padx=2)
        
        # Таблица (без ФИО для анонимности)
        columns = [
            {'name': 'ID', 'width': 50},
            {'name': 'Возраст', 'width': 70},
            {'name': 'Пол', 'width': 80},
            {'name': 'Регион', 'width': 150},
            {'name': 'Образование', 'width': 150},
            {'name': 'Дата рождения', 'width': 120}
        ]
        
        self.table = DataTable(self, columns)
        self.table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def refresh_data(self):
        """Обновить данные в таблице."""
        try:
            data = respondents.get_all()
            table_data = []
            for item in data:
                table_data.append({
                    'ID': item['id_respondenta'],
                    'Возраст': int(item['age']) if item['age'] else '',
                    'Пол': item['pol'],
                    'Регион': item['region'],
                    'Образование': item['uroven_obrazovaniya'],
                    'Дата рождения': str(item['data_rozhdeniya'])
                })
            self.table.load_data(table_data)
        except Exception as e:
            show_error(self, f"Ошибка загрузки данных: {e}")
    
    def create_respondent(self):
        """Создать нового респондента."""
        # Загружаем справочники
        try:
            pol_list = respondents.get_all_pol()
            region_list = respondents.get_all_region()
            uroven_list = respondents.get_all_uroven()
        except Exception as e:
            show_error(self, f"Ошибка загрузки справочников: {e}")
            return
        
        pol_values = [f"{p['id_pola']}: {p['naimenovanie']}" for p in pol_list]
        region_values = [f"{r['id_regiona']}: {r['naimenovanie']}" for r in region_list]
        uroven_values = [f"{u['id_urovnya']}: {u['naimenovanie']}" for u in uroven_list]
        
        fields = [
            {'label': 'Фамилия (опционально)', 'key': 'familiya', 'type': 'text', 'required': False},
            {'label': 'Имя (опционально)', 'key': 'imya', 'type': 'text', 'required': False},
            {'label': 'Отчество (опционально)', 'key': 'otchestvo', 'type': 'text', 'required': False},
            {'label': 'Дата рождения', 'key': 'data_rozhdeniya', 'type': 'date', 'required': True},
            {'label': 'Пол', 'key': 'id_pola', 'type': 'combobox', 'values': pol_values, 'required': True},
            {'label': 'Регион', 'key': 'id_regiona', 'type': 'combobox', 'values': region_values, 'required': True},
            {'label': 'Образование', 'key': 'id_urovnya', 'type': 'combobox', 'values': uroven_values, 'required': True}
        ]
        
        dialog = InputDialog(self, "Создать респондента", fields)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                id_pola = int(dialog.result['id_pola'].split(':')[0])
                id_regiona = int(dialog.result['id_regiona'].split(':')[0])
                id_urovnya = int(dialog.result['id_urovnya'].split(':')[0])
                
                respondent_id = respondents.create(
                    dialog.result.get('familiya', '') or None,
                    dialog.result.get('imya', '') or None,
                    dialog.result.get('otchestvo', '') or None,
                    dialog.result['data_rozhdeniya'],
                    id_pola,
                    id_regiona,
                    id_urovnya
                )
                
                if respondent_id:
                    show_info(self, f"Респондент создан с ID: {respondent_id}")
                    self.refresh_data()
                else:
                    show_error(self, "Не удалось создать респондента")
            except Exception as e:
                import traceback
                traceback.print_exc()
                show_error(self, f"Ошибка создания респондента: {e}")
    
    def edit_respondent(self):
        """Редактировать респондента."""
        selected = self.table.get_selected()
        if not selected:
            show_error(self, "Выберите респондента для редактирования")
            return
        
        respondent_id = int(selected[0])
        respondent = respondents.get_by_id(respondent_id)
        
        if not respondent:
            show_error(self, "Респондент не найден")
            return
        
        # Загружаем справочники
        try:
            pol_list = respondents.get_all_pol()
            region_list = respondents.get_all_region()
            uroven_list = respondents.get_all_uroven()
        except Exception as e:
            show_error(self, f"Ошибка загрузки справочников: {e}")
            return
        
        pol_values = [f"{p['id_pola']}: {p['naimenovanie']}" for p in pol_list]
        region_values = [f"{r['id_regiona']}: {r['naimenovanie']}" for r in region_list]
        uroven_values = [f"{u['id_urovnya']}: {u['naimenovanie']}" for u in uroven_list]
        
        fields = [
            {'label': 'Фамилия (опционально)', 'key': 'familiya', 'type': 'text', 'required': False},
            {'label': 'Имя (опционально)', 'key': 'imya', 'type': 'text', 'required': False},
            {'label': 'Отчество (опционально)', 'key': 'otchestvo', 'type': 'text', 'required': False},
            {'label': 'Дата рождения', 'key': 'data_rozhdeniya', 'type': 'date', 'required': True},
            {'label': 'Пол', 'key': 'id_pola', 'type': 'combobox', 'values': pol_values, 'required': True},
            {'label': 'Регион', 'key': 'id_regiona', 'type': 'combobox', 'values': region_values, 'required': True},
            {'label': 'Образование', 'key': 'id_urovnya', 'type': 'combobox', 'values': uroven_values, 'required': True}
        ]
        
        initial_data = {
            'familiya': respondent.get('familiya', '') or '',
            'imya': respondent.get('imya', '') or '',
            'otchestvo': respondent.get('otchestvo', '') or '',
            'data_rozhdeniya': str(respondent['data_rozhdeniya']),
            'id_pola': f"{respondent['id_pola']}: {respondent['pol']}",
            'id_regiona': f"{respondent['id_regiona']}: {respondent['region']}",
            'id_urovnya': f"{respondent['id_urovnya']}: {respondent['uroven_obrazovaniya']}"
        }
        
        dialog = InputDialog(self, "Редактировать респондента", fields, initial_data)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                id_pola = int(dialog.result['id_pola'].split(':')[0])
                id_regiona = int(dialog.result['id_regiona'].split(':')[0])
                id_urovnya = int(dialog.result['id_urovnya'].split(':')[0])
                
                success = respondents.update(
                    respondent_id,
                    dialog.result.get('familiya', '') or None,
                    dialog.result.get('imya', '') or None,
                    dialog.result.get('otchestvo', '') or None,
                    dialog.result['data_rozhdeniya'],
                    id_pola,
                    id_regiona,
                    id_urovnya
                )
                
                if success:
                    show_info(self, "Респондент обновлён")
                    self.refresh_data()
            except Exception as e:
                show_error(self, f"Ошибка обновления респондента: {e}")
    
    def delete_respondent(self):
        """Удалить респондента."""
        selected = self.table.get_selected()
        if not selected:
            show_error(self, "Выберите респондента для удаления")
            return
        
        respondent_id = int(selected[0])
        
        if ask_confirm(self, f"Удалить респондента ID {respondent_id}?"):
            try:
                success = respondents.delete(respondent_id)
                if success:
                    show_info(self, "Респондент удалён")
                    self.refresh_data()
            except Exception as e:
                show_error(self, f"Ошибка удаления респондента: {e}")
