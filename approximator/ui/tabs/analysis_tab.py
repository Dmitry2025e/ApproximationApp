# Путь: approximator/ui/tabs/analysis_tab.py
# =================================================================================
# МОДУЛЬ ВКЛАДКИ "АНАЛИЗ"
# =================================================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSplitter, QTableWidget, QHeaderView, 
                             QPushButton, QCheckBox, QComboBox, QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

class AnalysisTab(QWidget):
    def _on_stitch_checkbox_changed(self, state):
        # Включение/отключение комбобокса выбора метода сшивки
        self.stitch_method_combo.setEnabled(state == Qt.Checked)
        # При изменении состояния чекбокса сразу пересчитываем, если есть обработчик
        if hasattr(self, 'calculate_button'):
            self.calculate_button.click()
    def recreate_layout(self):
        # Удаляем старый layout у self
        old_layout = self.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)  # Открепить layout от self
        self._init_ui()
    def _save_project(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import json
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'state'):
            main_window = main_window.parent()
        if not main_window:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось получить состояние приложения.')
            return
        app_state = main_window.state
        # Получаем список файлов из вкладки Импорт
        imported_files = []
        if hasattr(main_window, 'import_tab') and hasattr(main_window.import_tab, 'file_list_widget'):
            imported_files = [main_window.import_tab.file_list_widget.item(i).text() for i in range(main_window.import_tab.file_list_widget.count())]
        # Сохраняем выбранную колонку времени
        time_column = None
        if hasattr(main_window, 'import_tab') and hasattr(main_window.import_tab, 'time_column_combo'):
            time_column = main_window.import_tab.time_column_combo.currentText()
        data = {
            'channels': {
                ch: {
                    'segments': [
                        {
                            'x_start': seg.x_start,
                            'x_end': seg.x_end,
                            'poly_degree': seg.poly_degree,
                            'color': seg.color,
                            'line_style': getattr(seg, 'line_style', '-'),
                            'thickness': getattr(seg, 'thickness', 1.0),
                            'is_excluded': getattr(seg, 'is_excluded', False),
                            'is_mask': getattr(seg, 'is_mask', False),
                            'fit_result': seg.fit_result.to_dict() if hasattr(seg, 'fit_result') and seg.fit_result else None
                        } for seg in ch_state.segments
                    ]
                } for ch, ch_state in app_state.channel_states.items()
            },
            'settings': {
                'active_channel': app_state.active_channel_name,
                'selected_segment_index': app_state.selected_segment_index,
                'show_source_data': app_state.show_source_data,
                'show_approximation': app_state.show_approximation,
                'auto_recalculate': app_state.auto_recalculate,
                'time_column': time_column
            },
            'imported_files': imported_files
        }
        file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить проект', '', 'JSON Files (*.json)')
        if not file_path:
            return
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, 'Сохранение', 'Проект успешно сохранён!')

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Создаем виджет для графика
        self.figure = Figure()
        self.plot_widget = FigureCanvas(self.figure)
        self.plot_widget.setMinimumSize(400, 300)
        self.toolbar = NavigationToolbar2QT(self.plot_widget, self)
        
        # Создаем таблицы
        self.channels_table = QTableWidget()
        self.segments_table = QTableWidget()
        
        # Создаем кнопки управления каналами
        self.show_all_channels_button = QPushButton("Показать все")
        self.hide_all_channels_button = QPushButton("Скрыть все")
        self.calculate_button = QPushButton("Рассчитать")
        self.restore_excluded_button = QPushButton("Восстановить вырезанное")
        
        # Кнопки управления проектом
        self.save_project_button = QPushButton("Сохранить проект")
        self.load_project_button = QPushButton("Загрузить проект")
        
        # Кнопки управления режимом
        self.cut_mode_button = QPushButton("Режим: Анализ")
        self.cut_mode_button.setCheckable(True)
        self.cut_mode_button.setFixedWidth(120)
        
        # Кнопки управления сегментами
        self.merge_segment_button = QPushButton("Объединить")
        self.remove_segment_button = QPushButton("Удалить")
        self.reset_segments_button = QPushButton("Сбросить")
        
        # Элементы управления сшивкой
        self.stitch_checkbox = QCheckBox("Плавная сшивка")
        self.stitch_checkbox.setChecked(False)
        self.stitch_method_combo = QComboBox()
        self.stitch_method_combo.addItems([
            "C0 (по значению)",
            "C1 (значение+производная)",
            "C2 (значение+1-я+2-я производная)"
        ])
        self.stitch_method_combo.setCurrentIndex(1)
        self.stitch_method_combo.setEnabled(False)
        
        # Чекбоксы отображения
        self.show_source_checkbox = QCheckBox("Исходные")
        self.show_source_checkbox.setChecked(True)
        self.show_approx_checkbox = QCheckBox("Аппроксимация")
        self.show_approx_checkbox.setChecked(True)
        self.auto_recalc_checkbox = QCheckBox("Автопересчет")
        self.auto_recalc_checkbox.setChecked(True)
        
        # Поле смещения
        self.offset_input = QLineEdit("0")
        self.offset_input.setFixedWidth(100)
        
        # Инициализируем UI
        self._init_ui()
        
        # Подключаем обработчик изменения состояния чекбокса сшивки
        self.stitch_checkbox.stateChanged.connect(self._on_stitch_checkbox_changed)

    def _init_ui(self):
        """Инициализация интерфейса вкладки анализа."""
        self.channels_table.setColumnCount(4)
        self.channels_table.setHorizontalHeaderLabels(["Канал", "Показывать?", "Смещение, с", "Цвет"])
        self.channels_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.channels_table.setSelectionMode(QTableWidget.SingleSelection)
        self.channels_table.setMaximumHeight(250)
        header_channels = self.channels_table.horizontalHeader()
        header_channels.setSectionResizeMode(QHeaderView.Interactive)
        header_channels.resizeSection(0, 120)

        self.segments_table.setColumnCount(7)
        self.segments_table.setHorizontalHeaderLabels(["Сегмент", "Степень", "Исключить?", "Цвет", "RMSE", "R²", "N точек"])
        header_segments = self.segments_table.horizontalHeader()
        header_segments.setSectionResizeMode(QHeaderView.Interactive)

        toolbar_layout_1 = QHBoxLayout()
        toolbar_layout_1.addWidget(self.show_all_channels_button)
        toolbar_layout_1.addWidget(self.hide_all_channels_button)
        toolbar_layout_1.addWidget(self.calculate_button)
        toolbar_layout_1.addWidget(self.restore_excluded_button)
        toolbar_layout_1.addSpacing(20)
        toolbar_layout_1.addWidget(self.save_project_button)
        toolbar_layout_1.addWidget(self.load_project_button)
        toolbar_layout_1.addStretch()
        self.save_project_button.clicked.connect(self._save_project)
        self.load_project_button.clicked.connect(self._load_project)

        toolbar_layout_2 = QHBoxLayout()
        toolbar_layout_2.addStretch()
        toolbar_layout_2.addWidget(self.stitch_checkbox)
        toolbar_layout_2.addWidget(self.stitch_method_combo)
        toolbar_layout_2.addWidget(self.show_source_checkbox)
        toolbar_layout_2.addWidget(self.show_approx_checkbox)
        toolbar_layout_2.addWidget(self.auto_recalc_checkbox)
        toolbar_layout_2.addSpacing(20)
        toolbar_layout_2.addWidget(self.cut_mode_button)

        segments_toolbar_layout = QHBoxLayout()
        segments_toolbar_layout.addWidget(self.merge_segment_button)
        segments_toolbar_layout.addWidget(self.remove_segment_button)
        segments_toolbar_layout.addWidget(self.reset_segments_button)
        segments_toolbar_layout.addStretch()
        
        # Подключаем обработчики кнопок управления сегментами
        self.merge_segment_button.clicked.connect(
            lambda: self.parent().segment_table_handler.merge_selected_segments() if hasattr(self.parent(), 'segment_table_handler') else None
        )
        self.remove_segment_button.clicked.connect(
            lambda: self.parent().segment_table_handler.delete_selected_segments() if hasattr(self.parent(), 'segment_table_handler') else None
        )
        self.reset_segments_button.clicked.connect(
            lambda: self.parent().segment_table_handler.reset_segments() if hasattr(self.parent(), 'segment_table_handler') else None
        )

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.addWidget(self.toolbar)
        left_layout.addWidget(self.plot_widget)

        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.addWidget(QLabel("Управление каналами:"))
        right_panel_layout.addLayout(toolbar_layout_1)
        right_panel_layout.addLayout(toolbar_layout_2)
        right_panel_layout.addWidget(self.channels_table)
        right_panel_layout.addWidget(QLabel("Управление сегментами для активного канала:"))
        right_panel_layout.addLayout(segments_toolbar_layout)
        right_panel_layout.addWidget(self.segments_table)
        right_panel.setMinimumWidth(450)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 0)

        main_layout = QVBoxLayout()
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

    def _load_project(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import json
        from data_models.channel_state import ChannelState
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'state'):
            main_window = main_window.parent()
        if not main_window:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось получить состояние приложения.')
            return
        app_state = main_window.state
        file_path, _ = QFileDialog.getOpenFileName(self, 'Открыть проект', '', 'JSON Files (*.json)')
        if not file_path:
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Восстанавливаем каналы
        app_state.channel_states.clear()
        for ch, ch_data in data.get('channels', {}).items():
            app_state.channel_states[ch] = ChannelState.from_dict(ch_data)
        # Восстанавливаем настройки
        settings = data.get('settings', {})
        app_state.active_channel_name = settings.get('active_channel', '')
        app_state.selected_segment_index = settings.get('selected_segment_index')
        app_state.show_source_data = settings.get('show_source_data', True)
        app_state.show_approximation = settings.get('show_approximation', True)
        app_state.auto_recalculate = settings.get('auto_recalculate', True)
        # Восстанавливаем список импортированных файлов на вкладке Импорт
        imported_files = data.get('imported_files', [])
        if hasattr(main_window, 'import_tab') and hasattr(main_window.import_tab, 'file_list_widget'):
            main_window.import_tab.file_list_widget.clear()
            for f in imported_files:
                main_window.import_tab.file_list_widget.addItem(f)
        # Автоматически загружаем файлы и обновляем merged_dataframe, channel_list, таблицы и график
        # 1. Загружаем файлы через data_loader
        if hasattr(main_window, 'data_loader') and hasattr(main_window, 'data_merger'):
            loaded_dfs = {}
            for f in imported_files:
                try:
                    df = main_window.data_loader.load_file(f)
                    if not df.empty:
                        loaded_dfs[f] = df
                except Exception as e:
                    print(f"Ошибка загрузки файла {f}: {e}")
            app_state.loaded_dataframes = loaded_dfs
            # 2. Объединяем данные
            if loaded_dfs:
                # Определяем колонку времени (пытаемся взять ту, что была выбрана ранее, иначе первую попавшуюся)
                all_columns = set()
                for df in loaded_dfs.values():
                    all_columns.update(df.columns)
                time_column = None
                if hasattr(main_window.import_tab, 'time_column_combo'):
                    time_column = main_window.import_tab.time_column_combo.currentText()
                if not time_column or time_column not in all_columns:
                    # fallback: ищем 'Time' или первую колонку
                    if 'Time' in all_columns:
                        time_column = 'Time'
                    else:
                        time_column = list(all_columns)[0] if all_columns else None
                if time_column:
                    merged_df = main_window.data_merger.merge_dataframes(list(loaded_dfs.values()), on_column=time_column)
                    app_state.merged_dataframe = merged_df
                    # Восстанавливаем channel_list
                    channel_names = [col for col in merged_df.columns if col != time_column]
                    app_state.channel_list = channel_names
        # 3. Обновляем таблицы и график
        if hasattr(main_window, 'analysis_setup_handler'):
            main_window.analysis_setup_handler.update_channels_table()
        if hasattr(main_window, 'segment_table_handler'):
            main_window.segment_table_handler.update_table()
        if hasattr(main_window, 'plot_manager'):
            # Перерисовать график с границами сегментов
            time_column = None
            if hasattr(main_window.import_tab, 'time_column_combo'):
                time_column = main_window.import_tab.time_column_combo.currentText()
            if not time_column and app_state.merged_dataframe is not None and not app_state.merged_dataframe.empty:
                # fallback: ищем 'Time' или первую колонку
                all_columns = app_state.merged_dataframe.columns
                if 'Time' in all_columns:
                    time_column = 'Time'
                else:
                    time_column = all_columns[0] if len(all_columns) > 0 else None
            if time_column:
                main_window.plot_manager.redraw_all_channels(
                    df=app_state.merged_dataframe,
                    x_col=time_column,
                    channel_states=app_state.channel_states,
                    active_channel_name=app_state.active_channel_name,
                    selected_segment_index=app_state.selected_segment_index,
                    preserve_zoom=False,
                    show_source=app_state.show_source_data,
                    show_approximation=app_state.show_approximation
                )
                # Нарисовать границы сегментов для активного канала
                active = app_state.active_channel_name
                if active and active in app_state.channel_states:
                    segments = app_state.channel_states[active].segments
                    ax = main_window.plot_manager.ax
                    for seg in segments:
                        x = seg.x_start
                        ax.axvline(x, color='k', linestyle=':', alpha=0.5)
                    if segments:
                        ax.axvline(segments[-1].x_end, color='k', linestyle=':', alpha=0.5)
                    main_window.plot_manager.canvas.draw()
        QMessageBox.information(self, 'Загрузка', 'Проект успешно загружен!')
    def update_controls(self):
        """Обновляет состояние элементов управления на основе текущего состояния."""
        # Обновляем состояние чекбоксов отображения
        if hasattr(self.parent(), 'state'):
            state = self.parent().state
            self.show_source_checkbox.setChecked(state.show_source_data)
            self.show_approx_checkbox.setChecked(state.show_approximation)
            self.auto_recalc_checkbox.setChecked(state.auto_recalculate)
            
            # Обновляем состояние элементов управления сшивкой
            active_channel = state.active_channel_name
            if active_channel and active_channel in state.channel_states:
                channel_state = state.channel_states[active_channel]
                self.stitch_checkbox.setChecked(channel_state.stitch_enabled)
                self.stitch_method_combo.setCurrentIndex(channel_state.stitch_method)
                self.stitch_method_combo.setEnabled(channel_state.stitch_enabled)
            else:
                self.stitch_checkbox.setChecked(False)
                self.stitch_method_combo.setCurrentIndex(0)
                self.stitch_method_combo.setEnabled(False)

    def _setup_stitch_controls(self):
        """Настраивает элементы управления сшивкой."""
        self.stitch_checkbox = QCheckBox("Плавная сшивка")
        self.stitch_checkbox.setChecked(False)
        
        self.stitch_method_combo = QComboBox()
        self.stitch_method_combo.addItems(["C0 (значения)", "C1 (производные)", "C2 (вторые производные)"])
        self.stitch_method_combo.setCurrentIndex(1)  # C1 по умолчанию
        self.stitch_method_combo.setEnabled(False)
        
        # Подключаем сигналы к обработчикам
        main_window = self.parent()
        if hasattr(main_window, 'analysis_event_handler'):
            self.stitch_checkbox.stateChanged.connect(
                lambda state: main_window.analysis_event_handler._handle_stitch_state_change(state))
            self.stitch_method_combo.currentIndexChanged.connect(
                lambda idx: main_window.analysis_event_handler._handle_stitch_method_change(idx))
        
        stitch_layout = QHBoxLayout()
        stitch_layout.addWidget(self.stitch_checkbox)
        stitch_layout.addWidget(self.stitch_method_combo)
        stitch_layout.addStretch()
        return stitch_layout

    def _create_ui(self):
        """Создает пользовательский интерфейс вкладки."""
        main_layout = QVBoxLayout()
        
        # Настраиваем группу управления сшивкой
        stitch_group = QGroupBox("Параметры сшивки")
        stitch_group.setLayout(self._setup_stitch_controls())
        main_layout.addWidget(stitch_group)
        
        # ...existing code...