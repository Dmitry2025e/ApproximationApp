from matplotlib.lines import Line2D

class DraggableSegmentBoundary:
    """
    Представляет одну из границ сегмента (x_start или x_end) как интерактивную линию.
    Поддерживает перетаскивание мышью и обновляет связанный Segment.

    Parameters:
        ax: matplotlib.axes.Axes — ось, на которой рисуется граница
        segment: объект Segment, из модели данных
        side: 'start' или 'end' — какую именно границу представляет
        on_move_callback: функция для вызова после перемещения (например, plot_widget.draw)
    """

    def __init__(self, ax, segment, side: str, on_move_callback, on_click_callback):
        self.ax = ax
        self.segment = segment
        self.side = side
        self.on_move_callback = on_move_callback
        self.on_click_callback = on_click_callback

        self.pressed = False
        self.line = self._create_line()
        self.ax.add_line(self.line) # добавляем линию на график

    def _get_base_style(self):
        """Возвращает базовые графические параметры линии."""
        return {
            'color': self.segment.color,
            'linewidth': self.segment.thickness,
            'linestyle': self.segment.line_style,
            'alpha': 0.6
        }

    def _get_line_style(self):
        """Возвращает базовые графические параметры для линии границы."""
        return {
            'color': self.segment.color,
            'linestyle': self.segment.line_style,
            'linewidth': self.segment.thickness,
            'alpha': 0.6,
            'picker': True
        }

    def _create_line(self):
        """Создаёт линию для отрисовки."""
        style = self._get_line_style()
        y_min, y_max = self.ax.get_ylim()
        x = self.x_position
        return Line2D([x, x], [y_min, y_max], **style)

    @property
    def x_position(self) -> float:
        """Текущее положение границы по оси X."""
        return self.segment.x_start if self.side == 'start' else self.segment.x_end

    def contains(self, event) -> bool:
        """Проверяет, попал ли курсор мыши близко к границе."""
        if event.inaxes != self.ax or not event.xdata:
            return False

        # Автоматическая адаптация под zoom
        x_min, x_max = self.ax.get_xlim()
        zoom_span = x_max - x_min
        sensitivity = zoom_span * 0.005  # 0.5% от видимого диапазона

        return abs(event.xdata - self.x_position) < sensitivity




    def on_press(self, event):
        if self.contains(event):
            self.pressed = True
            print(f"[boundary] pressed: {self.side} of segment ({self.segment.x_start:.2f}, {self.segment.x_end:.2f}) at x={event.xdata:.2f}")
            if callable(self.on_click_callback):
                self.on_click_callback(self.segment)

    def on_release(self, event):
        self.pressed = False

    def on_motion(self, event):
        if self.pressed and event.xdata:
            print(f"[boundary] dragging {self.side} to x={event.xdata:.2f}")

            # Обновляем координаты сегмента
            if self.side == 'start':
                self.segment.x_start = min(event.xdata, self.segment.x_end - 0.01)
            else:
                self.segment.x_end = max(event.xdata, self.segment.x_start + 0.01)

            # Обновляем графическую линию
            self.line.set_xdata([self.x_position, self.x_position])

            # Вызов обратного вызова
            if callable(self.on_move_callback):
                self.on_move_callback()