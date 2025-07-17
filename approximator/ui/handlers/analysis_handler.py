# Путь: ui/handlers/analysis_handler.py
# =================================================================================
# МОДУЛЬ ОБРАБОТЧИКА СОБЫТИЙ ВКЛАДКИ "АНАЛИЗ"
# =================================================================================
from PyQt5.QtWidgets import QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout, QColorDialog
from PyQt5.QtGui import QColor, QCursor
from PyQt5.QtCore import Qt

from approximator.data_models.segment import Segment
from approximator.services.math.standard_fitter import StandardFitter

class AnalysisEventHandler:
    def __init__(self, main_window, app_state, plot_manager, fitter):
        self.main_window = main_window
        self.state = app_state
        self.plot_manager = plot_manager
        self.fitter = fitter
        self._connect_events()

    def _connect_events(self):
        analysis_tab = self.main_window.analysis_tab
        analysis_tab.channel_combo.currentIndexChanged.connect(self._handle_channel_change)
        analysis_tab.offset_input.editingFinished.connect(self._handle_offset_change)
        analysis_tab.segments_table.itemChanged.connect(self._handle_segment_table_change)
        analysis_tab.segments_table.cellDoubleClicked.connect(self._handle_color_cell_double_click)
        analysis_tab.calculate_button.clicked.connect(self._handle_calculate_approximation)
        
        # Подключаем обработчики для элементов сшивки
        analysis_tab.stitch_checkbox.stateChanged.connect(self._handle_stitch_state_change)
        analysis_tab.stitch_method_combo.currentIndexChanged.connect(self._handle_stitch_method_change)
        
        # Подключаем полный набор обработчиков событий холста
        canvas = self.plot_manager.canvas
        canvas.mpl_connect('button_press_event', self._on_mouse_press)
        canvas.mpl_connect('button_release_event', self._on_mouse_release)
        canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        canvas.mpl_connect('pick_event', self._on_pick)  # Для "захвата" линий

    def _reset_analysis_tab(self):
        """Сбрасывает все виджеты на вкладке анализа к начальному состоянию."""
        self.main_window.analysis_tab.channel_combo.clear()
        self.main_window.analysis_tab.offset_input.setText("0.0")
        segments_table = self.main_window.analysis_tab.segments_table
        segments_table.clearContents()
        segments_table.setRowCount(0)
        self.plot_manager.clear_plot()
        
    def _handle_calculate_approximation(self):
        """Запускает процесс аппроксимации для активного канала."""
        channel_name = self.state.active_channel_name
        if not channel_name: return
        
        print(f"\nЗапуск аппроксимации для канала: {channel_name}")
        channel_state = self.state.channel_states[channel_name]
        df = self.state.merged_dataframe

        all_channel_names = set(self.state.channel_states.keys())
        time_column_candidates = list(set(df.columns) - all_channel_names)
        if not time_column_candidates: return
        time_column = time_column_candidates[0]

        for segment in channel_state.segments:
            if segment.is_excluded:
                segment.fit_result = None
                print(f"  - Сегмент {segment.label} исключен.")
                continue

            segment_data = df[
                (df[time_column] >= segment.x_start) & 
                (df[time_column] <= segment.x_end)
            ]
            x_data = segment_data[time_column]
            y_data = segment_data[channel_name].dropna()

            x_data = x_data[y_data.index]

            fit_res = self.fitter.fit(x_data, y_data, segment.poly_degree)
            segment.fit_result = fit_res

            if fit_res:
                print(f"  - Сегмент {segment.label} (степень {segment.poly_degree}): Успешно. RMSE = {fit_res.rmse:.4f}, R^2 = {fit_res.r_squared:.4f}")
            else:
                print(f"  - Сегмент {segment.label} (степень {segment.poly_degree}): Ошибка.")
        
        self._redraw_plot_for_active_channel()

    def _handle_channel_change(self, index: int):
        """Обрабатывает смену канала, корректно обновляя поле смещения."""
        if index == -1 or not self.state.channel_list: return
        try:
            channel_name = self.state.channel_list[index]
        except IndexError: return

        self.state.active_channel_name = channel_name
        
        channel_state = self.state.channel_states[channel_name]
        offset_input = self.main_window.analysis_tab.offset_input
        
        offset_input.blockSignals(True)
        offset_input.setText(str(channel_state.time_offset).replace('.', ','))
        offset_input.blockSignals(False)

        self._redraw_plot_for_active_channel()
        self._update_segments_table()
        
    def _handle_offset_change(self):
        """Сохраняет изменение смещения из поля ввода в состояние и перерисовывает график."""
        active_channel_name = self.state.active_channel_name
        if not active_channel_name: return

        offset_input = self.main_window.analysis_tab.offset_input
        
        try:
            new_offset = float(offset_input.text().replace(',', '.'))
            channel_state = self.state.channel_states[active_channel_name]
            channel_state.time_offset = new_offset
            
            print(f"Для канала '{active_channel_name}' сохранено смещение: {new_offset}")
            
            self._redraw_plot_for_active_channel()

        except (ValueError, KeyError):
            channel_state = self.state.channel_states[active_channel_name]
            offset_input.setText(str(channel_state.time_offset).replace('.', ','))
            print("Ошибка: введено некорректное значение смещения.")

    def _find_nearest_segment_boundary(self, x, y, threshold=10):
        """Находит ближайшую границу сегмента с учетом типа сегмента."""
        channel_name = self.state.active_channel_name
        if not channel_name:
            return None, None, None
        
        channel_state = self.state.channel_states[channel_name]
        if not channel_state.segments:
            return None, None, None
        
        min_dist = float('inf')
        nearest = None
        nearest_is_start = False
        selected_idx = self.state.selected_segment_index
        
        # Проверяем, есть ли рядом границы разных типов сегментов
        boundaries_at_x = []
        for segment in channel_state.segments:
            if abs(segment.x_start - x) < threshold:
                boundaries_at_x.append(('start', segment))
            if abs(segment.x_end - x) < threshold:
                boundaries_at_x.append(('end', segment))
        
        # Если есть несколько границ рядом
        if len(boundaries_at_x) > 1:
            # Приоритет выбранному сегменту
            selected_boundary = next((b for b in boundaries_at_x 
                                   if channel_state.segments.index(b[1]) == selected_idx), None)
            if selected_boundary:
                boundary_type, segment = selected_boundary
                return segment, boundary_type == 'start', segment.segment_type
            
            # Если нет выбранного, приоритет обычным сегментам
            regular_boundary = next((b for b in boundaries_at_x 
                                  if b[1].segment_type == "Обычный"), None)
            if regular_boundary:
                boundary_type, segment = regular_boundary
                return segment, boundary_type == 'start', segment.segment_type
            
            # Если нет обычных, берем первую маску
            boundary_type, segment = boundaries_at_x[0]
            return segment, boundary_type == 'start', segment.segment_type
        
        # Если граница только одна
        for segment in channel_state.segments:
            # Приоритет выбранному сегменту
            priority = 2 if channel_state.segments.index(segment) == selected_idx else 1
            
            # Проверяем левую границу
            dist = abs(segment.x_start - x)
            if dist < min_dist / priority and dist < threshold:
                min_dist = dist * priority
                nearest = segment
                nearest_is_start = True
            
            # Проверяем правую границу
            dist = abs(segment.x_end - x)
            if dist < min_dist / priority and dist < threshold:
                min_dist = dist * priority
                nearest = segment
                nearest_is_start = False
        
        if nearest:
            return nearest, nearest_is_start, nearest.segment_type
        return None, None, None

    def _on_mouse_press(self, event):
        """Обработчик нажатия кнопки мыши."""
        if not event.inaxes or event.button != 1:  # Только левая кнопка
            return
            
        segment, is_start, segment_type = self._find_nearest_segment_boundary(event.xdata, event.ydata)
        if segment:
            self.state.dragged_segment = segment
            self.state.dragged_is_start = is_start
            self.state.dragged_segment_type = segment_type
            self.state.drag_start_x = event.xdata
            
            # Подсветка границы при перетаскивании
            line_style = ':' if segment_type == "Маска" else '--'
            color = 'gray' if segment_type == "Маска" else segment.color
            line = self.ax.axvline(event.xdata, color=color, 
                                 linestyle=line_style, alpha=0.8, zorder=5)
            self.state.dragged_line = line
            self.canvas.draw_idle()

    def _on_mouse_release(self, event):
        """Обрабатывает отпускание кнопки мыши, завершая перетаскивание."""
        if self.state.dragged_line is None:
            return

        print("Перетаскивание завершено.")
        self.state.dragged_line.set_color('grey')
        self.state.dragged_line.set_linewidth(1.5)
        
        self._update_segments_from_drag(event.xdata)
        
        self.state.dragged_line = None
        self.state.dragged_boundary_index = None

        self._redraw_plot_for_active_channel()
        self._update_segments_table()

    def _on_mouse_move(self, event):
        """Обрабатывает движение мыши."""
        if self.state.dragged_line is not None:
            self.plot_manager.update_dragged_line_position(event.xdata)
            return

        is_over_line = False
        if event.inaxes:
            for line in self.plot_manager.boundary_lines:
                contains, _ = line.contains(event)
                if contains:
                    is_over_line = True
                    break
        
        if is_over_line:
            self.main_window.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.main_window.setCursor(QCursor(Qt.ArrowCursor))
            
        if event.inaxes:
            self.main_window.statusBar().showMessage(f"X = {event.xdata:.2f}, Y = {event.ydata:.2f}")
        else:
            self.main_window.statusBar().clearMessage()

    def _on_pick(self, event):
        """Обрабатывает событие 'захвата' интерактивного объекта (нашей линии)."""
        if event.mouseevent.button == 1 and self.state.dragged_line is None:
            picked_line = event.artist
            
            if picked_line in self.plot_manager.boundary_lines:
                self.state.dragged_line = picked_line
                # Находим индекс "захваченной" линии в списке
                self.state.dragged_boundary_index = self.plot_manager.boundary_lines.index(picked_line)
                
                picked_line.set_color('blue')
                picked_line.set_linewidth(2.5)
                self.plot_manager.canvas.draw()
                print(f"Захвачена граница с индексом {self.state.dragged_boundary_index}")

    def _create_new_segment(self, event):
        """Создает новый сегмент по правому клику мыши."""
        active_channel_name = self.state.active_channel_name
        if not active_channel_name: return
        
        channel_state = self.state.channel_states[active_channel_name]
        
        x_coord = float(event.xdata) - channel_state.time_offset
        
        current_boundaries = {seg.x_start for seg in channel_state.segments}
        current_boundaries.update({seg.x_end for seg in channel_state.segments})
        current_boundaries.add(x_coord)
        
        sorted_boundaries = sorted(list(current_boundaries))
        channel_state.regenerate_segments(sorted_boundaries)
        
        self._redraw_plot_for_active_channel()
        self._update_segments_table()

    def _update_segments_from_drag(self, new_x):
        """Обновляет границы сегментов при перетаскивании."""
        if not self.state.dragged_segment:
            return
            
        channel_name = self.state.active_channel_name
        if not channel_name:
            return
            
        channel_state = self.state.channel_states[channel_name]
        dragged_segment = self.state.dragged_segment
        is_start = self.state.dragged_is_start
        segment_type = self.state.dragged_segment_type
        
        # Получаем границы того же типа сегментов
        boundaries = []
        for seg in channel_state.segments:
            if seg.segment_type == segment_type:
                boundaries.extend([seg.x_start, seg.x_end])
        boundaries = sorted(list(set(boundaries)))
        
        # Определяем текущую позицию
        current_x = dragged_segment.x_start if is_start else dragged_segment.x_end
        current_idx = boundaries.index(current_x)
        
        # Ограничиваем движение соседними границами того же типа
        if current_idx > 0 and current_idx < len(boundaries) - 1:
            new_x = min(max(new_x, boundaries[current_idx-1]), boundaries[current_idx+1])
            
            # Обновляем все сегменты данного типа, использующие эту границу
            for segment in channel_state.segments:
                if segment.segment_type == segment_type:
                    if abs(segment.x_start - current_x) < 1e-6:
                        segment.x_start = new_x
                    if abs(segment.x_end - current_x) < 1e-6:
                        segment.x_end = new_x
        
        # Обновляем интерфейс
        self._redraw_plot()
        if hasattr(self, 'update_segment_table'):
            self.update_segment_table()

    def _handle_segment_table_change(self, item: QTableWidgetItem):
        """Обрабатывает изменение текста в ячейке (для степени полинома)."""
        if item.column() != 1: return
        row = item.row()
        channel_state = self.state.channel_states[self.state.active_channel_name]
        try:
            new_degree = int(item.text())
            segment = channel_state.segments[row]
            segment.poly_degree = new_degree
            print(f"Сегмент {segment.label} изменен. Новая степень: {new_degree}")
        except (ValueError, IndexError):
            segment = channel_state.segments[row]
            item.setText(str(segment.poly_degree)) 

    def _set_segment_excluded(self, segment: Segment, state: int):
        """Обрабатывает клик по чекбоксу."""
        is_checked = (state == Qt.Checked)
        segment.is_excluded = is_checked
        print(f"Сегмент {segment.label} изменен. Исключен: {is_checked}")
    
    def _handle_color_cell_double_click(self, row, column):
        """Обрабатывает двойной клик по ячейке цвета."""
        if column != 3: return
        channel_state = self.state.channel_states[self.state.active_channel_name]
        segment = channel_state.segments[row]
        new_color = QColorDialog.getColor(initial=QColor(segment.color), parent=self.main_window)
        if new_color.isValid():
            segment.color = new_color.name()
            self._update_segments_table()
            self._redraw_plot_for_active_channel()

    def _update_segments_table(self):
        """Обновляет таблицу сегментов данными из активного ChannelState."""
        table = self.main_window.analysis_tab.segments_table
        table.blockSignals(True)
        channel_name = self.state.active_channel_name
        if not channel_name or channel_name not in self.state.channel_states:
            table.setRowCount(0)
            table.blockSignals(False)
            return
        segments = self.state.channel_states[channel_name].segments
        table.setRowCount(len(segments))
        for i, seg in enumerate(segments):
            table.setItem(i, 0, QTableWidgetItem(seg.label))
            table.setItem(i, 1, QTableWidgetItem(str(seg.poly_degree)))
            checkbox = QCheckBox()
            checkbox.setChecked(seg.is_excluded)
            checkbox.stateChanged.connect(lambda state, s=seg: self._set_segment_excluded(s, state))
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            table.setCellWidget(i, 2, cell_widget)
            color_item = QTableWidgetItem()
            color_item.setBackground(QColor(seg.color))
            table.setItem(i, 3, color_item)
        table.blockSignals(False)

    def _redraw_plot_for_active_channel(self):
        """Перерисовывает график, передавая в PlotManager актуальное смещение."""
        channel_name = self.state.active_channel_name
        if not channel_name: return
        df = self.state.merged_dataframe
        channel_state = self.state.channel_states[channel_name]
        
        all_channel_names = set(self.state.channel_states.keys())
        time_column_candidates = list(set(df.columns) - all_channel_names)
        if not time_column_candidates: return
        time_column = time_column_candidates[0]
        
        self.plot_manager.plot_data(
            df=df, 
            x_col=time_column, 
            y_col=channel_name, 
            segments=channel_state.segments,
            time_offset=channel_state.time_offset
        )

    def _update_plot(self, preserve_zoom=True):
        """Обновляет график с опцией сохранения текущей позиции."""
        active_channel = self.state.active_channel_name
        if not active_channel or not hasattr(self.main_window, 'plot_manager'):
            return
            
        time_column = self.main_window.import_tab.time_column_combo.currentText()
        self.plot_manager.redraw_all_channels(
            df=self.state.merged_dataframe,
            x_col=time_column,
            channel_states=self.state.channel_states,
            active_channel_name=active_channel,
            selected_segment_index=self.state.selected_segment_index,
            preserve_zoom=preserve_zoom,
            show_source=self.state.show_source_data,
            show_approximation=self.state.show_approximation
        )

    def _handle_stitch_state_change(self, state):
        """Обрабатывает изменение состояния чекбокса сшивки."""
        try:
            active_channel = self.state.active_channel_name
            if active_channel and active_channel in self.state.channel_states:
                channel_state = self.state.channel_states[active_channel]
                enabled = bool(state)
                print(f"[stitch_handler] Setting stitch enabled to {enabled} for channel {active_channel}")
                
                # Обновляем состояние
                channel_state.stitch_enabled = enabled
                self.main_window.analysis_tab.stitch_method_combo.setEnabled(enabled)
                
                # Запускаем пересчет если нужно
                if self.state.auto_recalculate:
                    print("[stitch_handler] Auto recalculate triggered")
                    self._handle_calculate_approximation()
                    
                # Обновляем UI с сохранением позиции
                self._update_plot(preserve_zoom=True)
                    
        except Exception as e:
            print(f"Error in stitch state handler: {e}")

    def _handle_stitch_method_change(self, index):
        """Обрабатывает изменение метода сшивки в комбобоксе."""
        try:
            if index == -1:  # Пропускаем начальную инициализацию
                return
                
            active_channel = self.state.active_channel_name
            if active_channel and active_channel in self.state.channel_states:
                channel_state = self.state.channel_states[active_channel]
                print(f"[stitch_handler] Setting stitch method to {index} for channel {active_channel}")
                
                # Обновляем состояние
                channel_state.stitch_method = index
                
                # Запускаем пересчет если включена сшивка и авторасчет
                if channel_state.stitch_enabled and self.state.auto_recalculate:
                    print("[stitch_handler] Auto recalculate triggered")
                    self._handle_calculate_approximation()
                    
                # Обновляем UI с сохранением позиции
                self._update_plot(preserve_zoom=True)
                
        except Exception as e:
            print(f"Error in stitch method handler: {e}")

    def _get_stitch_params(self):
        """Возвращает текущие параметры сшивки для активного канала."""
        try:
            active_channel = self.state.active_channel_name
            if active_channel and active_channel in self.state.channel_states:
                channel_state = self.state.channel_states[active_channel]
                enabled = channel_state.stitch_enabled
                method = channel_state.stitch_method
                print(f"[stitch_params] Channel {active_channel}: enabled={enabled}, method={method}")
                return {
                    'enabled': enabled,
                    'method': method
                }
        except Exception as e:
            print(f"Error in get_stitch_params: {e}")
        return {'enabled': False, 'method': 0}