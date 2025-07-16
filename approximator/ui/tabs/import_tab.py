# Путь: ui/tabs/import_tab.py
# =================================================================================
# МОДУЛЬ ВКЛАДКИ "ИМПОРТ"
#
# НАЗНАЧЕНИЕ:
#   Определяет внешний вид и компоновку всех элементов на вкладке "Импорт".
#   - Панель для выбора файлов и управления списком.
#   - Панель для настроек импорта (выбор колонки времени).
#   - Таблица для предпросмотра данных.
#
# =================================================================================

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QTableWidget, QHeaderView, QLabel, 
                             QSplitter, QComboBox)
from PyQt5.QtCore import Qt
import os

class ImportTab(QWidget):
    """
    Виджет для вкладки "Импорт".
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        # --- Создание виджетов ---
        self.add_files_button = QPushButton("1. Добавить файлы...")
        print(f"DEBUG: ImportTab add_files_button id={id(self.add_files_button)}")
        self.preview_files_button = QPushButton("2. Показать в таблице")
        self.load_project_button = QPushButton("Открыть проект")
        self.merge_and_load_button = QPushButton("4. Объединить и загрузить")
        self.remove_selected_button = QPushButton("Удалить выбранный")
        self.reset_button = QPushButton("Очистить все")
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.time_column_combo = QComboBox()
        self.preview_table = QTableWidget()
        self.settings_table = QTableWidget() # Задел на будущее

        # --- Компоновка ---
        remove_buttons_layout = QHBoxLayout()
        remove_buttons_layout.addWidget(self.remove_selected_button)
        remove_buttons_layout.addWidget(self.reset_button)

        top_left_widget = QWidget()
        top_left_layout = QVBoxLayout(top_left_widget)
        top_left_layout.setContentsMargins(0, 0, 0, 0)
        top_left_layout.addWidget(self.add_files_button)
        top_left_layout.addWidget(self.preview_files_button)
        top_left_layout.addWidget(self.load_project_button)
        top_left_layout.addWidget(self.merge_and_load_button)
        top_left_layout.addWidget(self.file_list_widget)
        top_left_layout.addLayout(remove_buttons_layout)

        bottom_left_widget = QWidget()
        bottom_left_layout = QVBoxLayout(bottom_left_widget)
        bottom_left_layout.setContentsMargins(0, 0, 0, 0)
        bottom_left_layout.addWidget(QLabel("3. Выберите общую колонку времени:"))
        bottom_left_layout.addWidget(self.time_column_combo)
        bottom_left_layout.addWidget(QLabel("Настройки колонок (в будущем):"))
        bottom_left_layout.addWidget(self.settings_table)

        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.addWidget(top_left_widget)
        left_splitter.addWidget(bottom_left_widget)
        left_splitter.setSizes([350, 250])

        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        right_panel_layout.addWidget(QLabel("Предпросмотр данных:"))
        right_panel_layout.addWidget(self.preview_table)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_panel_widget)
        main_splitter.setSizes([450, 750])
        main_splitter.setStretchFactor(1, 1)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

        # Подключение обработчика для кнопки загрузки проекта
        self.load_project_button.clicked.connect(self._handle_load_project)

    def _handle_load_project(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import json
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
        # 1. Сбросить предыдущее состояние
        handler._handle_reset_import()
        # 2. Добавить файлы через обработчик (имитируем ручное добавление)
        handler._selected_file_paths = list(imported_files)
        handler._update_file_list_widget()
        handler._update_time_column_combo()
        # 3. Загрузить файлы (как при ручном добавлении)
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
        # 4. Восстановить выбранную колонку времени
        settings = data.get('settings', {})
        time_column_saved = settings.get('time_column')
        if time_column_saved:
            combo = main_window.import_tab.time_column_combo
            idx = combo.findText(time_column_saved)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        # 5. Вызвать объединение и загрузку (имитируем нажатие кнопки)
        handler._handle_merge_and_load()
        # 6. Восстановить состояние каналов и сегментов
        from data_models.channel_state import ChannelState
        app_state.channel_states.clear()
        for ch, ch_data in data.get('channels', {}).items():
            app_state.channel_states[ch] = ChannelState.from_dict(ch_data)
        app_state.active_channel_name = settings.get('active_channel', '')
        app_state.selected_segment_index = settings.get('selected_segment_index')
        app_state.show_source_data = settings.get('show_source_data', True)
        app_state.show_approximation = settings.get('show_approximation', True)
        app_state.auto_recalculate = settings.get('auto_recalculate', True)
        # 7. Обновить таблицы и график
        if hasattr(main_window, 'analysis_setup_handler'):
            main_window.analysis_setup_handler.update_channels_table()
        if hasattr(main_window, 'segment_table_handler'):
            main_window.segment_table_handler.update_table()
        if hasattr(main_window, 'plot_manager'):
            time_column = None
            if hasattr(main_window.import_tab, 'time_column_combo'):
                time_column = main_window.import_tab.time_column_combo.currentText()
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
        # Выбрать первую строку в списке файлов (для UI)
        if imported_files:
            list_widget = main_window.import_tab.file_list_widget
            for i in range(list_widget.count()):
                if list_widget.item(i).text() == imported_files[0]:
                    list_widget.setCurrentRow(i)
                    break
        # Восстановить выбранную колонку времени (если есть)
        settings = data.get('settings', {})
        time_column_saved = settings.get('time_column')
        if time_column_saved:
            combo = main_window.import_tab.time_column_combo
            idx = combo.findText(time_column_saved)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        # Объединить и загрузить (имитируем нажатие кнопки)
        handler._handle_merge_and_load()
        # Восстановить параметры состояния (каналы, сегменты, активный канал и т.д.)
        from data_models.channel_state import ChannelState
        app_state.channel_states.clear()
        for ch, ch_data in data.get('channels', {}).items():
            app_state.channel_states[ch] = ChannelState.from_dict(ch_data)
        settings = data.get('settings', {})
        app_state.active_channel_name = settings.get('active_channel', '')
        app_state.selected_segment_index = settings.get('selected_segment_index')
        app_state.show_source_data = settings.get('show_source_data', True)
        app_state.show_approximation = settings.get('show_approximation', True)
        app_state.auto_recalculate = settings.get('auto_recalculate', True)
        # Обновить таблицы и график
        if hasattr(main_window, 'analysis_setup_handler'):
            main_window.analysis_setup_handler.update_channels_table()
        if hasattr(main_window, 'segment_table_handler'):
            main_window.segment_table_handler.update_table()
        if hasattr(main_window, 'plot_manager'):
            # Перерисовать график
            time_column = None
            if hasattr(main_window.import_tab, 'time_column_combo'):
                time_column = main_window.import_tab.time_column_combo.currentText()
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
        # Включить вкладку 'Экспорт', если данные успешно загружены
        if hasattr(main_window, 'tabs'):
            main_window.tabs.setTabEnabled(2, True)
        QMessageBox.information(self, 'Загрузка', 'Проект успешно загружен!')