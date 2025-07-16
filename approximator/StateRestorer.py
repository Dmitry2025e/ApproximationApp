"""
Восстановление состояния приложения из JSON (например, autosave.json).

Назначение:
- Восстановить интерфейс, данные, график и настройки
- Разгрузить main.py и MainWindow от прямой логики автозагрузки
- Повысить устойчивость приложения при повреждении сохранённых данных
"""

class StateRestorer:
    def __init__(self, window):
        """
        Связывает восстановитель с экземпляром главного окна и его состоянием.
        """
        self.window = window
        self.state = getattr(window, 'state', None)

    def restore(self, data: dict):
        """
        Запускает восстановление всех компонент приложения из словаря состояния.
        """
        self._restore_import_tab(data)
        self._restore_analysis_setup(data)
        self._restore_segment_table(data)
        self._restore_plot(data)
        self._restore_analysis_tab(data)

    def _restore_import_tab(self, data):
        """
        Восстановление состояния вкладки импорта (колонка времени).
        """
        import_tab = getattr(self.window, 'import_tab', None)
        if not import_tab or not hasattr(import_tab, 'time_column_combo'):
            return

        time_column = data.get("selected_time_column")
        if time_column:
            index = import_tab.time_column_combo.findText(time_column)
            if index >= 0:
                import_tab.time_column_combo.setCurrentIndex(index)

    def _restore_analysis_setup(self, data):
        """
        Восстановление таблицы каналов: имя, цвет, стиль, статус.
        """
        handler = getattr(self.window, 'analysis_setup_handler', None)
        if handler and hasattr(handler, 'update_channels_table'):
            handler.update_channels_table()

    def _restore_segment_table(self, data):
        """
        Восстановление таблицы сегментов: интервалы, параметры, активность.
        """
        handler = getattr(self.window, 'segment_table_handler', None)
        if handler and hasattr(handler, 'update_table'):
            handler.update_table()

    def _restore_plot(self, data):
        """
        Перерисовка графика каналов на основе сохранённых параметров.
        """
        plot_manager = getattr(self.window, 'plot_manager', None)
        import_tab = getattr(self.window, 'import_tab', None)

        if not self.state or not hasattr(self.state, 'merged_dataframe'):
            return
        df = self.state.merged_dataframe
        if df is None or df.empty:
            return

        time_column = None
        if import_tab and hasattr(import_tab, 'time_column_combo'):
            time_column = import_tab.time_column_combo.currentText()

        if not time_column:
            columns = df.columns
            time_column = "Time" if "Time" in columns else (columns[0] if columns else None)

        if not time_column or not plot_manager or not hasattr(plot_manager, 'redraw_all_channels'):
            return

        plot_manager.redraw_all_channels(
            df=df,
            x_col=time_column,
            channel_states=self.state.channel_states,
            active_channel_name=self.state.active_channel_name,
            selected_segment_index=self.state.selected_segment_index,
            preserve_zoom=False,
            show_source=self.state.show_source_data,
            show_approximation=self.state.show_approximation
        )

    def _restore_analysis_tab(self, data):
        """
        Восстановление элементов интерфейса вкладки анализа (кнопки, таблицы).
        """
        tab = getattr(self.window, 'analysis_tab', None)
        if tab:
            if hasattr(tab, 'update_controls'):
                tab.update_controls()
            if hasattr(tab, 'update_tables'):
                tab.update_tables()