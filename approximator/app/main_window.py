# Путь: approximator/app/main_window.py

from approximator.utils.log import debug

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget

# Модели и виджеты
from approximator.data_models.app_state import AppState
from approximator.ui.tabs.import_tab import ImportTab
from approximator.ui.tabs.analysis_tab import AnalysisTab
from approximator.ui.tabs.export_tab import ExportTab
from approximator.services.plot.plot_manager import PlotManager

# Сервисы
from approximator.services.data_loader import DataLoader
from approximator.services.data_merger import DataMerger
from approximator.services.approximation.polynomial_fitter import PolynomialFitter

# Парсеры
from approximator.file_parsers.excel_parser import ExcelParser

# Обработчики UI
from approximator.ui.handlers.import_event_handler import ImportEventHandler
from approximator.ui.handlers.analysis_handler import AnalysisEventHandler
from approximator.ui.handlers.analysis_setup_handler import AnalysisSetupHandler
from approximator.ui.handlers.segment_mouse_handler import SegmentMouseHandler
from approximator.ui.handlers.segment_table_handler import SegmentTableHandler

from approximator.ui.setup.handler_initializer import create_handlers

class MainWindow(QMainWindow):
    """Главное окно приложения."""
    def __init__(self):
        super().__init__()

        # Инициализируем состояние
        self.state = AppState()

        # Инициализация базовых компонентов
        self.setWindowTitle("Аппроксиматор")
        self.setGeometry(100, 100, 1200, 800)
        
        # Создаем главный виджет и layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Инициализируем сервисы
        from approximator.file_parsers.generic_csv_parser import GenericCsvParser
        from approximator.file_parsers.excel_parser import ExcelParser
        from approximator.file_parsers.adc_parser import AdcParser
        
        # Важен порядок: специализированные парсеры должны идти перед общими
        self.data_loader = DataLoader([
            AdcParser(),      # Парсер для файлов АЦП
            ExcelParser(),    # Парсер для Excel
            GenericCsvParser() # Общий парсер CSV (должен быть последним)
        ])
        self.data_merger = DataMerger()
        self.fitter = PolynomialFitter()

        # Создаем вкладки
        self.tabs = QTabWidget()
        self.import_tab = ImportTab(self)
        self.analysis_tab = AnalysisTab(self)
        self.export_tab = ExportTab(self)
        
        # Добавляем вкладки
        self.tabs.addTab(self.import_tab, "Импорт")
        self.tabs.addTab(self.analysis_tab, "Анализ")
        self.tabs.addTab(self.export_tab, "Экспорт")
        self.layout.addWidget(self.tabs)
        
        # Отключаем вкладки анализа и экспорта до загрузки данных
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        
        # Инициализируем plot_manager
        self.plot_manager = PlotManager(self.analysis_tab.plot_widget)
        
        # Создаем обработчики
        create_handlers(self)
        # создаем контроллер приложения
        from  approximator.services.project_state_controller import ProjectStateController
        self.project_controller = ProjectStateController(self)
        try:
            self.project_controller.load_project("state.json")
            debug("[MainWindow] ✅ Состояние проекта восстановлено")
        except Exception as e:
            debug(f"[MainWindow] ⚠️ Не удалось восстановить состояние: {e}")

    def request_recalculation(self):
        """Запускает пересчет аппроксимаций."""
        print("[request_recalculation] Requesting recalculation")
        if hasattr(self, 'segment_table_handler'):
            self.segment_table_handler._fit_segments()  # Только пересчет, без обновления UI

    def closeEvent(self, event):
        """Автосохранение состояния при закрытии приложения."""
        try:
            self.project_controller.save_project("state.json")
            print("[MainWindow] 💾 Состояние проекта сохранено")
        except Exception as e:
            print(f"[MainWindow] ⚠️ Ошибка при сохранении состояния: {e}")
        event.accept()

