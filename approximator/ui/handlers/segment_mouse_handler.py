from approximator.services.plot.boundaries.draggable_boundary import DraggableSegmentBoundary
from approximator.data_models.data_structures import Segment


class SegmentMouseHandler:
    """
    Управляет событиями мыши: добавление сегментов, взаимодействие с интерактивными границами.
    Работает с объектной моделью Segment / ChannelState.
    """

    def __init__(self, main_window, app_state, plot_manager,
                 redraw_callback, update_table_callback, request_recalc_callback):
        self.main_window = main_window
        self.state = app_state
        self.plot_manager = plot_manager
        self.redraw_callback = redraw_callback
        self.update_table_callback = update_table_callback
        self.request_recalc_callback = request_recalc_callback

        self._boundaries = []  # Все интерактивные границы текущего канала

        self._connect_events()

    def _connect_events(self):
        canvas = self.plot_manager.canvas
        canvas.mpl_connect("button_press_event", self._on_mouse_press)
        canvas.mpl_connect("button_release_event", self._on_mouse_release)
        canvas.mpl_connect("motion_notify_event", self._on_mouse_move)

    def _on_mouse_press(self, event):
        if event.button == 3:
            self._create_new_segment(event)
        elif event.button == 1:
            for boundary in self._boundaries:
                boundary.on_press(event)
                print(f"[mouse_handler] pressed boundary: {boundary.side} @ {boundary.x_position:.2f}")

    def _on_mouse_release(self, event):
        for boundary in self._boundaries:
            boundary.on_release(event)

        self.redraw_callback(preserve_zoom=True)
        self.update_table_callback()
        self.request_recalc_callback()

    def _on_mouse_move(self, event):
        for boundary in self._boundaries:
            boundary.on_motion(event)

        if event.xdata:
            self.main_window.statusBar().showMessage(f"X = {event.xdata:,.2f}")

    def _create_new_segment(self, event):
        """Добавляет новый Segment в активный канал по позиции X."""
        x = event.xdata
        if x is None or not self.state.active_channel_name:
            return

        channel = self.state.channel_states.get(self.state.active_channel_name)
        if not channel:
            return

        new_segment = Segment(x_start=x - 1.0, x_end=x + 1.0)
        channel.segments.append(new_segment)
        channel.segments.sort(key=lambda s: s.x_start)

        self.redraw_callback(preserve_zoom=True)
        self.update_table_callback()
        self.request_recalc_callback()

        self._rebuild_boundaries()  # подключаем интерактивность нового сегмента



    def _rebuild_boundaries(self):
        """Создаёт интерактивные объекты границ сегментов."""
        self._boundaries.clear()
        channel = self.state.channel_states.get(self.state.active_channel_name)
        if not channel or not channel.segments:
            return

        for i, segment in enumerate(channel.segments):
            for side in ['start', 'end']:
                def _on_click(s=segment, idx=i):
                    self.state.selected_segment_index = idx
                    #self.redraw_callback(preserve_zoom=True)

                boundary = DraggableSegmentBoundary(
                    ax=self.plot_manager.get_axes(),
                    segment=segment,
                    side=side,
                    on_move_callback=self.plot_manager.canvas.draw,
                    on_click_callback=_on_click
                )
                self._boundaries.append(boundary)