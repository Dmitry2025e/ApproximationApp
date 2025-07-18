# Путь: ui/tabs/import_tab.py
# =================================================================================
# МОДУЛЬ ВКЛАДКИ "ИМПОРТ"
# =================================================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QLabel, QSplitter, QMessageBox, QFileDialog, QPushButton
)
from PyQt5.QtCore import Qt
import os
import json

from approximator.ui.components.time_column_selector import TimeColumnSelector
from approximator.ui.components.file_list_panel import FileListPanel
from approximator.ui.components.preview_table_panel import PreviewTablePanel


class ImportTab(QWidget):
    """Виджет для вкладки 'Импорт'."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        # --- Компоненты ---
        self.file_panel = FileListPanel()
        self.merge_and_load_button = QPushButton("4. Объединить и загрузить")  # ✅ Вернули кнопку
        self.time_selector = TimeColumnSelector()
        self.preview_panel = PreviewTablePanel()

        self.settings_table = QTableWidget()  # Задел на будущее

        # --- Компоновка ---
        top_left_widget = QWidget()
        top_left_layout = QVBoxLayout(top_left_widget)
        top_left_layout.setContentsMargins(0, 0, 0, 0)
        top_left_layout.addWidget(self.file_panel)
        top_left_layout.addWidget(self.merge_and_load_button)  # ✅ Добавили в layout

        bottom_left_widget = QWidget()
        bottom_left_layout = QVBoxLayout(bottom_left_widget)
        bottom_left_layout.setContentsMargins(0, 0, 0, 0)
        bottom_left_layout.addWidget(self.time_selector)
        bottom_left_layout.addWidget(QLabel("Настройки колонок (в будущем):"))
        bottom_left_layout.addWidget(self.settings_table)

        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.addWidget(top_left_widget)
        left_splitter.addWidget(bottom_left_widget)
        left_splitter.setSizes([350, 250])

        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        right_panel_layout.addWidget(QLabel("Предпросмотр данных:"))
        right_panel_layout.addWidget(self.preview_panel)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_panel_widget)
        main_splitter.setSizes([450, 750])
        main_splitter.setStretchFactor(1, 1)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

        # Подключение обработчика для кнопки загрузки проекта
        self.file_panel.load_project_button = self._create_load_project_button()
        self.file_panel.layout().insertWidget(2, self.file_panel.load_project_button)
        self.file_panel.load_project_button.clicked.connect(self._handle_load_project)

    def _create_load_project_button(self):
        return QPushButton("Открыть проект")

    def _handle_load_project(self):
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'import_event_handler'):
            main_window = main_window.parent()
        if not main_window or not hasattr(main_window, 'import_event_handler'):
            QMessageBox.warning(self, 'Ошибка', 'Не удалось получить обработчик импорта.')
            return

        handler = main_window.import_event_handler
        app_state = main_window.state

        file_path, _ = QFileDialog.getOpenFileName(self, 'Открыть проект', '', 'JSON Files (*.json)')
        if not file_path:
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        imported_files = data.get('imported_files', [])
        handler._handle_reset_import()
        handler._selected_file_paths = list(imported_files)
        handler._update_file_list_widget()
        handler._update_time_column_combo()

        loaded_dfs = {}
        for fpath in imported_files:
            if not os.path.exists(fpath):
                QMessageBox.warning(self, 'Ошибка', f'Файл не найден: {fpath}')
                continue
            try:
                df = handler.data_loader.load_file(fpath)
                if not df.empty:
                    loaded_dfs[fpath] = df
            except Exception as e:
                print(f"Ошибка загрузки файла {fpath}: {e}")
        app_state.loaded_dataframes = loaded_dfs

        settings = data.get('settings', {})
        time_column_saved = settings.get('time_column')
        if time_column_saved:
            self.time_selector.set_selected(time_column_saved)
            for fpath in imported_files:
                app_state.selected_columns[fpath] = time_column_saved

        handler._handle_merge_and_load()

        from approximator.data_models.channel_state import ChannelState
        app_state.channel_states.clear()
        for ch, ch_data in data.get('channels', {}).items():
            app_state.channel_states[ch] = ChannelState.from_dict(ch_data)

        app_state.active_channel_name = settings.get('active_channel', '')
        app_state.selected_segment_index = settings.get('selected_segment_index')
        app_state.show_source_data = settings.get('show_source_data', True)
        app_state.show_approximation = settings.get('show_approximation', True)
        app_state.auto_recalculate = settings.get('auto_recalculate', True)

        if hasattr(main_window, 'analysis_setup_handler'):
            main_window.analysis_setup_handler.update_channels_table()
        if hasattr(main_window, 'segment_table_handler'):
            main_window.segment_table_handler.update_table()
        if hasattr(main_window, 'plot_manager'):
            time_column = self.time_selector.get_selected()
            if not time_column and app_state.merged_dataframe is not None and not app_state.merged_dataframe.empty:
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

        handler._update_time_column_combo()

        if imported_files:
            list_widget = self.file_panel.list_widget
            for i in range(list_widget.count()):
                if list_widget.item(i).text() == imported_files[0]:
                    list_widget.setCurrentRow(i)
                    break

        QMessageBox.information(self, 'Загрузка', 'Проект успешно загружен!')