from approximator.utils.log import debug

from approximator.ui.handlers.segment_mouse_handler import SegmentMouseHandler
from approximator.ui.handlers.segment_table_handler import SegmentTableHandler
from approximator.ui.handlers.analysis_setup_handler import AnalysisSetupHandler
from approximator.ui.handlers.import_event_handler import ImportEventHandler


def create_handlers(main_window):
    debug("[handler_initializer] → Инициализация обработчиков")

    # 🎯 Redraw plot function — центральное обновление
    def redraw_plot(preserve_zoom=False):
        debug(f"[redraw_plot] Запуск redraw с preserve_zoom={preserve_zoom}")

        # Перерисовка интерактивных границ
        if hasattr(main_window, 'segment_mouse_handler'):
            main_window.segment_mouse_handler._rebuild_boundaries()

        # Получение выбранной колонки времени из GUI
        time_column = None
        if hasattr(main_window.import_tab, 'time_selector'):
            time_column = main_window.import_tab.time_selector.get_selected()

        # Защита от пустого выбора
        if not time_column:
            debug("[redraw_plot] ❌ time_column не выбрана — пропуск отрисовки")
            return

        # Перерисовка графика
        main_window.plot_manager.redraw_all_channels(
            df=main_window.state.merged_dataframe,
            x_col=time_column,
            channel_states=main_window.state.channel_states,
            active_channel_name=main_window.state.active_channel_name,
            selected_segment_index=main_window.state.selected_segment_index,
            preserve_zoom=preserve_zoom,
            show_source=main_window.state.show_source_data,
            show_approximation=main_window.state.show_approximation
        )

    # ⚙️ Analysis setup handler
    main_window.analysis_setup_handler = AnalysisSetupHandler(
        main_window,
        main_window.state,
        redraw_callback = redraw_plot,
        update_segments_table_callback = lambda: main_window.segment_table_handler.update_table() if hasattr(main_window, 'segment_table_handler') else None,
        update_channels_callback = lambda: main_window.analysis_setup_handler.update_channels_table() if hasattr(main_window, 'analysis_setup_handler') else None
    )

    # 🔄 Анализ reset
    def analysis_reset():
        debug("[handler_initializer] ⟳ Сброс состояния анализа")
        if hasattr(main_window, 'analysis_setup_handler'):
            main_window.analysis_setup_handler.update_channels_table()
        if hasattr(main_window, 'segment_table_handler'):
            main_window.segment_table_handler.update_table()
        if hasattr(main_window, 'plot_manager'):
            redraw_plot(preserve_zoom=False)

    # 📥 Import handler — с прямыми зависимостями
    main_window.import_event_handler = ImportEventHandler(
        main_window = main_window,
        app_state = main_window.state,
        data_loader = main_window.data_loader,
        data_merger = main_window.data_merger,
        analysis_setup_handler = main_window.analysis_setup_handler,
        analysis_reset_callback = analysis_reset
    )

    # 📊 Segment table handler
    main_window.segment_table_handler = SegmentTableHandler(
        main_window,
        main_window.state,
        main_window.fitter,
        redraw_callback = redraw_plot,
        update_table_callback = lambda: main_window.segment_table_handler.update_table() if hasattr(main_window, 'segment_table_handler') else None,
        get_stitch_params = lambda: {'enabled': False, 'method': 1}
    )

    # 🖱️ Segment mouse handler
    main_window.segment_mouse_handler = SegmentMouseHandler(
        state = main_window.state,
        plot_manager = main_window.plot_manager,
        redraw_callback = redraw_plot,
        update_table_callback = lambda: main_window.segment_table_handler.update_table() if hasattr(main_window, 'segment_table_handler') else None,
        request_recalc_callback = main_window.request_recalculation
    )

    debug("[handler_initializer] ✅ Обработчики успешно созданы")