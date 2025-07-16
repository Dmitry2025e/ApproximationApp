from .boundaries.draggable_boundary import DraggableSegmentBoundary


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
        """
        Отрисовывает границы сегмента с использованием его параметров.

        Args:
            segment: экземпляр Segment
            is_selected: выделен ли сегмент (например, выбран в интерфейсе)
        """
        if not segment:
            return

        # Цвет и стиль линии — с учётом выделения
        color = 'red' if is_selected else segment.color
        linestyle = segment.line_style
        linewidth = segment.thickness

        self.ax.axvline(x=segment.x_start, color=color, linestyle=linestyle,
                        linewidth=linewidth, alpha=0.5)
        self.ax.axvline(x=segment.x_end, color=color, linestyle=linestyle,
                        linewidth=linewidth, alpha=0.5)


    def redraw_all_channels(self, df, x_col, channel_states, active_channel_name=None,
                            selected_segment_index=None, preserve_zoom=False,
                            show_source=True, show_approximation=True):
        """
        Перерисовывает все каналы на графике.

        Args:
            df: pandas.DataFrame с данными
            x_col: имя колонки времени
            channel_states: dict[str, ChannelState] — состояния каналов
            active_channel_name: какой канал считать активным
            selected_segment_index: индекс выбранного сегмента
            preserve_zoom: сохранять ли текущее положение осей
            show_source: отображать ли исходные точки
            show_approximation: отображать ли аппроксимацию
        """
        if preserve_zoom:
            self._save_view_state()

        self._clear_plot()

        # Отрисовка всех каналов
        for channel_name, channel_state in channel_states.items():
            if not channel_state.is_visible:
                continue

            # Исходные данные
            if show_source and channel_name in df.columns:
                color = 'red' if channel_name == active_channel_name else channel_state.base_color
                alpha = 1.0 if channel_name == active_channel_name else 0.3
                self.ax.scatter(df[x_col], df[channel_name], color=color, alpha=alpha, s=1)

            # Аппроксимация
            approx_col = f"{channel_name}_approx"
            if show_approximation and approx_col in df.columns:
                self.ax.plot(
                    df[x_col],
                    df[approx_col],
                    color=channel_state.base_color,
                    linestyle=channel_state.line_style,
                    linewidth=channel_state.thickness,
                    alpha=0.7
                )

        # Отрисовка сегментов активного канала
        if active_channel_name and active_channel_name in channel_states:
            segments = channel_states[active_channel_name].segments or []
            for i, segment in enumerate(segments):
                self._draw_segment_boundaries(segment, i == selected_segment_index)

        if preserve_zoom:
            self._restore_view_state()

        self.plot_widget.draw()

    def get_axes(self):
        """Возвращает текущие оси графика."""
        return self.ax