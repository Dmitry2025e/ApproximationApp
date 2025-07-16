# Путь: ui/handlers/analysis_setup_handler.py
# =================================================================================
# МОДУЛЬ ОБРАБОТЧИКА НАСТРОЙКИ АНАЛИЗА
# =================================================================================
from PyQt5.QtWidgets import QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout, QColorDialog, QHeaderView
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
import random

from data_models.channel_state import ChannelState

class AnalysisSetupHandler:
    def __init__(self, main_window, app_state, redraw_callback, update_segments_table_callback, update_channels_callback):
        self.main_window = main_window
        self.state = app_state
        self.redraw_callback = redraw_callback
        self.update_segments_table_callback = update_segments_table_callback
        self.update_channels_callback = update_channels_callback
        self._connect_events()

    def _connect_events(self):
        analysis_tab = self.main_window.analysis_tab
        table = analysis_tab.channels_table
        
        table.currentCellChanged.connect(self._handle_active_channel_change)
        table.itemChanged.connect(self._handle_offset_change)
        table.itemChanged.connect(self.handle_channel_name_edit)
        table.cellDoubleClicked.connect(self._handle_color_double_click)
        
        analysis_tab.show_all_channels_button.clicked.connect(self._show_all_channels)
        analysis_tab.hide_all_channels_button.clicked.connect(self._hide_all_channels)
        analysis_tab.restore_excluded_button.clicked.connect(self._handle_restore_excluded)
        
        analysis_tab.show_source_checkbox.stateChanged.connect(self._toggle_source_visibility)
        analysis_tab.show_approx_checkbox.stateChanged.connect(self._toggle_approx_visibility)
        analysis_tab.auto_recalc_checkbox.stateChanged.connect(self._toggle_auto_recalc)

    def _toggle_auto_recalc(self, state):
        self.state.auto_recalculate = (state == Qt.Checked)
        print(f"Автопересчет {'включен' if self.state.auto_recalculate else 'выключен'}.")

    def _toggle_source_visibility(self, state):
        self.state.show_source_data = (state == Qt.Checked)
        self.redraw_callback()

    def _toggle_approx_visibility(self, state):
        self.state.show_approximation = (state == Qt.Checked)
        self.redraw_callback()

    def _show_all_channels(self):
        for channel_name in self.state.channel_list:
            if channel_name in self.state.channel_states:
                self.state.channel_states[channel_name].is_visible = True
        self.update_channels_callback(); self.redraw_callback()

    def _hide_all_channels(self):
        for channel_name in self.state.channel_list:
            if channel_name in self.state.channel_states:
                self.state.channel_states[channel_name].is_visible = False
        self.update_channels_callback(); self.redraw_callback()

    def _handle_restore_excluded(self):
        active_channel_name = self.state.active_channel_name
        if not active_channel_name: return
        channel_state = self.state.channel_states[active_channel_name]
        if not channel_state.excluded_indices: return
        channel_state.excluded_indices.clear()
        self.redraw_callback()

    def _handle_active_channel_change(self, currentRow, currentColumn, previousRow, previousColumn):
        if currentRow != previousRow:
            if currentRow == -1 or currentRow >= len(self.state.channel_list):
                self.state.active_channel_name = ""
            else:
                self.state.active_channel_name = self.state.channel_list[currentRow]
            self.state.selected_segment_index = None
            self.update_channels_callback()
            self.update_segments_table_callback()
            self.redraw_callback()

    def _set_channel_visibility(self, channel_state: ChannelState, state: int):
        is_checked = (state == Qt.Checked)
        channel_state.is_visible = is_checked
        self.redraw_callback()

    def _handle_color_double_click(self, row, column):
        if column != 3 or row >= len(self.state.channel_list):
            return
        channel_name = self.state.channel_list[row]
        channel_state = self.state.channel_states.get(channel_name)
        if channel_state is None:
            return
        base_color = channel_state.base_color if channel_state.base_color else "#1f77b4"
        try:
            color_obj = QColor(base_color)
            if not color_obj.isValid():
                color_obj = QColor("#1f77b4")
        except Exception:
            color_obj = QColor("#1f77b4")
        new_color = QColorDialog.getColor(color_obj, self.main_window)
        if new_color.isValid():
            channel_state.base_color = new_color.name()
            self.update_channels_callback()
            self.redraw_callback()

    def _handle_offset_change(self, item: QTableWidgetItem):
        row, column = item.row(), item.column()
        if column != 2 or row >= len(self.state.channel_list): return
        channel_name = self.state.channel_list[row]
        channel_state = self.state.channel_states[channel_name]
        try:
            new_offset = float(item.text().replace(',', '.'))
            channel_state.time_offset = new_offset; self.redraw_callback()
        except (ValueError, KeyError):
            item.setText(str(channel_state.time_offset))

    def update_channels_table(self):
        from PyQt5.QtWidgets import QComboBox, QDoubleSpinBox
        table = self.main_window.analysis_tab.channels_table
        table.blockSignals(True)
        # 0: Название, 1: Показывать, 2: Смещение, 3: Цвет, 4: Толщина, 5: Стиль линии
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Название", "Показывать?", "Смещение, с", "Цвет", "Толщина", "Стиль линии"])
        table.resizeColumnsToContents()
        table.setRowCount(len(self.state.channel_list))
        normal_font, bold_font = QFont(), QFont(); bold_font.setBold(True)
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        line_styles = ['-', '--', '-.', ':']
        for i, channel_name in enumerate(self.state.channel_list):
            if channel_name not in self.state.channel_states: continue
            state = self.state.channel_states[channel_name]
            if state.base_color == "#1f77b4" and i > 0:
                 state.base_color = colors[i % len(colors)] if i < len(colors) else f"#{random.randint(0, 0xFFFFFF):06x}"
            # Editable display name
            display_name = state.display_name if state.display_name else channel_name
            name_item = QTableWidgetItem(display_name)
            name_item.setFont(bold_font if channel_name == self.state.active_channel_name else normal_font)
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            table.setItem(i, 0, name_item)
            # Показывать
            checkbox = QCheckBox(); checkbox.setChecked(state.is_visible)
            checkbox.stateChanged.connect(lambda s, st=state: self._set_channel_visibility(st, s))
            cell_widget = QWidget(); layout = QHBoxLayout(cell_widget)
            layout.addWidget(checkbox); layout.setAlignment(Qt.AlignCenter); layout.setContentsMargins(0,0,0,0)
            table.setCellWidget(i, 1, cell_widget)
            # Смещение
            offset_item = QTableWidgetItem(str(state.time_offset).replace('.', ',')); table.setItem(i, 2, offset_item)
            # Цвет
            color_item = QTableWidgetItem(); color_item.setBackground(QColor(state.base_color))
            color_item.setFlags(color_item.flags() & ~Qt.ItemIsEditable); table.setItem(i, 3, color_item)
            # Толщина
            thickness_spin = QDoubleSpinBox(); thickness_spin.setDecimals(2); thickness_spin.setMinimum(0.5); thickness_spin.setMaximum(10.0)
            thickness_spin.setValue(getattr(state, 'thickness', 1.5))
            def on_thickness_change(val, st=state):
                st.thickness = val; self.redraw_callback()
            thickness_spin.valueChanged.connect(on_thickness_change)
            table.setCellWidget(i, 4, thickness_spin)
            # Стиль линии
            style_combo = QComboBox(); style_combo.addItems(line_styles)
            style_combo.setCurrentText(getattr(state, 'line_style', '-'))
            def on_style_change(idx, st=state, combo=style_combo):
                st.line_style = combo.currentText(); self.redraw_callback()
            style_combo.currentIndexChanged.connect(on_style_change)
            table.setCellWidget(i, 5, style_combo)
        if self.state.active_channel_name in self.state.channel_list:
            table.selectRow(self.state.channel_list.index(self.state.active_channel_name))
        table.blockSignals(False)

    def handle_channel_name_edit(self, item):
        row, column = item.row(), item.column()
        if column != 0 or row >= len(self.state.channel_list): return
        channel_name = self.state.channel_list[row]
        channel_state = self.state.channel_states[channel_name]
        new_name = item.text().strip()
        if new_name:
            channel_state.display_name = new_name