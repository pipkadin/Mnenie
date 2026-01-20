"""
Главный модуль приложения.
Точка входа в программу.
"""

import tkinter as tk
from tkinter import ttk
from app.db import init_pool, close_pool
from app.ui.windows.surveys_window import SurveysWindow
from app.ui.windows.questions_window import QuestionsWindow
from app.ui.windows.respondents_window import RespondentsWindow
from app.ui.windows.conduct_survey_window import ConductSurveyWindow
from app.ui.windows.reports_window import ReportsWindow
from app.ui.components.dialogs import show_error


class MainApplication(tk.Tk):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Система изучения общественного мнения")
        self.geometry("1200x800")
        
        # Инициализация БД
        try:
            init_pool()
        except Exception as e:
            show_error(self, f"Ошибка подключения к БД: {e}")
            self.destroy()
            return
        
        self.setup_ui()
        
        # Обработчик закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Настройка интерфейса."""
        # Создаём вкладки
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка 1: Опросы
        surveys_tab = SurveysWindow(notebook)
        notebook.add(surveys_tab, text="Опросы")
        
        # Вкладка 2: Вопросы
        questions_tab = QuestionsWindow(notebook)
        notebook.add(questions_tab, text="Вопросы")
        
        # Вкладка 3: Респонденты
        respondents_tab = RespondentsWindow(notebook)
        notebook.add(respondents_tab, text="Респонденты")
        
        # Вкладка 4: Прохождение опроса
        conduct_tab = ConductSurveyWindow(notebook)
        notebook.add(conduct_tab, text="Прохождение опроса")
        
        # Вкладка 5: Отчёты
        reports_tab = ReportsWindow(notebook)
        notebook.add(reports_tab, text="Отчёты")
    
    def on_closing(self):
        """Обработчик закрытия приложения."""
        close_pool()
        self.destroy()


def main():
    """Точка входа."""
    app = MainApplication()
    app.mainloop()


if __name__ == "__main__":
    main()
