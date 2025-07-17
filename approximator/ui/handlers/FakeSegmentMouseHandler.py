class FakeSegmentMouseHandler:
    def __init__(self, *, state, plot_manager, redraw_callback, update_table_callback, request_recalc_callback):
        from approximator.utils.log import debug
        debug("[FakeSegmentMouseHandler] __init__ called")
        debug(f"[FakeSegmentMouseHandler] state={type(state)}, plot_manager={type(plot_manager)}")
        debug(f"[FakeSegmentMouseHandler] redraw_callback={type(redraw_callback)}")
        debug(f"[FakeSegmentMouseHandler] update_table_callback={type(update_table_callback)}")
        debug(f"[FakeSegmentMouseHandler] request_recalc_callback={type(request_recalc_callback)}")