from matplotlib.backend_bases import MouseEvent
from approximator.services.segments import SegmentEditor
from approximator.services.plot.boundaries.draggable_segment_boundary import DraggableSegmentBoundary
from approximator.data_models.app_state import AppState
from approximator.services.plot.plot_manager import PlotManager

from approximator.utils.log import debug
debug("[SegmentMouseHandler] ✅ Инициализирован")

class SegmentMouseHandler:
    def __init__(
        self,
        state: AppState,
        plot_manager: PlotManager,
        redraw_callback,
        update_table_callback,
        request_recalc_callback
    ):
        self.state = state
        self.plot_manager = plot_manager
        self.redraw_callback = redraw_callback
        self.update_table_callback = update_table_callback
        self.request_recalc_callback = request_recalc_callback

        self.boundaries = []

        canvas = self.plot_manager.canvas
        self.cid_press = canvas.mpl_connect("button_press_event", self._on_mouse_press)
        self.cid_release = canvas.mpl_connect("button_release_event", self._on_mouse_release)
        self.cid_motion = canvas.mpl_connect("motion_notify_event", self._on_mouse_move)

    def _get_active_channel(self):
        return self.state.channel_states.get(self.state.active_channel_name)

    def _remove_old_boundaries(self):
        for boundary in self.boundaries:
            boundary.remove()
        self.boundaries.clear()

    def _rebuild_boundaries(self):
        self._remove_old_boundaries()
        channel = self._get_active_channel()
        if not channel:
            return

        editor = SegmentEditor(channel)
        ax = self.plot_manager.get_axes()

        for i, segment in enumerate(channel.segments):
            for side in ('start', 'end'):
                boundary = DraggableSegmentBoundary(
                    ax=ax,
                    segment_index=i,
                    side=side,
                    channel=channel,
                    editor=editor,
                    on_move_callback=self.redraw_callback
                )
                self.boundaries.append(boundary)

    def _on_mouse_press(self, event: MouseEvent):
        for boundary in self.boundaries:
            boundary.on_press(event)

    def _on_mouse_release(self, event: MouseEvent):
        for boundary in self.boundaries:
            boundary.on_release(event)

    def _on_mouse_move(self, event: MouseEvent):
        for boundary in self.boundaries:
            boundary.on_motion(event)

    def _on_mouse_right_click(self, event: MouseEvent):
        if event.button != 3 or event.xdata is None:
            return
        channel = self._get_active_channel()
        if not channel:
            return

        editor = SegmentEditor(channel)
        if editor.split_segment_at(event.xdata):
            self.redraw_callback(preserve_zoom=True)
            self.update_table_callback()
            self.request_recalc_callback()