# Путь: ui/handlers/segment_table_handler.py
# =================================================================================
# МОДУЛЬ ОБРАБОТЧИКА СОБЫТИЙ ТАБЛИЦЫ СЕГМЕНТОВ
# =================================================================================
from PyQt5.QtWidgets import (QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout, 
                            QColorDialog, QHeaderView, QComboBox, QTableWidget,
                            QPushButton)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

from approximator.data_models.segment import Segment

class SegmentTableHandler:
    """Обработчик таблицы сегментов."""
    
    # Определение колонок таблицы
    COLUMNS = ['x_start', 'x_end', 'poly_degree', 'segment_type', 'thickness', 'line_style', 'color']
    HEADERS = ["Начало", "Конец", "Степень", "Тип", "Толщина", "Стиль", "Цвет"]
    
    # Типы сегментов
    SEGMENT_TYPES = ["Обычный", "Маска"]
    
    # Стили линий
    LINE_STYLES = ['-', '--', '-.', ':']
    LINE_STYLE_NAMES = ['Сплошная', 'Пунктирная', 'Штрихпунктирная', 'Точечная']
    
    # def __init__(self, main_window, state, fitter, redraw_callback=None,
    #              update_table_callback=None, get_stitch_params=None):
    #     """Инициализация обработчика таблицы сегментов."""
    #     self.main_window = main_window
    #     self.state = state
    #     self.fitter = fitter
    #     self.redraw_callback = redraw_callback if redraw_callback else lambda *a, **kw: None
    #     self.update_table_callback = update_table_callback if update_table_callback else lambda: None
    #     self.get_stitch_params = get_stitch_params if get_stitch_params else lambda: {'enabled': False, 'method': 1}
    #     self._handlers = {}
    #
    #     # Инициализируем базовые атрибуты
    #     self.analysis_tab = None
    #     self.segment_table = None
    #
    #     # Пытаемся найти таблицу сегментов
    #     self._find_segments_table()
    #
    #     # Настраиваем таблицу, если она найдена
    #     if self.segment_table:
    #         self._setup_table()
    #         self._connect_events()
    #     else:
    #         print("WARNING: segments_table not found in analysis_tab")
    #
    # def __init__(self, main_window, app_state, fitter, redraw_callback, update_table_callback, get_stitch_params=None):
    #     """Инициализация обработчика таблицы сегментов."""
    #     self.main_window = main_window
    #     self.state = app_state
    #     self.fitter = fitter
    #     self.redraw_callback = redraw_callback
    #     self.update_table_callback = update_table_callback
    #     self.get_stitch_params = get_stitch_params or (lambda: {'enabled': False, 'method': 1})
    #
    #     # Инициализируем таблицу
    #     self.table_widget = self.main_window.analysis_tab.segments_table
    #     self.table_widget.setColumnCount(len(self.COLUMNS))
    #     self.table_widget.setHorizontalHeaderLabels(self.HEADERS)
    #     self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
    #     self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
    #
    #     # Подключаем обработчики событий
    #     self.table_widget.cellChanged.connect(self._on_cell_changed)
    #     self.table_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def __init__(self, main_window, app_state, fitter, redraw_callback=None,
                 update_table_callback=None, get_stitch_params=None):
        """Инициализация обработчика таблицы сегментов."""

        self.main_window = main_window
        self.state = app_state
        self.fitter = fitter
        self.redraw_callback = redraw_callback or (lambda *a, **kw: None)
        self.update_table_callback = update_table_callback or (lambda: None)
        self.get_stitch_params = get_stitch_params or (lambda: {'enabled': False, 'method': 1})
        self._handlers = {}

        # Получаем таблицу сегментов из analysis_tab
        self.segment_table = self.main_window.analysis_tab.segments_table
        self.segment_table.setColumnCount(len(self.COLUMNS))
        self.segment_table.setHorizontalHeaderLabels(self.HEADERS)
        self.segment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.segment_table.setSelectionMode(QTableWidget.SingleSelection)

        # Подключаем обработчики событий
        self.segment_table.cellChanged.connect(self._on_cell_changed)
        self.segment_table.itemSelectionChanged.connect(self._on_selection_changed)

    def _find_segments_table(self):
        """Находит таблицу сегментов в главном окне."""
        # Находим вкладку анализа
        if hasattr(self.main_window, 'analysis_tab'):
            self.analysis_tab = self.main_window.analysis_tab
            
        # Находим таблицу сегментов
        if self.analysis_tab and hasattr(self.analysis_tab, 'segments_table'):
            self.segment_table = self.analysis_tab.segments_table
            
        self._setup_table()
        self._connect_events()
        
    def _setup_table(self):
        """Настройка таблицы сегментов."""
        if not self.segment_table:
            print("WARNING: Cannot setup table - table widget is None")
            return
            
        self.segment_table.setColumnCount(len(self.COLUMNS))
        self.segment_table.setHorizontalHeaderLabels(self.HEADERS)
        header = self.segment_table.horizontalHeader()
        for i in range(len(self.COLUMNS)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            
        # Разрешаем выделение только целых строк
        self.segment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.segment_table.setSelectionMode(QTableWidget.SingleSelection)
    
    def _connect_events(self):
        """Подключение обработчиков событий."""
        if not self.segment_table:
            print("WARNING: Cannot connect events - table widget is None")
            return
            
        # События таблицы
        self.segment_table.cellChanged.connect(self._on_cell_changed)
        self.segment_table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.segment_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # События кнопок
        analysis_tab = self.main_window.analysis_tab
        if hasattr(analysis_tab, 'merge_segment_button'):
            analysis_tab.merge_segment_button.clicked.connect(self._handle_merge_segment)
        if hasattr(analysis_tab, 'remove_segment_button'):
            analysis_tab.remove_segment_button.clicked.connect(self._handle_remove_segment)
        if hasattr(analysis_tab, 'reset_segments_button'):
            analysis_tab.reset_segments_button.clicked.connect(self._handle_reset_segments)
            
    def _on_selection_changed(self):
        """Обработчик изменения выделения в таблице."""
        try:
            selected_items = self.segment_table.selectedItems()
            if not selected_items:
                self.state.selected_segment_index = None
            else:
                self.state.selected_segment_index = selected_items[0].row()
            self.redraw_callback(preserve_zoom=True)
        except Exception as e:
            print(f"Error in selection change handler: {e}")
            
    def _fit_segments(self):
        """Выполнить fit для активного канала."""
        active_channel = self.state.active_channel_name
        if active_channel and active_channel in self.state.channel_states:
            channel_state = self.state.channel_states[active_channel]
            df = self.state.merged_dataframe
            if df is not None and not df.empty:
                time_column = None
                if hasattr(self.main_window.import_tab, 'time_column_combo'):
                    time_column = self.main_window.import_tab.time_column_combo.currentText()
                if not time_column:
                    all_columns = df.columns
                    if 'Time' in all_columns:
                        time_column = 'Time'
                    else:
                        time_column = all_columns[0] if len(all_columns) > 0 else None
                if not time_column:
                    return

                print(f"[_fit_segments] Fitting segments for channel {active_channel}, time column: {time_column}")
                for seg in channel_state.segments:
                    # Используем segment_type вместо is_excluded
                    if seg.segment_type == "Маска":
                        seg.fit_result = None
                        print(f"  - Segment {seg.label} is masked, skipping")
                        continue

                    mask = (df[time_column] >= seg.x_start) & (df[time_column] <= seg.x_end)
                    x_data = df.loc[mask, time_column]
                    y_data = df.loc[mask, active_channel]
                    
                    if len(x_data) < seg.poly_degree + 1:
                        print(f"  - Segment {seg.label} has too few points ({len(x_data)}) for degree {seg.poly_degree}, skipping")
                        seg.fit_result = None
                        continue

                    print(f"  - Fitting segment {seg.label} with {len(x_data)} points, degree {seg.poly_degree}")
                    try:
                        seg.fit_result = self.fitter.fit(x_data, y_data, seg.poly_degree)
                        if seg.fit_result:
                            print(f"    R² = {seg.fit_result.r_squared:.4f}, RMSE = {seg.fit_result.rmse:.4f}")
                    except Exception as e:
                        print(f"    Error fitting segment: {e}")
                        seg.fit_result = None
                        
                # После фитирования обновляем UI
                self.redraw_callback(preserve_zoom=True)

    def _connect_events(self):
        """Подключает обработчики событий."""
        # Подключаем события таблицы
        self.table_widget.currentCellChanged.connect(self._handle_selection_change)
        self.table_widget.itemChanged.connect(self._handle_item_change)
        
        # Подключаем кнопки
        analysis_tab = self.main_window.analysis_tab
        analysis_tab.merge_segment_button.clicked.connect(self._handle_merge_segment)
        analysis_tab.remove_segment_button.clicked.connect(self._handle_remove_segment)
        analysis_tab.reset_segments_button.clicked.connect(self._handle_reset_segments)

    def _create_handler_key(self, segment_id, handler_type):
        """Создает уникальный ключ для обработчика события."""
        return f"{segment_id}_{handler_type}"

    def _get_or_create_handler(self, segment, handler_type, combo=None):
        """Создает или возвращает существующий обработчик для сегмента."""
        handler_key = self._create_handler_key(id(segment), handler_type)
        
        if handler_key not in self._handlers:
            if handler_type == 'type':
                def handler(idx, s=segment, c=combo):
                    try:
                        new_type = c.itemText(idx)
                        if s.segment_type != new_type:
                            s.segment_type = new_type
                            self._fit_segments()
                            self.redraw_callback(preserve_zoom=True)
                    except Exception as e:
                        print(f"Error in segment type handler: {e}")
                self._handlers[handler_key] = handler
            elif handler_type == 'line_style':
                def handler(idx, s=segment, c=combo):
                    try:
                        new_style = c.itemText(idx)
                        if s.line_style != new_style:
                            s.line_style = new_style
                            self.redraw_callback(preserve_zoom=True)
                    except Exception as e:
                        print(f"Error in line style handler: {e}")
                self._handlers[handler_key] = handler
                
        return self._handlers.get(handler_key)

    def _create_table_cell(self, row, col, segment):
        """Создает ячейку таблицы для заданного столбца."""
        column_name = self.COLUMNS[col]
        
        if column_name == 'exclude':
            checkbox = QCheckBox()
            checkbox.setChecked(segment.is_excluded)
            handler = lambda state: self._handle_exclude_state_change(bool(state), segment)
            checkbox.stateChanged.connect(handler)
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            return widget
            
        elif column_name == 'segment_type':
            combo = QComboBox()
            combo.addItems(["Обычный", "Исключённый", "Маска"])
            combo.setCurrentText(segment.segment_type)
            combo.blockSignals(True)  # Блокируем сигналы при создании
            try:
                handler = lambda idx: self._handle_type_change(idx, segment)
                combo.currentIndexChanged.connect(handler)
            finally:
                combo.blockSignals(False)  # Разблокируем сигналы
            return combo
            
        elif column_name == 'style':
            combo = QComboBox()
            combo.addItems(["-", "--", "-.", ":"])
            combo.setCurrentText(segment.line_style)
            combo.blockSignals(True)  # Блокируем сигналы при создании
            try:
                handler = lambda idx: self._handle_style_change(idx, segment)
                combo.currentIndexChanged.connect(handler)
            finally:
                combo.blockSignals(False)  # Разблокируем сигналы
            return combo
            
        elif column_name == 'color':
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(4, 4, 4, 4)
            
            def show_color_dialog():
                try:
                    active_channel = self.state.active_channel_name
                    if not active_channel or active_channel not in self.state.channel_states:
                        return
                        
                    segment = self.state.channel_states[active_channel].segments[row]
                    current_color = getattr(segment, 'color', '#000000')
                    current_color = current_color if isinstance(current_color, str) else '#000000'
                    
                    color = QColorDialog.getColor(QColor(current_color))
                    if color.isValid():
                        try:
                            segment.color = color.name()
                            widget.setStyleSheet(f'background-color: {color.name()}; border: 1px solid #808080;')
                            self.redraw_callback()
                        except Exception as e:
                            print(f"Error setting color: {e}")
                except Exception as e:
                    print(f"Error in color dialog: {e}")
            
            widget.mousePressEvent = lambda e: show_color_dialog()
            
            try:
                # Установим текущий цвет как фон виджета
                active_channel = self.state.active_channel_name
                if active_channel and active_channel in self.state.channel_states:
                    segment = self.state.channel_states[active_channel].segments[row]
                    color = getattr(segment, 'color', '#000000')
                    color = color if isinstance(color, str) else '#000000'
                    widget.setStyleSheet(f'background-color: {color}; border: 1px solid #808080;')
            except Exception as e:
                print(f"Error setting initial color: {e}")
                widget.setStyleSheet('background-color: #000000; border: 1px solid #808080;')
                
            return widget
            
        elif column_name == 'visible':
            checkbox = QCheckBox()
            checkbox.setStyleSheet('QCheckBox { margin: 5px; }')
            
            active_channel = self.state.active_channel_name
            if active_channel and active_channel in self.state.channel_states:
                segment = self.state.channel_states[active_channel].segments[row]
                checkbox.setChecked(not hasattr(segment, 'visible') or segment.visible)
            
            def on_visibility_changed(state):
                if not active_channel or active_channel not in self.state.channel_states:
                    return
                segment = self.state.channel_states[active_channel].segments[row]
                segment.visible = bool(state)
                self.redraw_callback()
                
            checkbox.stateChanged.connect(on_visibility_changed)
            return checkbox
        
        return None  # Для остальных столбцов

    def _handle_exclude_state_change(self, state, segment):
        """Обработчик изменения состояния исключения сегмента."""
        try:
            segment.is_excluded = state
            segment.segment_type = "Исключённый" if state else "Обычный"
            print(f"[exclude_handler] Changed segment {segment.label} excluded state to {state}")
            self.update_table_callback()  # Обновим всю таблицу
            self._fit_update_redraw()
        except Exception as e:
            print(f"Error in exclude handler: {e}")
            
    def _update_segment_type(self, segment, new_type, row):
        """Безопасно обновляет тип сегмента."""
        try:
            segment.segment_type = new_type
            segment.is_excluded = (new_type == "Исключённый")
            
            # Обновляем только состояние UI без вызова обработчиков
            self.table_widget.blockSignals(True)
            try:
                type_combo = self.table_widget.cellWidget(row, self.COLUMNS.index('segment_type'))
                if type_combo:
                    type_combo.setCurrentText(new_type)
                
                exclude_widget = self.table_widget.cellWidget(row, self.COLUMNS.index('exclude'))
                if exclude_widget:
                    checkbox = exclude_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(segment.is_excluded)
            finally:
                self.table_widget.blockSignals(False)
                
            # Перерисовываем с сохранением масштаба
            self._fit_segments()
            self.redraw_callback(preserve_zoom=True)
            
        except Exception as e:
            print(f"Error updating segment type: {e}")

    def _handle_type_change(self, idx, segment):
        """Обработчик изменения типа сегмента."""
        try:
            if idx == -1:  # Пропускаем начальную инициализацию
                return
                
            if 0 <= idx < len(self.SEGMENT_TYPES):
                new_type = self.SEGMENT_TYPES[idx]
                print(f"[type_handler] Changing segment type to {new_type}")
                
                # Обновляем тип сегмента
                segment.segment_type = new_type
                segment.update_label()
                
                # Запускаем перерасчет с учетом нового типа
                self._fit_segments()
                
                # Обновляем отображение
                self.update_table()
                self.redraw_callback(preserve_zoom=True)
        except Exception as e:
            print(f"Error in type change handler: {e}")

    def update_table(self):
        """Обновляет таблицу сегментов."""
        if not self.segment_table:
            print("WARNING: Cannot update table - table widget is None")
            return
            
        try:
            self.segment_table.blockSignals(True)  # Блокируем сигналы
            
            active_channel = self.state.active_channel_name
            if not active_channel or active_channel not in self.state.channel_states:
                self.segment_table.setRowCount(0)
                return

            channel_state = self.state.channel_states[active_channel]
            if not channel_state.segments:
                self.segment_table.setRowCount(0)
                return

            self.segment_table.setRowCount(len(channel_state.segments))
            
            for row, segment in enumerate(channel_state.segments):
                for col, column_name in enumerate(self.COLUMNS):
                    cell_widget = self._create_table_cell(row, col, segment)
                    if cell_widget:
                        self.segment_table.setCellWidget(row, col, cell_widget)
                    else:
                        item = QTableWidgetItem(str(getattr(segment, column_name, '')))
                        self.segment_table.setItem(row, col, item)
                        
        except Exception as e:
            print(f"Error updating segment table: {e}")
        finally:
            self.segment_table.blockSignals(False)  # Разблокируем сигналы

    def _handle_merge_segment(self):
        idx = self.state.selected_segment_index
        if idx is None or idx == 0: return
        channel_state = self.state.channel_states[self.state.active_channel_name]
        prev_segment, current_segment = channel_state.segments[idx - 1], channel_state.segments[idx]
        prev_segment.x_end = current_segment.x_end
        prev_segment.update_label(); del channel_state.segments[idx]
        self.state.selected_segment_index = idx - 1
        self._fit_update_redraw()

    def _handle_remove_segment(self):
        idx = self.state.selected_segment_index
        if idx is None: return
        channel_state = self.state.channel_states[self.state.active_channel_name]
        if len(channel_state.segments) <= 1: return
        segment_to_remove = channel_state.segments[idx]
        print(f"[_handle_remove_segment] Removing segment {segment_to_remove.label}")
        
        if idx > 0:
            channel_state.segments[idx - 1].x_end = segment_to_remove.x_end
            channel_state.segments[idx - 1].update_label()
        elif idx + 1 < len(channel_state.segments):
            channel_state.segments[idx + 1].x_start = segment_to_remove.x_start
            channel_state.segments[idx + 1].update_label()
            
        del channel_state.segments[idx]
        self.state.selected_segment_index = max(0, idx - 1)
        
        self._fit_update_redraw()
        
    def _handle_reset_segments(self):
        channel_name = self.state.active_channel_name
        if not channel_name: return
        channel_state = self.state.channel_states[channel_name]
        df, time_col = self.state.merged_dataframe, "Time"
        time_min, time_max = df[time_col].min(), df[time_col].max()
        # Сохраняем старые цвета и стили по границам
        old_segments = getattr(channel_state, 'segments', [])
        new_segment = Segment(x_start=time_min, x_end=time_max, color=channel_state.base_color)
        for old in old_segments:
            if abs(old.x_start - new_segment.x_start) < 1e-8 and abs(old.x_end - new_segment.x_end) < 1e-8:
                new_segment.color = getattr(old, 'color', channel_state.base_color)
                new_segment.line_style = getattr(old, 'line_style', '-')
        channel_state.segments = [new_segment]
        self.state.selected_segment_index = 0
        
        self._fit_update_redraw()

    def _handle_selection_change(self, current_row, current_column, prev_row, prev_column):
        """Обработчик изменения выделения в таблице сегментов."""
        try:
            if current_row < 0:
                self.state.selected_segment_index = None
                return

            active_channel = self.state.active_channel_name
            if not active_channel or active_channel not in self.state.channel_states:
                return

            channel_state = self.state.channel_states[active_channel]
            if not channel_state.segments or current_row >= len(channel_state.segments):
                return

            self.state.selected_segment_index = current_row
            self.redraw_callback(preserve_zoom=True)  # Сохраняем масштаб при смене выделения
            
        except Exception as e:
            print(f"Error in segment selection handler: {e}")

    def _handle_item_change(self, item: QTableWidgetItem):
        """Обработчик изменения ячейки таблицы."""
        if item.column() != 1: return  # Только для колонки степени полинома
        
        row = item.row()
        if not self.state.active_channel_name: return
        
        channel_state = self.state.channel_states[self.state.active_channel_name]
        if row >= len(channel_state.segments): return
        
        segment = channel_state.segments[row]
        try:
            new_degree = int(item.text())
            if new_degree != segment.poly_degree:
                print(f"[_handle_item_change] Changing polynomial degree from {segment.poly_degree} to {new_degree}")
                segment.poly_degree = new_degree
                self._fit_update_redraw()
        except (ValueError, IndexError):
            item.setText(str(segment.poly_degree))

    def _set_segment_excluded(self, segment: Segment, state: int):
        is_checked = (state == Qt.Checked)
        if is_checked != segment.is_excluded:
            segment.is_excluded = is_checked
            self._fit_segments()
            self.update_table()
            self.redraw_callback(preserve_zoom=True)
    
    def _fit_update_redraw(self):
        """
        Выполняет последовательность: fit -> update -> redraw
        с правильным сохранением состояния.
        """
        print("[_fit_update_redraw] Starting fit-update-redraw sequence")
        self._fit_segments()  # Сначала пересчитываем аппроксимации
        self.update_table()   # Обновляем таблицу с результатами
        self.redraw_callback(preserve_zoom=True)  # Перерисовываем с сохранением масштаба
        print("[_fit_update_redraw] Sequence completed")
    
    def _on_cell_changed(self, row, column):
        """Обработчик изменения ячейки в таблице."""
        try:
            active_channel = self.state.active_channel_name
            if not active_channel or row >= len(self.state.channel_states[active_channel].segments):
                return
                
            segment = self.state.channel_states[active_channel].segments[row]
            header = self.COLUMNS[column]
            
            item = self.segment_table.item(row, column)
            if not item:
                return
                
            value = item.text()
            
            if header == 'poly_degree':
                try:
                    segment.poly_degree = max(1, min(10, int(value)))
                except ValueError:
                    pass
            elif header == 'segment_type':
                segment.segment_type = value
            elif header == 'x_start':
                try:
                    segment.x_start = float(value)
                    segment.update_label()
                except ValueError:
                    pass
            elif header == 'x_end':
                try:
                    segment.x_end = float(value)
                    segment.update_label()
                except ValueError:
                    pass
            elif header == 'thickness':
                try:
                    segment.thickness = float(value)
                except ValueError:
                    pass
            elif header == 'line_style':
                segment.line_style = value
                
            # После любого изменения пересчитываем аппроксимацию
            self._fit_segments()
            self.update_table()
            self.redraw_callback(preserve_zoom=True)
            
        except Exception as e:
            print(f"Error in cell changed handler: {e}")
            
    def update_table(self):
        """Обновляет содержимое таблицы."""
        # Переполучаем таблицу на случай, если она была создана после инициализации
        if not self.segment_table and hasattr(self, 'analysis_tab') and self.analysis_tab and hasattr(self.analysis_tab, 'segments_table'):
            self.segment_table = self.analysis_tab.segments_table
            
        if not self.segment_table:
            print("WARNING: Cannot update table - table widget is None")
            return
            
        self.segment_table.blockSignals(True)
        try:
            active_channel = self.state.active_channel_name
            if not active_channel or active_channel not in self.state.channel_states:
                self.segment_table.setRowCount(0)
                return
                
            channel_state = self.state.channel_states[active_channel]
            segments = channel_state.segments
            
            self.segment_table.setRowCount(len(segments))
            
            for row, segment in enumerate(segments):
                # Начало
                item = QTableWidgetItem(f"{segment.x_start:.2f}")
                self.segment_table.setItem(row, self.COLUMNS.index('x_start'), item)
                
                # Конец
                item = QTableWidgetItem(f"{segment.x_end:.2f}")
                self.segment_table.setItem(row, self.COLUMNS.index('x_end'), item)
                
                # Степень полинома
                item = QTableWidgetItem(str(segment.poly_degree))
                self.segment_table.setItem(row, self.COLUMNS.index('poly_degree'), item)
                
                # Тип сегмента (комбобокс)
                combo = QComboBox()
                combo.addItems(self.SEGMENT_TYPES)
                combo.setCurrentText(segment.segment_type)
                combo.currentTextChanged.connect(
                    self._get_or_create_handler(segment, 'type', combo))
                self.segment_table.setCellWidget(row, self.COLUMNS.index('segment_type'), combo)
                
                # Толщина
                item = QTableWidgetItem(f"{segment.thickness:.1f}")
                self.segment_table.setItem(row, self.COLUMNS.index('thickness'), item)
                
                # Стиль линии (комбобокс)
                combo = QComboBox()
                combo.addItems(self.LINE_STYLES)
                combo.setCurrentText(segment.line_style)
                combo.currentTextChanged.connect(
                    self._get_or_create_handler(segment, 'line_style', combo))
                self.segment_table.setCellWidget(row, self.COLUMNS.index('line_style'), combo)
                
                # Цвет
                color_widget = QWidget()
                color_layout = QHBoxLayout(color_widget)
                color_layout.setContentsMargins(2, 2, 2, 2)
                
                color_button = QPushButton()
                color_button.setFixedSize(20, 20)
                color_button.setStyleSheet(f"background-color: {segment.color}")
                color_button.clicked.connect(lambda checked, r=row: self._on_color_button_clicked(r))
                
                color_layout.addWidget(color_button)
                color_layout.addStretch()
                
                self.segment_table.setCellWidget(row, self.COLUMNS.index('color'), color_widget)
                
            # Восстанавливаем выделение
            if self.state.selected_segment_index is not None:
                self.segment_table.selectRow(self.state.selected_segment_index)
                
        finally:
            self.segment_table.blockSignals(False)
            
    def _on_segment_type_changed(self, row: int, new_type: str):
        """Обработчик изменения типа сегмента."""
        active_channel = self.state.active_channel_name
        if not active_channel or row >= len(self.state.channel_states[active_channel].segments):
            return
            
        segment = self.state.channel_states[active_channel].segments[row]
        if segment.segment_type != new_type:
            segment.segment_type = new_type
            self._fit_segments()
            self.redraw_callback(preserve_zoom=True)