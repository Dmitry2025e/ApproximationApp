# Путь: approximator/app/main_window.py

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
        
        # Инициализируем состояние
        self.state = AppState()
        
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


    def request_recalculation(self):
        """Запускает пересчет аппроксимаций."""
        print("[request_recalculation] Requesting recalculation")
        if hasattr(self, 'segment_table_handler'):
            self.segment_table_handler._fit_segments()  # Только пересчет, без обновления UI

    def _create_handlers_old(self):
        """Инициализирует все обработчики и связывает их через колбэки."""
        def redraw_plot(preserve_zoom: bool = False):
            if not hasattr(self, 'plot_manager') or not hasattr(self, 'state'): return
            
            time_column = None
            if hasattr(self.import_tab, 'time_column_combo'):
                time_column = self.import_tab.time_column_combo.currentText()
                
            if not time_column and self.state.merged_dataframe is not None and not self.state.merged_dataframe.empty:
                all_columns = self.state.merged_dataframe.columns
                if 'Time' in all_columns:
                    time_column = 'Time'
                else:
                    time_column = all_columns[0] if len(all_columns) > 0 else None
                    
            if time_column:
                print(f"[redraw_plot] Redrawing with time_column={time_column}, preserve_zoom={preserve_zoom}")
                self.plot_manager.redraw_all_channels(
                    df=self.state.merged_dataframe,
                    x_col=time_column,
                    channel_states=self.state.channel_states,
                    active_channel_name=self.state.active_channel_name,
                    selected_segment_index=self.state.selected_segment_index,
                    preserve_zoom=preserve_zoom,
                    show_source=self.state.show_source_data,
                    show_approximation=self.state.show_approximation
                )

                # ✅ Встраиваем интерактивные границы сегментов
                if hasattr(self, 'segment_mouse_handler'):
                    self.segment_mouse_handler._rebuild_boundaries()

        # Setup handlers first
        self.analysis_setup_handler = AnalysisSetupHandler(
            self, self.state,
            redraw_callback=redraw_plot,
            update_segments_table_callback=lambda: self.segment_table_handler.update_table() if hasattr(self, 'segment_table_handler') else None,
            update_channels_callback=lambda: self.analysis_setup_handler.update_channels_table() if hasattr(self, 'analysis_setup_handler') else None
        )

        def analysis_reset():
            """Сброс состояния анализа."""
            if hasattr(self, 'analysis_setup_handler'):
                self.analysis_setup_handler.update_channels_table()
            if hasattr(self, 'segment_table_handler'):
                self.segment_table_handler.update_table()
            if hasattr(self, 'plot_manager'):
                redraw_plot(preserve_zoom=False)
        
        # Create Import handler with all dependencies
        self.import_event_handler = ImportEventHandler(
            main_window=self,
            app_state=self.state,
            data_loader=self.data_loader,
            data_merger=self.data_merger,
            analysis_setup_handler=self.analysis_setup_handler,
            analysis_reset_callback=analysis_reset
        )
        
        # Segment handlers
        self.segment_table_handler = SegmentTableHandler(
            self, self.state, self.fitter,
            redraw_callback=redraw_plot,
            update_table_callback=lambda: self.segment_table_handler.update_table() if hasattr(self, 'segment_table_handler') else None,
            get_stitch_params=lambda: {'enabled': False, 'method': 1}
        )
        
        # Mouse handler
        self.segment_mouse_handler = SegmentMouseHandler(
            state = self.state,
            plot_manager = self.plot_manager,
            redraw_callback=redraw_plot,
            update_table_callback=lambda: self.segment_table_handler.update_table() if hasattr(self, 'segment_table_handler') else None,
            request_recalc_callback=self.request_recalculation
        )