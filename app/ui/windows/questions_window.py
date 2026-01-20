"""
Окно для управления вопросами и вариантами ответов (CRUD).
"""

import tkinter as tk
from tkinter import ttk
from app.repositories import surveys, questions
from app.ui.components.table import DataTable
from app.ui.components.dialogs import InputDialog, show_error, show_info, ask_confirm


class QuestionsWindow(ttk.Frame):
    """Окно управления вопросами."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_survey_id = None
        self.setup_ui()
        self.load_surveys()
    
    def setup_ui(self):
        """Настройка интерфейса."""
        # Выбор опроса
        survey_frame = ttk.LabelFrame(self, text="Выбор опроса")
        survey_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(survey_frame, text="Опрос:").pack(side=tk.LEFT, padx=5)
        self.survey_var = tk.StringVar()
        self.survey_combo = ttk.Combobox(survey_frame, textvariable=self.survey_var, 
                                         state='readonly', width=40)
        self.survey_combo.pack(side=tk.LEFT, padx=5)
        self.survey_combo.bind('<<ComboboxSelected>>', self.on_survey_selected)
        ttk.Button(survey_frame, text="Обновить список", command=self.load_surveys).pack(side=tk.LEFT, padx=5)
        
        # Панель кнопок для вопросов
        questions_frame = ttk.LabelFrame(self, text="Вопросы")
        questions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(questions_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Добавить вопрос", command=self.create_question).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Редактировать вопрос", command=self.edit_question).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить вопрос", command=self.delete_question).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Добавить вариант ответа", command=self.create_option).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Редактировать вариант", command=self.edit_option).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить вариант", command=self.delete_option).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_questions).pack(side=tk.LEFT, padx=2)
        
        # Таблица вопросов
        columns = [
            {'name': 'ID', 'width': 50},
            {'name': 'Порядок', 'width': 70},
            {'name': 'Текст вопроса', 'width': 400},
            {'name': 'Тип', 'width': 100}
        ]
        
        self.questions_table = DataTable(questions_frame, columns, on_select=self.on_question_selected)
        self.questions_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Таблица вариантов ответов
        options_frame = ttk.LabelFrame(self, text="Варианты ответов выбранного вопроса")
        options_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        options_columns = [
            {'name': 'ID', 'width': 50},
            {'name': 'Порядок', 'width': 70},
            {'name': 'Текст', 'width': 300},
            {'name': 'Положительный', 'width': 100}
        ]
        
        self.options_table = DataTable(options_frame, options_columns)
        self.options_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Сохраняем ID выбранного вопроса
        self.selected_vopros_id = None
    
    def load_surveys(self):
        """Загрузить список опросов."""
        try:
            surveys_list = surveys.get_all()
            survey_items = [f"{s['id_oprosa']}: {s['tema']}" for s in surveys_list]
            self.survey_combo['values'] = survey_items
            if survey_items:
                self.survey_combo.current(0)
                self.on_survey_selected()
        except Exception as e:
            show_error(self, f"Ошибка загрузки опросов: {e}")
    
    def on_survey_selected(self, event=None):
        """Обработчик выбора опроса."""
        selection = self.survey_var.get()
        if selection:
            opros_id = int(selection.split(':')[0])
            self.current_survey_id = opros_id
            self.refresh_questions()
    
    def refresh_questions(self):
        """Обновить список вопросов."""
        if not self.current_survey_id:
            return
        
        try:
            # Сохраняем выбранный вопрос перед обновлением
            selected_before = self.questions_table.get_selected()
            selected_vopros_id_before = int(selected_before[0]) if selected_before else None
            
            questions_list = questions.get_by_opros(self.current_survey_id)
            table_data = []
            for q in questions_list:
                table_data.append({
                    'ID': q['id_voprosa'],
                    'Порядок': q['poryadok'],
                    'Текст вопроса': q['tekst_voprosa'],
                    'Тип': q['tip_voprosa']
                })
            self.questions_table.load_data(table_data)
            
            # Восстанавливаем выбор и загружаем варианты, если вопрос был выбран
            if selected_vopros_id_before:
                # Пытаемся найти этот вопрос в обновлённом списке
                for i, row in enumerate(table_data):
                    if row['ID'] == selected_vopros_id_before:
                        # Выбираем строку в таблице
                        children = self.questions_table.tree.get_children()
                        if i < len(children):
                            self.questions_table.tree.selection_set(children[i])
                            self.questions_table.tree.focus(children[i])
                            # Загружаем варианты для выбранного вопроса
                            self.refresh_options(selected_vopros_id_before)
                            break
                else:
                    # Вопрос не найден - очищаем варианты
                    self.options_table.clear()
                    self.selected_vopros_id = None
            else:
                # Не было выбранного вопроса - очищаем варианты
                self.options_table.clear()
                self.selected_vopros_id = None
        except Exception as e:
            show_error(self, f"Ошибка загрузки вопросов: {e}")
    
    def create_question(self):
        """Создать новый вопрос."""
        if not self.current_survey_id:
            show_error(self, "Выберите опрос")
            return
        
        fields = [
            {'label': 'Текст вопроса', 'key': 'tekst_voprosa', 'type': 'text', 'required': True},
            {'label': 'Порядок', 'key': 'poryadok', 'type': 'text', 'required': False}
        ]
        
        dialog = InputDialog(self, "Создать вопрос", fields)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                poryadok = int(dialog.result['poryadok']) if dialog.result['poryadok'] else None
                vopros_id = questions.create(
                    self.current_survey_id,
                    dialog.result['tekst_voprosa'],
                    poryadok=poryadok
                )
                
                if vopros_id:
                    show_info(self, f"Вопрос создан с ID: {vopros_id}")
                    self.refresh_questions()
                    # Автоматически выбираем созданный вопрос
                    self.selected_vopros_id = vopros_id
                    # Находим и выбираем строку в таблице
                    children = self.questions_table.tree.get_children()
                    for child in children:
                        item_values = self.questions_table.tree.item(child)['values']
                        if item_values and int(item_values[0]) == vopros_id:
                            self.questions_table.tree.selection_set(child)
                            self.questions_table.tree.focus(child)
                            self.refresh_options(vopros_id)
                            break
                else:
                    show_error(self, "Не удалось создать вопрос")
            except ValueError as e:
                show_error(self, f"Неверный формат числа для порядка: {e}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                show_error(self, f"Ошибка создания вопроса: {e}")
    
    def edit_question(self):
        """Редактировать вопрос."""
        selected = self.questions_table.get_selected()
        if not selected:
            show_error(self, "Выберите вопрос для редактирования")
            return
        
        vopros_id = int(selected[0])
        vopros = questions.get_by_id(vopros_id)
        
        if not vopros:
            show_error(self, "Вопрос не найден")
            return
        
        fields = [
            {'label': 'Текст вопроса', 'key': 'tekst_voprosa', 'type': 'text', 'required': True},
            {'label': 'Порядок', 'key': 'poryadok', 'type': 'text', 'required': True}
        ]
        
        initial_data = {
            'tekst_voprosa': vopros['tekst_voprosa'],
            'poryadok': str(vopros['poryadok'])
        }
        
        dialog = InputDialog(self, "Редактировать вопрос", fields, initial_data)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                poryadok = int(dialog.result['poryadok'])
                success = questions.update(vopros_id, dialog.result['tekst_voprosa'], poryadok)
                
                if success:
                    show_info(self, "Вопрос обновлён")
                    self.refresh_questions()
            except ValueError:
                show_error(self, "Неверный формат числа для порядка")
            except Exception as e:
                show_error(self, f"Ошибка обновления вопроса: {e}")
    
    def delete_question(self):
        """Удалить вопрос."""
        selected = self.questions_table.get_selected()
        if not selected:
            show_error(self, "Выберите вопрос для удаления")
            return
        
        vopros_id = int(selected[0])
        
        if ask_confirm(self, f"Удалить вопрос ID {vopros_id}?"):
            try:
                success = questions.delete(vopros_id)
                if success:
                    show_info(self, "Вопрос удалён")
                    self.refresh_questions()
            except Exception as e:
                show_error(self, f"Ошибка удаления вопроса: {e}")
    
    def on_question_selected(self, values=None):
        """Обработчик выбора вопроса - загрузить варианты ответов."""
        selected = self.questions_table.get_selected()
        if not selected:
            self.options_table.clear()
            self.selected_vopros_id = None
            return
        
        vopros_id = int(selected[0])
        self.selected_vopros_id = vopros_id
        self.refresh_options(vopros_id)
    
    def refresh_options(self, vopros_id):
        """Обновить список вариантов ответов."""
        try:
            options_list = questions.get_variants(vopros_id)
            table_data = []
            for opt in options_list:
                table_data.append({
                    'ID': opt['id_varianta'],
                    'Порядок': opt['poryadok'],
                    'Текст': opt['tekst_varianta'],
                    'Положительный': 'Да' if opt['priznak_polozh'] == 1 else 'Нет'
                })
            self.options_table.load_data(table_data)
        except Exception as e:
            show_error(self, f"Ошибка загрузки вариантов ответов: {e}")
    
    def create_option(self):
        """Создать вариант ответа."""
        selected = self.questions_table.get_selected()
        if not selected:
            show_error(self, "Выберите вопрос для добавления варианта ответа")
            return
        
        vopros_id = int(selected[0])
        
        fields = [
            {'label': 'Текст варианта', 'key': 'tekst_varianta', 'type': 'text', 'required': True},
            {'label': 'Положительный ответ', 'key': 'priznak_polozh', 'type': 'combobox', 
             'values': ['Да', 'Нет'], 'required': True},
            {'label': 'Порядок', 'key': 'poryadok', 'type': 'text', 'required': False}
        ]
        
        dialog = InputDialog(self, "Создать вариант ответа", fields)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                priznak_polozh = 1 if dialog.result['priznak_polozh'] == 'Да' else 0
                poryadok = int(dialog.result['poryadok']) if dialog.result['poryadok'] else None
                variant_id = questions.create_variant(vopros_id, dialog.result['tekst_varianta'], 
                                                    priznak_polozh, poryadok)
                
                if variant_id:
                    show_info(self, f"Вариант ответа создан с ID: {variant_id}")
                    # Обновляем варианты, сохраняя выбор вопроса
                    if self.selected_vopros_id == vopros_id:
                        self.refresh_options(vopros_id)
                    else:
                        # Если вопрос не выбран, выбираем его и загружаем варианты
                        self.selected_vopros_id = vopros_id
                        children = self.questions_table.tree.get_children()
                        for child in children:
                            item_values = self.questions_table.tree.item(child)['values']
                            if item_values and int(item_values[0]) == vopros_id:
                                self.questions_table.tree.selection_set(child)
                                self.questions_table.tree.focus(child)
                                self.refresh_options(vopros_id)
                                break
                else:
                    show_error(self, "Не удалось создать вариант ответа")
            except ValueError as e:
                show_error(self, f"Неверный формат числа для порядка: {e}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                show_error(self, f"Ошибка создания варианта ответа: {e}")
    
    def edit_option(self):
        """Редактировать вариант ответа."""
        selected = self.options_table.get_selected()
        if not selected:
            show_error(self, "Выберите вариант ответа для редактирования")
            return
        
        variant_id = int(selected[0])
        
        # Получаем данные варианта
        vopros_selected = self.questions_table.get_selected()
        if not vopros_selected:
            return
        
        vopros_id = int(vopros_selected[0])
        options_list = questions.get_variants(vopros_id)
        option = next((opt for opt in options_list if opt['id_varianta'] == variant_id), None)
        
        if not option:
            show_error(self, "Вариант ответа не найден")
            return
        
        fields = [
            {'label': 'Текст варианта', 'key': 'tekst_varianta', 'type': 'text', 'required': True},
            {'label': 'Положительный ответ', 'key': 'priznak_polozh', 'type': 'combobox', 
             'values': ['Да', 'Нет'], 'required': True},
            {'label': 'Порядок', 'key': 'poryadok', 'type': 'text', 'required': True}
        ]
        
        initial_data = {
            'tekst_varianta': option['tekst_varianta'],
            'priznak_polozh': 'Да' if option['priznak_polozh'] == 1 else 'Нет',
            'poryadok': str(option['poryadok'])
        }
        
        dialog = InputDialog(self, "Редактировать вариант ответа", fields, initial_data)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                priznak_polozh = 1 if dialog.result['priznak_polozh'] == 'Да' else 0
                poryadok = int(dialog.result['poryadok'])
                success = questions.update_variant(variant_id, dialog.result['tekst_varianta'], 
                                                  priznak_polozh, poryadok)
                
                if success:
                    show_info(self, "Вариант ответа обновлён")
                    # Обновляем варианты для выбранного вопроса
                    if self.selected_vopros_id == vopros_id:
                        self.refresh_options(vopros_id)
            except ValueError:
                show_error(self, "Неверный формат числа для порядка")
            except Exception as e:
                show_error(self, f"Ошибка обновления варианта ответа: {e}")
    
    def delete_option(self):
        """Удалить вариант ответа."""
        selected = self.options_table.get_selected()
        if not selected:
            show_error(self, "Выберите вариант ответа для удаления")
            return
        
        variant_id = int(selected[0])
        
        if ask_confirm(self, f"Удалить вариант ответа ID {variant_id}?"):
            try:
                success = questions.delete_variant(variant_id)
                if success:
                    show_info(self, "Вариант ответа удалён")
                    # Обновляем варианты для выбранного вопроса
                    if self.selected_vopros_id:
                        self.refresh_options(self.selected_vopros_id)
            except Exception as e:
                show_error(self, f"Ошибка удаления варианта ответа: {e}")
