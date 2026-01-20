"""
Окно для прохождения опроса респондентом.
Использует UCHASTIE для фиксации участия и OTVET для ответов.
"""

import tkinter as tk
from tkinter import ttk
from app.repositories import surveys, questions, respondents, responses
from app.ui.components.dialogs import show_error, show_info, InputDialog


class ConductSurveyWindow(ttk.Frame):
    """Окно прохождения опроса."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_opros_id = None
        self.current_respondent_id = None
        self.current_voprosy = []
        self.current_vopros_index = 0
        self.setup_ui()
        self.load_surveys()
        self.load_respondents()
    
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
        ttk.Button(survey_frame, text="Обновить", command=self.load_surveys).pack(side=tk.LEFT, padx=5)
        
        # Выбор/создание респондента
        respondent_frame = ttk.LabelFrame(self, text="Респондент")
        respondent_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(respondent_frame, text="Респондент:").pack(side=tk.LEFT, padx=5)
        self.respondent_var = tk.StringVar()
        self.respondent_combo = ttk.Combobox(respondent_frame, textvariable=self.respondent_var, 
                                            state='readonly', width=30)
        self.respondent_combo.pack(side=tk.LEFT, padx=5)
        self.respondent_combo.bind('<<ComboboxSelected>>', self.on_respondent_selected)
        ttk.Button(respondent_frame, text="Создать нового", command=self.create_respondent).pack(side=tk.LEFT, padx=5)
        ttk.Button(respondent_frame, text="Обновить", command=self.load_respondents).pack(side=tk.LEFT, padx=5)
        
        # Область вопроса
        self.question_frame = ttk.LabelFrame(self, text="Вопрос")
        self.question_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.question_label = ttk.Label(self.question_frame, text="Выберите опрос и респондента", 
                                        font=('Arial', 12))
        self.question_label.pack(pady=20)
        
        self.options_frame = ttk.Frame(self.question_frame)
        self.options_frame.pack(pady=10)
        
        self.option_var = tk.IntVar()
        
        # Кнопки навигации
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.prev_btn = ttk.Button(nav_frame, text="Предыдущий", command=self.prev_question, state='disabled')
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = ttk.Button(nav_frame, text="Следующий", command=self.next_question, state='disabled')
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        self.submit_btn = ttk.Button(nav_frame, text="Отправить ответ", command=self.submit_answer, state='disabled')
        self.submit_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(nav_frame, text="Начать опрос", command=self.start_survey, state='disabled')
        self.start_btn.pack(side=tk.LEFT, padx=5)
    
    def load_surveys(self):
        """Загрузить список активных опросов."""
        try:
            surveys_list = surveys.get_active()
            survey_items = [f"{s['id_oprosa']}: {s['tema']}" for s in surveys_list]
            self.survey_combo['values'] = survey_items
        except Exception as e:
            show_error(self, f"Ошибка загрузки опросов: {e}")
    
    def load_respondents(self):
        """Загрузить список респондентов."""
        try:
            respondents_list = respondents.get_all()
            respondent_items = [f"{r['id_respondenta']}: {int(r.get('age', 0))} лет, {r['region']}" for r in respondents_list]
            self.respondent_combo['values'] = respondent_items
        except Exception as e:
            show_error(self, f"Ошибка загрузки респондентов: {e}")
    
    def on_survey_selected(self, event=None):
        """Обработчик выбора опроса."""
        selection = self.survey_var.get()
        if selection:
            opros_id = int(selection.split(':')[0])
            self.current_opros_id = opros_id
            self.check_ready()
    
    def on_respondent_selected(self, event=None):
        """Обработчик выбора респондента."""
        selection = self.respondent_var.get()
        if selection:
            respondent_id = int(selection.split(':')[0])
            self.current_respondent_id = respondent_id
            self.check_ready()
    
    def check_ready(self):
        """Проверить, готовы ли опрос и респондент, и автоматически загрузить вопросы."""
        if self.current_opros_id and self.current_respondent_id:
            self.start_btn.config(state='normal')
            # Автоматически загружаем вопросы и показываем первый
            self.auto_load_survey()
        else:
            self.start_btn.config(state='disabled')
    
    def auto_load_survey(self):
        """Автоматически загрузить опрос при выборе опроса и респондента."""
        if not self.current_opros_id or not self.current_respondent_id:
            return
        
        try:
            # Проверяем или создаём UCHASTIE
            if not responses.has_uchastie(self.current_opros_id, self.current_respondent_id):
                try:
                    uchastie_id = responses.create_uchastie(self.current_opros_id, self.current_respondent_id)
                    if not uchastie_id:
                        return
                except ValueError as e:
                    # Уже участвует - это нормально
                    pass
            
            # Получаем все вопросы опроса
            voprosy_list = questions.get_by_opros(self.current_opros_id)
            
            if not voprosy_list:
                self.question_label.config(text="В этом опросе нет вопросов")
                return
            
            # Показываем все вопросы (включая уже отвеченные)
            self.current_voprosy = voprosy_list
            self.current_vopros_index = 0
            self.show_question()
            self.start_btn.config(state='disabled')
        except Exception as e:
            import traceback
            traceback.print_exc()
            show_error(self, f"Ошибка загрузки опроса: {e}")
    
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
                    self.load_respondents()
                    self.respondent_var.set(f"{respondent_id}: новый респондент")
                    self.current_respondent_id = respondent_id
                    self.check_ready()
            except Exception as e:
                show_error(self, f"Ошибка создания респондента: {e}")
    
    def start_survey(self):
        """Начать опрос. Создаёт запись в UCHASTIE и показывает первый вопрос."""
        self.auto_load_survey()
    
    def show_question(self):
        """Показать текущий вопрос."""
        if not self.current_voprosy or self.current_vopros_index >= len(self.current_voprosy):
            show_info(self, "Опрос завершён!")
            self.start_btn.config(state='normal')
            return
        
        vopros = self.current_voprosy[self.current_vopros_index]
        
        # Очищаем предыдущий вопрос
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # Показываем текст вопроса
        self.question_label.config(text=f"Вопрос {self.current_vopros_index + 1}/{len(self.current_voprosy)}: {vopros['tekst_voprosa']}")
        
        # Получаем варианты ответов
        variants = questions.get_variants(vopros['id_voprosa'])
        
        if not variants:
            self.question_label.config(text=f"Вопрос {self.current_vopros_index + 1}/{len(self.current_voprosy)}: {vopros['tekst_voprosa']}\n(Нет вариантов ответа)")
            return
        
        # Проверяем, не отвечен ли уже этот вопрос
        existing_otvet = None
        has_answered = responses.has_answered(
            self.current_respondent_id,
            self.current_opros_id,
            vopros['id_voprosa']
        )
        
        if has_answered:
            # Получаем уже выбранный ответ
            existing_otvety = responses.get_by_respondent_and_opros(
                self.current_respondent_id,
                self.current_opros_id
            )
            existing_otvet = next((ot for ot in existing_otvety if ot['id_voprosa'] == vopros['id_voprosa']), None)
        
        # Создаём радиокнопки для вариантов
        selected_variant_id = existing_otvet['id_varianta'] if existing_otvet else 0
        self.option_var.set(selected_variant_id)
        
        for variant in variants:
            rb = ttk.Radiobutton(
                self.options_frame,
                text=variant['tekst_varianta'],
                variable=self.option_var,
                value=variant['id_varianta']
            )
            rb.pack(anchor='w', pady=2)
        
        # Обновляем кнопки навигации
        self.prev_btn.config(state='normal' if self.current_vopros_index > 0 else 'disabled')
        self.next_btn.config(state='normal' if self.current_vopros_index < len(self.current_voprosy) - 1 else 'disabled')
        self.submit_btn.config(state='normal')
    
    def prev_question(self):
        """Перейти к предыдущему вопросу."""
        if self.current_vopros_index > 0:
            self.current_vopros_index -= 1
            self.show_question()
    
    def next_question(self):
        """Перейти к следующему вопросу."""
        if self.current_vopros_index < len(self.current_voprosy) - 1:
            self.current_vopros_index += 1
            self.show_question()

    def submit_answer(self):
        """Отправить ответ на текущий вопрос."""
        if not self.current_voprosy or self.current_vopros_index >= len(self.current_voprosy):
            return

        vopros = self.current_voprosy[self.current_vopros_index]
        variant_id = self.option_var.get()

        if variant_id == 0:
            show_error(self, "Выберите вариант ответа")
            return

        try:
            otvet_id = responses.create_or_update_otvet(
                self.current_opros_id,
                vopros['id_voprosa'],
                self.current_respondent_id,
                variant_id
            )

            if otvet_id:
                # Обновляем отображение вопроса, чтобы показать сохранённый ответ
                self.show_question()
                show_info(self, "Ответ сохранён")
        except ValueError as e:
            show_error(self, str(e))
        except Exception as e:
            import traceback
            traceback.print_exc()
            show_error(self, f"Ошибка сохранения ответа: {e}")
