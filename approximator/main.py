# Путь: approximator/main.py

import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtWidgets import QApplication
from app.main_window import MainWindow

def clear_console():
    """
    Очищает консоль. Работает на Windows, MacOS и Linux.
    """
    # Для Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # Для MacOS и Linux
    else:
        _ = os.system('clear')


import json
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QEvent

AUTOSAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autosave.json")

def main():
    """
    Главная функция для запуска приложения.
    """
    clear_console()
    print("Консоль очищена. Запуск приложения...")

    app = QApplication(sys.argv)
    window = MainWindow()


    # --- Автоматическое сохранение состояния при выходе ---
    def autosave():
        try:
            if hasattr(window, 'analysis_tab') and hasattr(window.analysis_tab, '_save_project'):
                # Переопределяем диалог выбора файла, чтобы сохранять в autosave.json
                orig_getSaveFileName = __import__('PyQt5.QtWidgets').QtWidgets.QFileDialog.getSaveFileName
                __import__('PyQt5.QtWidgets').QtWidgets.QFileDialog.getSaveFileName = lambda *a, **kw: (AUTOSAVE_PATH, '')
                window.analysis_tab._save_project()
                __import__('PyQt5.QtWidgets').QtWidgets.QFileDialog.getSaveFileName = orig_getSaveFileName
        except Exception as e:
            print(f"Ошибка автосохранения: {e}")

    app.aboutToQuit.connect(autosave)
    window.show()

    # --- Автоматическая загрузка состояния при запуске ---
    if os.path.exists(AUTOSAVE_PATH):
        try:
            with open(AUTOSAVE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Используем тот же механизм, что и при ручной загрузке проекта
            if hasattr(window, 'import_tab') and hasattr(window.import_tab, '_handle_load_project'):
                # эмулируем загрузку через import_tab
                window.import_tab._handle_load_project_from_data(data)
                # Явно обновляем интерфейс после загрузки состояния
                if hasattr(window, 'analysis_setup_handler'):
                    window.analysis_setup_handler.update_channels_table()
                if hasattr(window, 'segment_table_handler'):
                    window.segment_table_handler.update_table()
                if hasattr(window, 'plot_manager'):
                    # Обновим график, если возможно
                    app_state = getattr(window, 'state', None)
                    time_column = None
                    if hasattr(window.import_tab, 'time_column_combo'):
                        time_column = window.import_tab.time_column_combo.currentText()
                    if app_state and hasattr(app_state, 'merged_dataframe') and app_state.merged_dataframe is not None:
                        if not time_column and not app_state.merged_dataframe.empty:
                            all_columns = app_state.merged_dataframe.columns
                            if 'Time' in all_columns:
                                time_column = 'Time'
                            else:
                                time_column = all_columns[0] if len(all_columns) > 0 else None
                        if time_column:
                            window.plot_manager.redraw_all_channels(
                                df=app_state.merged_dataframe,
                                x_col=time_column,
                                channel_states=app_state.channel_states,
                                active_channel_name=app_state.active_channel_name,
                                selected_segment_index=app_state.selected_segment_index,
                                preserve_zoom=False,
                                show_source=app_state.show_source_data,
                                show_approximation=app_state.show_approximation
                            )
                # Обновим элементы AnalysisTab, если есть
                if hasattr(window, 'analysis_tab'):
                    if hasattr(window.analysis_tab, 'update_controls'):
                        window.analysis_tab.update_controls()
                    if hasattr(window.analysis_tab, 'update_tables'):
                        window.analysis_tab.update_tables()
        except Exception as e:
            QMessageBox.warning(window, 'Автозагрузка', f'Ошибка автозагрузки состояния: {e}')

    sys.exit(app.exec_())

if __name__ == '__main__':
    # Добавим метод для загрузки состояния из dict в ImportTab
    from PyQt5.QtWidgets import QWidget
    def _handle_load_project_from_data(self, data):
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'import_event_handler'):
            main_window = main_window.parent()
        if not main_window or not hasattr(main_window, 'import_event_handler'):
            return
        handler = main_window.import_event_handler
        app_state = main_window.state
        imported_files = data.get('imported_files', [])
        handler._handle_reset_import()
        handler._selected_file_paths = list(imported_files)
        handler._update_file_list_widget()
        handler._update_time_column_combo()
        loaded_dfs = {}
        for fpath in imported_files:
            try:
                df = handler.data_loader.load_file(fpath)
                if not df.empty:
                    loaded_dfs[fpath] = df
                    print(f"Успешно загружен файл {fpath}")
            except Exception as e:
                print(f"Ошибка автозагрузки файла {fpath}: {e}")
        
        # Установим загруженные датафреймы
        app_state.loaded_dataframes = loaded_dfs
        
        # Выберем все файлы и инициируем слияние
        list_widget = main_window.import_tab.file_list_widget
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(True)
        
        # Загрузим сохраненные состояния каналов до обновления UI
        from data_models.channel_state import ChannelState
        saved_channels = {}
        try:
            for ch, ch_data in data.get('channels', {}).items():
                channel_state = ChannelState.from_dict(ch_data)
                if channel_state and channel_state.name != "unknown":
                    saved_channels[ch] = channel_state
        except Exception as e:
            print(f"Ошибка загрузки состояний каналов: {e}")
            
        # Обновим список файлов в UI
        list_widget = main_window.import_tab.file_list_widget
        list_widget.clear()
        for fpath in imported_files:
            list_widget.addItem(fpath)
        
        # Обновим комбобокс с колонками времени
        handler._update_time_column_combo()
        
        # Загрузим настройки
        settings = data.get('settings', {})
        time_column_saved = settings.get('time_column')
        if time_column_saved:
            combo = main_window.import_tab.time_column_combo
            idx = combo.findText(time_column_saved)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            
        # Восстановим настройки до слияния
        settings = data.get('settings', {})
        time_column_saved = settings.get('time_column')
        if time_column_saved:
            combo = main_window.import_tab.time_column_combo
            idx = combo.findText(time_column_saved)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        
        # Выполним слияние и загрузку
        handler._handle_merge_and_load()
        
        # После слияния восстановим состояния каналов
        app_state.channel_states.clear()
        app_state.channel_states.update(saved_channels)
        
        # Принудительно обновим UI
        if hasattr(main_window, 'plot_manager'):
            time_column = main_window.import_tab.time_column_combo.currentText()
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
    QWidget._handle_load_project_from_data = _handle_load_project_from_data
    main()