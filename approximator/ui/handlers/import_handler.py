# Путь: ui/handlers/import_handler.py
# =================================================================================
# МОДУЛЬ ОБРАБОТЧИКА СОБЫТИЙ ВКЛАДКИ "ИМПОРТ"
# =================================================================================
import pandas as pd
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QListWidgetItem
from typing import Set

from data_models.channel_state import ChannelState
from data_models.data_structures import Segment

class ImportEventHandler:
    def __init__(self, main_window, app_state, data_loader, data_merger, analysis_setup_handler, analysis_reset_callback):
        print("DEBUG: ImportEventHandler __init__")
        self.main_window = main_window
        self.state = app_state
        self.data_loader = data_loader
        self.data_merger = data_merger
        self.analysis_setup_handler = analysis_setup_handler
        self.analysis_reset_callback = analysis_reset_callback
        self._selected_file_paths = []
        self._connect_events()

    def _connect_events(self):
        print("DEBUG: ImportEventHandler _connect_events")
        import_tab = self.main_window.import_tab
        print(f"DEBUG: ImportEventHandler import_tab.add_files_button id={id(import_tab.add_files_button)}")
        import_tab.add_files_button.clicked.connect(self._handle_add_files)
        import_tab.reset_button.clicked.connect(self._handle_reset_import)
        import_tab.merge_and_load_button.clicked.connect(self._handle_merge_and_load)
        import_tab.remove_selected_button.clicked.connect(self._handle_remove_selected)
        import_tab.file_list_widget.currentItemChanged.connect(self._handle_file_selection_changed)

    def _handle_add_files(self):
        print("DEBUG: Кнопка 'Добавить файлы...' нажата")
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.main_window, "Выберите файлы", "", "Все файлы (*.*)")
        if not file_paths:
            return

        newly_added_paths = []
        for path in file_paths:
            if path not in self._selected_file_paths:
                self._selected_file_paths.append(path)
                newly_added_paths.append(path)
                df = self.data_loader.load_file(path)
                if not df.empty:
                    self.state.loaded_dataframes[path] = df

        if newly_added_paths:
            self._update_file_list_widget()
            self._update_time_column_combo()
            
            list_widget = self.main_window.import_tab.file_list_widget
            for i in range(list_widget.count()):
                if list_widget.item(i).text() == newly_added_paths[0]:
                    list_widget.setCurrentRow(i)
                    break

    def _handle_file_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current is None:
            self._reset_preview_table()
            return
        
        file_path = current.text()
        if file_path in self.state.loaded_dataframes:
            df_to_preview = self.state.loaded_dataframes[file_path]
            self._update_preview_table(df_to_preview)
        else:
            self._reset_preview_table()

    def _handle_remove_selected(self):
        current_item = self.main_window.import_tab.file_list_widget.currentItem()
        if not current_item: return
        file_path = current_item.text()
        
        if file_path in self._selected_file_paths: self._selected_file_paths.remove(file_path)
        if file_path in self.state.loaded_dataframes: del self.state.loaded_dataframes[file_path]
        
        self._update_file_list_widget()
        self._update_time_column_combo()
        self._reset_preview_table()

    def _handle_merge_and_load(self):
        time_column = self.main_window.import_tab.time_column_combo.currentText()
        if not time_column: return
        all_dfs = list(self.state.loaded_dataframes.values())
        if not all_dfs: return
        merged_df = self.data_merger.merge_dataframes(all_dfs, on_column=time_column)
        if merged_df.empty: return
        self.state.merged_dataframe = merged_df
        time_min, time_max = merged_df[time_column].min(), merged_df[time_column].max()
        channel_names = [col for col in merged_df.columns if col != time_column]
        self.state.channel_list = channel_names
        self.state.channel_states.clear()
        for name in channel_names:
            initial_segment = Segment(x_start=time_min, x_end=time_max)
            self.state.channel_states[name] = ChannelState(name=name, segments=[initial_segment])
        self.analysis_setup_handler.update_channels_table()
        self.main_window.tabs.setTabEnabled(1, True)
        self.main_window.tabs.setTabEnabled(2, True)  # Включаем Экспорт
        self.main_window.tabs.setCurrentIndex(1)
        self.analysis_setup_handler._handle_active_channel_change(0, 0, -1, -1)

    def _handle_reset_import(self):
        self._selected_file_paths.clear()
        self.state.loaded_dataframes.clear()
        self.state.merged_dataframe = pd.DataFrame()
        self.state.channel_list.clear()
        self.state.channel_states.clear()
        self._update_file_list_widget()
        self.main_window.import_tab.time_column_combo.clear()
        self._reset_preview_table()
        self.main_window.tabs.setTabEnabled(1, False)
        self.main_window.tabs.setTabEnabled(2, False)  # Отключаем Экспорт
        self.analysis_reset_callback()
        
    def _reset_preview_table(self):
        table = self.main_window.import_tab.preview_table
        table.clearContents(); table.setRowCount(0)

    def _update_file_list_widget(self):
        list_widget = self.main_window.import_tab.file_list_widget
        list_widget.currentItemChanged.disconnect(self._handle_file_selection_changed)
        list_widget.clear()
        list_widget.addItems(self._selected_file_paths)
        list_widget.currentItemChanged.connect(self._handle_file_selection_changed)

    def _update_time_column_combo(self):
        all_columns: Set[str] = set()
        for df in self.state.loaded_dataframes.values(): all_columns.update(df.columns)
        combo = self.main_window.import_tab.time_column_combo
        current_selection = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(sorted(list(all_columns)))
        if current_selection in all_columns: combo.setCurrentText(current_selection)
        combo.blockSignals(False)

    def _update_preview_table(self, df: pd.DataFrame):
        table = self.main_window.import_tab.preview_table
        table.clearContents(); table.setRowCount(0)
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns.astype(str))
        table.setRowCount(len(df.index))
        df_str = df.astype(str)
        for i, row in enumerate(df_str.itertuples(index=False)):
            for j, value in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(value))
        table.resizeColumnsToContents()