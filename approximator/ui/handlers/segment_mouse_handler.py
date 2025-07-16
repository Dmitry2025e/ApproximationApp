# Путь: ui/handlers/segment_mouse_handler.py
# =================================================================================
# МОДУЛЬ ОБРАБОТЧИКА СОБЫТИЙ МЫШИ НА ГРАФИКЕ
# =================================================================================
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt

class SegmentMouseHandler:
    def __init__(self, main_window, app_state, plot_manager, redraw_callback, update_table_callback, request_recalc_callback):
        self.main_window = main_window
        self.state = app_state
        self.plot_manager = plot_manager
        self.redraw_callback = redraw_callback
        self.update_table_callback = update_table_callback
        self.request_recalc_callback = request_recalc_callback
        self._dragging = False
        self._drag_start_x = None
        self._connect_events()
        # Удаляем кнопку режима анализа, если есть
        if hasattr(self.main_window.analysis_tab, 'cut_mode_button'):
            self.main_window.analysis_tab.cut_mode_button.hide()
            self.main_window.analysis_tab.cut_mode_button.setEnabled(False)

    def _connect_events(self):
        # Получаем canvas из plot_manager
        canvas = self.plot_manager.canvas
        self._cid_press = canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self._cid_release = canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self._cid_move = canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        
    def _create_new_segment(self, event):
        """Создает новый сегмент в точке клика правой кнопкой мыши."""
        if not self.state.active_channel_name:
            return
            
        x = event.xdata
        if x is None:
            return
            
        channel_state = self.state.channel_states.get(self.state.active_channel_name)
        if not channel_state:
            return
            
        segments = channel_state.get('segments', [])
        
        # Находим подходящее место для вставки нового сегмента
        new_segment = {'start': x - 1, 'end': x + 1}
        self._insert_segment(new_segment)
        self.redraw_callback(preserve_zoom=True)
        self.update_table_callback()
        self.request_recalc_callback()

    def _insert_segment(self, new_segment):
        """Вставляет новый сегмент в отсортированный список сегментов."""
        channel_state = self.state.channel_states.get(self.state.active_channel_name)
        if not channel_state:
            return

        segments = channel_state.get('segments', [])
        
        # Находим правильную позицию для вставки
        insert_pos = 0
        for i, segment in enumerate(segments):
            if new_segment['start'] < segment['start']:
                insert_pos = i
                break
            insert_pos = i + 1
            
        segments.insert(insert_pos, new_segment)
        channel_state['segments'] = segments
        
    def _update_segments_from_drag(self, new_x):
        """Обновляет позицию границы сегмента после перетаскивания."""
        if not self.state.active_channel_name or self._drag_start_x is None:
            return
            
        channel_state = self.state.channel_states.get(self.state.active_channel_name)
        if not channel_state:
            return
            
        segments = channel_state.get('segments', [])
        if not segments:
            return
            
        # Обновляем позицию границы
        self._dragging = False
        if self.state.selected_segment_index is not None:
            segment = segments[self.state.selected_segment_index]
            if abs(self._drag_start_x - segment['start']) < abs(self._drag_start_x - segment['end']):
                segment['start'] = new_x
            else:
                segment['end'] = new_x
                
        # Пересортируем сегменты если нужно
        segments.sort(key=lambda x: x['start'])
        channel_state['segments'] = segments
        
    def _on_mouse_press(self, event):
        """Обработчик нажатия кнопки мыши."""
        if event.button == 3:  # Правая кнопка мыши
            self._create_new_segment(event)
        elif event.button == 1 and self.state.selected_segment_index is not None:  # Левая кнопка мыши
            self._dragging = True
            self._drag_start_x = event.xdata

    def _on_mouse_release(self, event):
        """Обработчик отпускания кнопки мыши."""
        if self._dragging and event.xdata is not None:
            self._update_segments_from_drag(event.xdata)
            self.redraw_callback(preserve_zoom=True)
            self.update_table_callback()
            self.request_recalc_callback()
        self._dragging = False
        self._drag_start_x = None

    def _on_mouse_move(self, event):
        """Обработчик движения мыши."""
        if self._dragging and event.xdata is not None:
            # Показываем текущую позицию в статусбаре
            self.main_window.statusBar().showMessage(f"X = {event.xdata:,.2f}")
            # Обновляем отображение
            self.redraw_callback(preserve_zoom=True)