"""
Окно для просмотра отчётов.
"""

import tkinter as tk
from tkinter import ttk
from app.repositories import surveys, reports
from app.ui.components.table import DataTable
from app.ui.components.dialogs import show_error, show_info, ask_save_file
from datetime import datetime


class ReportsWindow(ttk.Frame):
    """Окно отчётов."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса."""
        # Панель выбора отчёта
        report_frame = ttk.LabelFrame(self, text="Выбор отчёта")
        report_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(report_frame, text="a) Список всех опросов", 
                  command=self.show_all_surveys).pack(side=tk.LEFT, padx=2)
        ttk.Button(report_frame, text="b) Распределение ответов", 
                  command=self.show_answer_distribution).pack(side=tk.LEFT, padx=2)
        ttk.Button(report_frame, text="c) Динамика по теме", 
                  command=self.show_topic_dynamics).pack(side=tk.LEFT, padx=2)
        ttk.Button(report_frame, text="d) Статистика респондентов", 
                  command=self.show_respondent_statistics).pack(side=tk.LEFT, padx=2)
        ttk.Button(report_frame, text="e) Средний возраст", 
                  command=self.show_average_age).pack(side=tk.LEFT, padx=2)
        ttk.Button(report_frame, text="f) Опросы с >70% положительных", 
                  command=self.show_positive_surveys).pack(side=tk.LEFT, padx=2)
        ttk.Button(report_frame, text="g) XML-отчёт", 
                  command=self.generate_xml_report).pack(side=tk.LEFT, padx=2)
        
        # Таблица результатов
        self.table = None
        self.table_frame = ttk.Frame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def clear_table(self):
        """Очистить таблицу."""
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.table = None
    
    def show_table(self, columns, data):
        """Показать таблицу с данными."""
        self.clear_table()
        self.table = DataTable(self.table_frame, columns)
        self.table.pack(fill=tk.BOTH, expand=True)
        self.table.load_data(data)
    
    def show_all_surveys(self):
        """Отчёт a) Список всех опросов."""
        try:
            data = reports.get_all_surveys_list()
            columns = [
                {'name': 'ID', 'width': 50},
                {'name': 'Тема', 'width': 250},
                {'name': 'Начало', 'width': 100},
                {'name': 'Окончание (план)', 'width': 120},
                {'name': 'Окончание (факт)', 'width': 120},
                {'name': 'Статус', 'width': 100},
                {'name': 'Участников', 'width': 100}
            ]
            
            table_data = []
            for item in data:
                table_data.append({
                    'ID': item['id_oprosa'],
                    'Тема': item['tema'],
                    'Начало': str(item['data_nachala']),
                    'Окончание (план)': str(item['data_okonch_pln']),
                    'Окончание (факт)': str(item['data_okonch_fakt']) if item['data_okonch_fakt'] else '',
                    'Статус': item['status'],
                    'Участников': item['participants_count']
                })
            
            self.show_table(columns, table_data)
        except Exception as e:
            show_error(self, f"Ошибка загрузки отчёта: {e}")
    
    def show_answer_distribution(self):
        """Отчёт b) Распределение ответов."""
        # Выбор опроса
        surveys_list = surveys.get_all()
        if not surveys_list:
            show_error(self, "Нет доступных опросов")
            return
        
        survey_items = [f"{s['id_oprosa']}: {s['tema']}" for s in surveys_list]
        
        dialog = tk.Toplevel(self)
        dialog.title("Выбор опроса")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Выберите опрос:").pack(pady=10)
        survey_var = tk.StringVar()
        combo = ttk.Combobox(dialog, textvariable=survey_var, values=survey_items, 
                            state='readonly', width=40)
        combo.pack(pady=10)
        
        def ok():
            if survey_var.get():
                opros_id = int(survey_var.get().split(':')[0])
                dialog.destroy()
                self._show_answer_distribution(opros_id)
            else:
                show_error(dialog, "Выберите опрос")
        
        ttk.Button(dialog, text="OK", command=ok).pack(pady=10)
    
    def _show_answer_distribution(self, opros_id):
        """Показать распределение ответов для опроса."""
        try:
            data = reports.get_answer_distribution(opros_id)
            columns = [
                {'name': 'Вопрос', 'width': 300},
                {'name': 'Вариант ответа', 'width': 200},
                {'name': 'Количество', 'width': 100},
                {'name': 'Процент', 'width': 100},
                {'name': 'Положительный', 'width': 100}
            ]
            
            table_data = []
            for item in data:
                table_data.append({
                    'Вопрос': item['tekst_voprosa'],
                    'Вариант ответа': item['tekst_varianta'],
                    'Количество': item['answer_count'],
                    'Процент': f"{item['percentage']:.2f}%" if item['percentage'] else "0%",
                    'Положительный': 'Да' if item['priznak_polozh'] == 1 else 'Нет'
                })
            
            self.show_table(columns, table_data)
        except Exception as e:
            show_error(self, f"Ошибка загрузки отчёта: {e}")
    
    def show_topic_dynamics(self):
        """Отчёт c) Динамика по теме."""
        # Получаем список тем
        surveys_list = surveys.get_all()
        topics = list(set(s['tema'] for s in surveys_list))
        
        if not topics:
            show_error(self, "Нет доступных тем")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("Выбор темы")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Выберите тему:").pack(pady=10)
        topic_var = tk.StringVar()
        combo = ttk.Combobox(dialog, textvariable=topic_var, values=topics, 
                            state='readonly', width=40)
        combo.pack(pady=10)
        
        def ok():
            if topic_var.get():
                topic = topic_var.get()
                dialog.destroy()
                self._show_topic_dynamics(topic)
            else:
                show_error(dialog, "Выберите тему")
        
        ttk.Button(dialog, text="OK", command=ok).pack(pady=10)
    
    def _show_topic_dynamics(self, topic):
        """Показать динамику по теме."""
        try:
            data = reports.get_topic_dynamics(topic)
            columns = [
                {'name': 'Неделя', 'width': 120},
                {'name': 'Положительных', 'width': 120},
                {'name': 'Всего ответов', 'width': 120},
                {'name': 'Процент положительных', 'width': 150}
            ]
            
            table_data = []
            for item in data:
                table_data.append({
                    'Неделя': str(item['week_start']),
                    'Положительных': item['positive_count'],
                    'Всего ответов': item['total_count'],
                    'Процент положительных': f"{item['positive_percentage']:.2f}%" if item['positive_percentage'] else "0%"
                })
            
            self.show_table(columns, table_data)
        except Exception as e:
            show_error(self, f"Ошибка загрузки отчёта: {e}")
    
    def show_respondent_statistics(self):
        """Отчёт d) Статистика респондентов."""
        try:
            data = reports.get_respondent_statistics()
            columns = [
                {'name': 'ID', 'width': 50},
                {'name': 'Возраст', 'width': 70},
                {'name': 'Пол', 'width': 80},
                {'name': 'Регион', 'width': 150},
                {'name': 'Образование', 'width': 150},
                {'name': 'Опросов', 'width': 80},
                {'name': 'Ответов', 'width': 80}
            ]
            
            table_data = []
            for item in data:
                table_data.append({
                    'ID': item['id_respondenta'],
                    'Возраст': int(item['age']) if item['age'] else '',
                    'Пол': item['gender'],
                    'Регион': item['region'],
                    'Образование': item['education_level'],
                    'Опросов': item['surveys_count'],
                    'Ответов': item['total_answers_count']
                })
            
            self.show_table(columns, table_data)
        except Exception as e:
            show_error(self, f"Ошибка загрузки отчёта: {e}")
    
    def show_average_age(self):
        """Отчёт e) Средний возраст участников."""
        try:
            data = reports.get_average_age_by_survey()
            columns = [
                {'name': 'ID опроса', 'width': 80},
                {'name': 'Тема', 'width': 250},
                {'name': 'Участников', 'width': 100},
                {'name': 'Средний возраст', 'width': 120},
                {'name': 'Мин. возраст', 'width': 100},
                {'name': 'Макс. возраст', 'width': 100}
            ]
            
            table_data = []
            for item in data:
                table_data.append({
                    'ID опроса': item['id_oprosa'],
                    'Тема': item['tema'],
                    'Участников': item['participants_count'],
                    'Средний возраст': f"{item['average_age']:.2f}" if item['average_age'] else '',
                    'Мин. возраст': int(item['min_age']) if item['min_age'] else '',
                    'Макс. возраст': int(item['max_age']) if item['max_age'] else ''
                })
            
            self.show_table(columns, table_data)
        except Exception as e:
            show_error(self, f"Ошибка загрузки отчёта: {e}")
    
    def show_positive_surveys(self):
        """Отчёт f) Опросы с >70% положительных ответов."""
        try:
            data = reports.get_positive_surveys(70.0)
            columns = [
                {'name': 'ID', 'width': 50},
                {'name': 'Тема', 'width': 250},
                {'name': 'Начало', 'width': 100},
                {'name': 'Окончание (план)', 'width': 120},
                {'name': 'Положительных', 'width': 120},
                {'name': 'Всего', 'width': 80},
                {'name': 'Процент', 'width': 100}
            ]
            
            table_data = []
            for item in data:
                table_data.append({
                    'ID': item['id_oprosa'],
                    'Тема': item['tema'],
                    'Начало': str(item['data_nachala']),
                    'Окончание (план)': str(item['data_okonch_pln']),
                    'Положительных': item['positive_count'],
                    'Всего': item['total_count'],
                    'Процент': f"{item['positive_percentage']:.2f}%" if item['positive_percentage'] else "0%"
                })
            
            self.show_table(columns, table_data)
        except Exception as e:
            show_error(self, f"Ошибка загрузки отчёта: {e}")
    
    def generate_xml_report(self):
        """Отчёт g) Генерация XML-отчёта."""
        surveys_list = surveys.get_all()
        if not surveys_list:
            show_error(self, "Нет доступных опросов")
            return
        
        survey_items = [f"{s['id_oprosa']}: {s['tema']}" for s in surveys_list]
        
        dialog = tk.Toplevel(self)
        dialog.title("Выбор опроса для XML-отчёта")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Выберите опрос:").pack(pady=10)
        survey_var = tk.StringVar()
        combo = ttk.Combobox(dialog, textvariable=survey_var, values=survey_items, 
                            state='readonly', width=40)
        combo.pack(pady=10)
        
        def ok():
            if survey_var.get():
                opros_id = int(survey_var.get().split(':')[0])
                dialog.destroy()
                self._generate_xml_report(opros_id)
            else:
                show_error(dialog, "Выберите опрос")
        
        ttk.Button(dialog, text="OK", command=ok).pack(pady=10)
    
    def _generate_xml_report(self, opros_id):
        """Сгенерировать и сохранить XML-отчёт."""
        try:
            xml_content = reports.generate_xml_report(opros_id)
            
            if not xml_content:
                show_error(self, "Не удалось сгенерировать XML-отчёт")
                return
            
            # Преобразуем XML в строку, если это не строка
            if hasattr(xml_content, '__str__'):
                xml_str = str(xml_content)
            else:
                xml_str = xml_content
            
            # Предлагаем сохранить файл
            filename = ask_save_file(self, f"opros_{opros_id}_report.xml")
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(xml_str)
                show_info(self, f"XML-отчёт сохранён: {filename}")
        except Exception as e:
            show_error(self, f"Ошибка генерации XML-отчёта: {e}")
