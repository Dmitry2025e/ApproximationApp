class PlotManager:
    def __init__(self, plot_widget):
        """
        Инициализирует менеджер отрисовки.
        
        Args:
            plot_widget: Виджет для отрисовки графиков (FigureCanvasQTAgg)
        """
        self.plot_widget = plot_widget
        self.ax = plot_widget.figure.gca()  # FigureCanvasQTAgg уже является canvas'ом
        self._clear_plot()
        self._current_ylim = None
        self._current_xlim = None
        
    @property
    def canvas(self):
        """Возвращает холст для отрисовки."""
        return self.plot_widget
        
    def _clear_plot(self):
        """Очищает график."""
        self.ax.clear()
        self.plot_widget.draw()
        
    def _save_view_state(self):
        """Сохраняет текущие границы осей."""
        self._current_xlim = self.ax.get_xlim()
        self._current_ylim = self.ax.get_ylim()
        
    def _restore_view_state(self):
        """Восстанавливает сохраненные границы осей."""
        if self._current_xlim is not None and self._current_ylim is not None:
            self.ax.set_xlim(self._current_xlim)
            self.ax.set_ylim(self._current_ylim)
            
    def _draw_segment_boundaries(self, segment, is_selected=False):
        """Отрисовывает границы сегмента с учетом его типа."""
        color = 'red' if is_selected else 'blue'
        self.ax.axvline(x=segment.start, color=color, linestyle='--', alpha=0.5)
        self.ax.axvline(x=segment.end, color=color, linestyle='--', alpha=0.5)

    def redraw_all_channels(self, df, x_col, channel_states, active_channel_name=None, 
                          selected_segment_index=None, preserve_zoom=False, 
                          show_source=True, show_approximation=True):
        """
        Перерисовывает все каналы на графике.
        
        Args:
            df: DataFrame с данными
            x_col: имя столбца с данными по оси X
            channel_states: состояния каналов
            active_channel_name: имя активного канала
            selected_segment_index: индекс выбранного сегмента
            preserve_zoom: сохранять ли текущий масштаб
            show_source: показывать ли исходные данные
            show_approximation: показывать ли аппроксимацию
        """
        if preserve_zoom:
            self._save_view_state()
            
        self._clear_plot()
        
        # Отрисовка каждого канала
        for channel_name, channel_state in channel_states.items():
            if not channel_state['visible']:
                continue
                
            # Исходные данные
            if show_source and channel_name in df.columns:
                color = 'red' if channel_name == active_channel_name else 'blue'
                alpha = 1.0 if channel_name == active_channel_name else 0.5
                self.ax.scatter(df[x_col], df[channel_name], 
                              color=color, alpha=alpha, s=1)
                
            # Аппроксимация
            if show_approximation and f"{channel_name}_approx" in df.columns:
                self.ax.plot(df[x_col], df[f"{channel_name}_approx"],
                           color='green', alpha=0.7)
                
        # Отрисовка сегментов
        if active_channel_name and active_channel_name in channel_states:
            segments = channel_states[active_channel_name].get('segments', [])
            for i, segment in enumerate(segments):
                self._draw_segment_boundaries(segment, i == selected_segment_index)
                
        if preserve_zoom:
            self._restore_view_state()
            
        self.plot_widget.draw()
        
    def get_axes(self):
        """Возвращает текущие оси графика."""
        return self.ax