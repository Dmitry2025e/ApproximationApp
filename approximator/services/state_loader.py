from approximator.data_models.channel_state import ChannelState
from approximator.utils.log import debug, error
from approximator.data_models.channel_state import ChannelState

def load_project_state(main_window, data):
    try:
        debug("[state_loader] Starting state restore")
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
                    debug(f"Успешно загружен файл {fpath}")
            except Exception as e:
                debug(f"Ошибка автозагрузки файла {fpath}: {e}")

        # Установим загруженные датафреймы
        app_state.loaded_dataframes = loaded_dfs

        # Выберем все файлы и инициируем слияние
        list_widget = main_window.import_tab.file_list_widget
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(True)

        # Загрузим сохраненные состояния каналов до обновления UI

        saved_channels = {}
        try:
            for ch, ch_data in data.get('channels', {}).items():
                channel_state = ChannelState.from_dict(ch_data)
                if channel_state and channel_state.name != "unknown":
                    saved_channels[ch] = channel_state
        except Exception as e:
            debug(f"Ошибка загрузки состояний каналов: {e}")

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

    except Exception as e:
        error(f"[state_loader] Failed to load state: {e}")