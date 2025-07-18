# Путь: services/project_state_controller.py

import json
import os
from typing import Optional

import pandas as pd
from approximator.data_models.channel_state import ChannelState
from approximator.services.data_loader import DataLoader
from approximator.services.data_merger import DataMerger

from approximator.file_parsers.generic_csv_parser import GenericCsvParser
from approximator.file_parsers.excel_parser import ExcelParser
from approximator.file_parsers.adc_parser import AdcParser


class ProjectStateController:
    """
    Управляет загрузкой и сохранением состояния проекта.
    """
    def __init__(self, main_window):
        self.main_window = main_window
        self.state = main_window.state

        # ✅ Встроенные парсеры и сервисы
        self.data_loader = DataLoader([
            AdcParser(),
            ExcelParser(),
            GenericCsvParser()
        ])
        self.data_merger = DataMerger()

    def load_project(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._apply_state(data)

    def save_project(self, file_path: str):
        state_dict = self._extract_state()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)

    def load_project_from_dict(self, data: dict):
        """
        Загружает состояние проекта из словаря (например, из autosave.json).
        """
        print("[ProjectStateController] 🔁 Восстановление из словаря")

        imported_files = data.get('imported_files', [])
        settings = data.get('settings', {})
        channels = data.get('channels', {})

        self.state.loaded_dataframes.clear()
        for path in imported_files:
            if os.path.exists(path):
                try:
                    df = self.data_loader.load_file(path)
                    if not df.empty:
                        self.state.loaded_dataframes[path] = df
                        print(f"[ProjectStateController] ✅ Загружен: {path}, shape={df.shape}")
                except Exception as e:
                    print(f"[ProjectStateController] ❌ Ошибка загрузки {path}: {e}")
            else:
                print(f"[ProjectStateController] ❌ Файл не найден: {path}")

        self.state.time_column = settings.get('time_column')
        self.state.selected_columns = {path: self.state.time_column for path in imported_files}

        all_dfs = list(self.state.loaded_dataframes.values())
        print(f"[ProjectStateController] 🔁 Объединение по колонке: {self.state.time_column}")
        if self.state.time_column and all_dfs:
            merged_df = self.data_merger.merge_dataframes(all_dfs, on_column=self.state.time_column)
            self.state.merged_dataframe = merged_df
            self.state.channel_list = [col for col in merged_df.columns if col != self.state.time_column]
            print(f"[ProjectStateController] ✅ Объединено: {merged_df.shape}")
        else:
            self.state.merged_dataframe = pd.DataFrame()
            self.state.channel_list = []
            print(f"[ProjectStateController] ⚠️ Объединение не выполнено")

        self.state.channel_states.clear()
        for ch_name, ch_data in channels.items():
            self.state.channel_states[ch_name] = ChannelState.from_dict(ch_data)

        self.state.active_channel_name = settings.get('active_channel', '')
        self.state.selected_segment_index = settings.get('selected_segment_index')
        self.state.show_source_data = settings.get('show_source_data', True)
        self.state.show_approximation = settings.get('show_approximation', True)
        self.state.auto_recalculate = settings.get('auto_recalculate', True)

        # GUI: обновление компонентов
        import_tab = self.main_window.import_tab
        import_tab.file_panel.set_files(imported_files)

        columns = self._collect_all_columns()
        import_tab.time_selector.set_columns(columns)

        if self.state.time_column and self.state.time_column in columns:
            import_tab.time_selector.set_selected(self.state.time_column)
            print(f"[ProjectStateController] ✅ Установлена колонка времени: {self.state.time_column}")
        else:
            print(
                f"[ProjectStateController] ⚠️ time_column '{self.state.time_column}' не найдена среди колонок: {columns}")
            self.state.time_column = None

        if hasattr(self.main_window, 'analysis_setup_handler'):
            self.main_window.analysis_setup_handler.update_channels_table()
        if hasattr(self.main_window, 'segment_table_handler'):
            self.main_window.segment_table_handler.update_table()

        self.main_window.tabs.setTabEnabled(1, True)
        self.main_window.tabs.setTabEnabled(2, True)
        self.main_window.tabs.setCurrentIndex(1)

        if self.state.merged_dataframe is not None and not self.state.merged_dataframe.empty and self.state.time_column:
            self._redraw_plot()
        else:
            print("[ProjectStateController] ⚠️ Пропуск redraw — нет объединённых данных или time_column")

    def _apply_state_o(self, data: dict):
        imported_files = data.get('imported_files', [])
        settings = data.get('settings', {})
        channels = data.get('channels', {})

        self.state.loaded_dataframes.clear()
        for path in imported_files:
            if os.path.exists(path):
                try:
                    df = self.data_loader.load_file(path)
                    if not df.empty:
                        self.state.loaded_dataframes[path] = df
                except Exception as e:
                    print(f"[ProjectStateController] Ошибка загрузки файла {path}: {e}")

        self.state.time_column = settings.get('time_column')
        self.state.selected_columns = {path: self.state.time_column for path in imported_files}

        all_dfs = list(self.state.loaded_dataframes.values())
        if self.state.time_column and all_dfs:
            merged_df = self.data_merger.merge_dataframes(all_dfs, on_column=self.state.time_column)
            self.state.merged_dataframe = merged_df
            self.state.channel_list = [col for col in merged_df.columns if col != self.state.time_column]
        else:
            self.state.merged_dataframe = pd.DataFrame()
            self.state.channel_list = []

        self.state.channel_states.clear()
        for ch_name, ch_data in channels.items():
            self.state.channel_states[ch_name] = ChannelState.from_dict(ch_data)

        self.state.active_channel_name = settings.get('active_channel', '')
        self.state.selected_segment_index = settings.get('selected_segment_index')
        self.state.show_source_data = settings.get('show_source_data', True)
        self.state.show_approximation = settings.get('show_approximation', True)
        self.state.auto_recalculate = settings.get('auto_recalculate', True)

        # GUI: обновление компонентов
        import_tab = self.main_window.import_tab
        import_tab.file_panel.set_files(imported_files)
        import_tab.time_selector.set_columns(self._collect_all_columns())
        if self.state.time_column:
            import_tab.time_selector.set_selected(self.state.time_column)

        if hasattr(self.main_window, 'analysis_setup_handler'):
            self.main_window.analysis_setup_handler.update_channels_table()
        if hasattr(self.main_window, 'segment_table_handler'):
            self.main_window.segment_table_handler.update_table()

        self.main_window.tabs.setTabEnabled(1, True)
        self.main_window.tabs.setTabEnabled(2, True)
        self.main_window.tabs.setCurrentIndex(1)

        self._redraw_plot()

    def _apply_state(self, data: dict):
        imported_files = data.get('imported_files', [])
        settings = data.get('settings', {})
        channels = data.get('channels', {})

        print(f"[ProjectStateController] 🔁 Загружаем файлы: {imported_files}")
        self.state.loaded_dataframes.clear()

        for path in imported_files:
            if os.path.exists(path):
                try:
                    df = self.data_loader.load_file(path)
                    if not df.empty:
                        self.state.loaded_dataframes[path] = df
                        print(f"[ProjectStateController] ✅ Загружен: {path}, shape={df.shape}")
                    else:
                        print(f"[ProjectStateController] ⚠️ Пустой файл: {path}")
                except Exception as e:
                    print(f"[ProjectStateController] ❌ Ошибка загрузки {path}: {e}")
            else:
                print(f"[ProjectStateController] ❌ Файл не найден: {path}")

        self.state.time_column = settings.get('time_column')
        self.state.selected_columns = {path: self.state.time_column for path in imported_files}

        all_dfs = list(self.state.loaded_dataframes.values())
        print(f"[ProjectStateController] 🔁 Объединение по колонке: {self.state.time_column}")
        if self.state.time_column and all_dfs:
            merged_df = self.data_merger.merge_dataframes(all_dfs, on_column=self.state.time_column)
            self.state.merged_dataframe = merged_df
            self.state.channel_list = [col for col in merged_df.columns if col != self.state.time_column]
            print(f"[ProjectStateController] ✅ Объединено: {merged_df.shape}")
        else:
            self.state.merged_dataframe = pd.DataFrame()
            self.state.channel_list = []
            print(f"[ProjectStateController] ⚠️ Объединение не выполнено")

        print(f"[ProjectStateController] 🔁 Восстановление каналов: {list(channels.keys())}")
        self.state.channel_states.clear()
        for ch_name, ch_data in channels.items():
            self.state.channel_states[ch_name] = ChannelState.from_dict(ch_data)

        self.state.active_channel_name = settings.get('active_channel', '')
        self.state.selected_segment_index = settings.get('selected_segment_index')
        self.state.show_source_data = settings.get('show_source_data', True)
        self.state.show_approximation = settings.get('show_approximation', True)
        self.state.auto_recalculate = settings.get('auto_recalculate', True)

        # GUI: обновление компонентов
        import_tab = self.main_window.import_tab
        import_tab.file_panel.set_files(imported_files)
        import_tab.time_selector.set_columns(self._collect_all_columns())
        if self.state.time_column:
            import_tab.time_selector.set_selected(self.state.time_column)

        print(
            f"[ProjectStateController] 🔁 Обновление GUI: файлов={len(imported_files)}, колонок={self._collect_all_columns()}")
        print(f"[ProjectStateController] 🔁 Выбранная колонка: {self.state.time_column}")

        if hasattr(self.main_window, 'analysis_setup_handler'):
            self.main_window.analysis_setup_handler.update_channels_table()
        if hasattr(self.main_window, 'segment_table_handler'):
            self.main_window.segment_table_handler.update_table()

        self.main_window.tabs.setTabEnabled(1, True)
        self.main_window.tabs.setTabEnabled(2, True)
        self.main_window.tabs.setCurrentIndex(1)

        self._redraw_plot()

    def _extract_state(self) -> dict:
        return {
            'imported_files': list(self.state.loaded_dataframes.keys()),
            'settings': {
                'time_column': self.state.time_column,
                'active_channel': self.state.active_channel_name,
                'selected_segment_index': self.state.selected_segment_index,
                'show_source_data': self.state.show_source_data,
                'show_approximation': self.state.show_approximation,
                'auto_recalculate': self.state.auto_recalculate
            },
            'channels': {
                name: ch.to_dict()
                for name, ch in self.state.channel_states.items()
            }
        }

    def _collect_all_columns(self) -> list[str]:
        all_columns = set()
        for df in self.state.loaded_dataframes.values():
            all_columns.update(df.columns)
        return sorted(list(all_columns))

    def _redraw_plot(self):
        df = self.state.merged_dataframe
        time_column = self.state.time_column
        if df is None or df.empty or not time_column:
            print("[ProjectStateController] ❌ Невозможно построить график — нет данных или time_column")
            return

        self.main_window.plot_manager.redraw_all_channels(
            df=df,
            x_col=time_column,
            channel_states=self.state.channel_states,
            active_channel_name=self.state.active_channel_name,
            selected_segment_index=self.state.selected_segment_index,
            preserve_zoom=False,
            show_source=self.state.show_source_data,
            show_approximation=self.state.show_approximation
        )

    def _load_and_register_file(self, path: str) -> pd.DataFrame:
        """
        Загружает файл, устраняет конфликты по именам колонок,
        сохраняет структуру и датафрейм в AppState.
        """
        df = self.data_loader.load_file(path)
        if df.empty:
            print(f"[ProjectStateController] ⚠️ Пустой файл: {path}")
            return df

        # Собираем уже использованные имена колонок
        existing = set()
        for other_df in self.state.loaded_dataframes.values():
            existing.update(other_df.columns)

        # Переименование конфликтующих колонок
        rename_map = {}
        new_columns = []
        for col in df.columns:
            new_col = col
            i = 1
            while new_col in existing:
                new_col = f"{col}_{i}"
                i += 1
            rename_map[col] = new_col
            new_columns.append(new_col)

        if rename_map:
            df = df.rename(columns=rename_map)
            print(f"[ProjectStateController] 🔁 Переименование колонок: {rename_map}")

        # Сохраняем структуру
        self.state.file_columns[path] = new_columns
        self.state.loaded_dataframes[path] = df

        print(f"[ProjectStateController] ✅ Загружен с уникальными колонками: {path}, shape={df.shape}")
        return df