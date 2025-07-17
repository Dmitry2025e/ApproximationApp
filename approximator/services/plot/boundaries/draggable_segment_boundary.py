from matplotlib.lines import Line2D
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent

from approximator.utils.plot.removable_artist import RemovableArtist
from approximator.services.segments import SegmentEditor
from approximator.data_models.channel_state import ChannelState


class DraggableSegmentBoundary:
    def __init__(
        self,
        ax: Axes,
        segment_index: int,
        side: str,  # 'start' или 'end'
        channel: ChannelState,
        editor: SegmentEditor,
        on_move_callback=None,
        on_press_callback=None,
        on_release_callback=None,
    ):
        self.ax = ax
        self.segment_index = segment_index
        self.side = side
        self.channel = channel
        self.editor = editor

        self.on_move_callback = on_move_callback
        self.on_press_callback = on_press_callback
        self.on_release_callback = on_release_callback

        self.pressed = False

        # 📐 Вычисляем координату линии
        segment = self.channel.segments[self.segment_index]
        x = segment.x_start if self.side == 'start' else segment.x_end

        # 🧱 Создаём линию
        self._line: Line2D = ax.axvline(x=x, color='r', linewidth=2, picker=True)

        # 🧹 Подключаем универсальный удалитель
        self._remover = RemovableArtist(self._line, ax)

    def contains(self, event: MouseEvent) -> bool:
        if event.inaxes != self.ax or event.xdata is None:
            return False

        x_min, x_max = self.ax.get_xlim()
        sensitivity = (x_max - x_min) * 0.005
        x_line = self._line.get_xdata()[0]

        return abs(event.xdata - x_line) < sensitivity

    def on_press(self, event: MouseEvent):
        if not self.contains(event):
            return

        self.pressed = True
        self._line.set_color('orange')
        self._line.set_linewidth(3)

        if callable(self.on_press_callback):
            self.on_press_callback()

    def on_motion(self, event: MouseEvent):
        if not (self.pressed and event.xdata):
            return

        moved = self.editor.move_boundary(
            index=self.segment_index,
            side=self.side,
            new_x=event.xdata
        )

        if moved:
            self._line.set_xdata([event.xdata, event.xdata])
            if callable(self.on_move_callback):
                self.on_move_callback()

    def on_release(self, event: MouseEvent):
        if not self.pressed:
            return

        self.pressed = False
        self._line.set_color('r')
        self._line.set_linewidth(2)

        if callable(self.on_release_callback):
            self.on_release_callback()

    def remove(self):
        self._remover.remove()