# Путь: approximator/ui/plot_manager.py
# Путь: ui/plot_manager.py
# =================================================================================
# МОДУЛЬ МЕНЕДЖЕРА ОТРИСОВКИ
# =================================================================================
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.lines import Line2D
from data_models.channel_state import ChannelState

class PlotManager:
    def __init__(self, canvas: FigureCanvas):
        self.canvas = canvas
        self.figure: Figure = canvas.figure
        self.ax = self.figure.add_subplot(111)
        self.boundary_lines: List[Line2D] = []
        self._force_no_segment_highlight = False

    def clear_plot(self):
        self.ax.clear(); self.boundary_lines.clear(); self.ax.grid(True); self.canvas.draw()

    def update_dragged_line_position(self, x_pos: float):
        for line in self.boundary_lines:
            if line.get_linewidth() > 2:
                line.set_xdata([x_pos, x_pos]); self.canvas.draw_idle(); return

    def redraw_all_channels(
        self, 
        df: pd.DataFrame, 
        x_col: str, 
        channel_states: Dict[str, ChannelState],
        active_channel_name: str = "", 
        selected_segment_index: Optional[int] = None,
        preserve_zoom: bool = False, 
        show_source: bool = True, 
        show_approximation: bool = True,
        smoothed_df: Optional[pd.DataFrame] = None,
        dragged: bool = False
    ):
        print(f"[redraw_all_channels] dragged={dragged}, selected_segment_index={selected_segment_index}, active_channel_name={active_channel_name}")
        # Удаляем все axvspan (Rectangle) патчи с оси
        for patch in list(self.ax.patches):
            try:
                patch.remove()
            except Exception:
                pass
        if preserve_zoom: xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
        self.ax.clear(); self.boundary_lines.clear()
        # Жёстко удаляем все патчи и линии после clear (на случай, если matplotlib что-то кэширует)
        for patch in list(self.ax.patches):
            try:
                patch.remove()
            except Exception:
                pass
        
        # --- Отрисовка исходных данных ---
        if show_source:
            for name, state in channel_states.items():
                if not state.is_visible or name not in df.columns: continue
                
                x_data_raw = df[x_col] + state.time_offset
                y_data_raw = df[name]
                
                excluded_mask = df.index.isin(state.excluded_indices)
                
                is_active = (name == active_channel_name)
                base_thickness = getattr(state, 'thickness', 1.5)
                base_style = getattr(state, 'line_style', '-')
                line_alpha = 1.0 if is_active else 0.4
                line_width = base_thickness
                line_color = state.base_color
                # Основная линия: только оттенок (alpha) для активного канала
                self.ax.plot(x_data_raw[~excluded_mask], y_data_raw[~excluded_mask],
                             marker='.', markersize=2, linestyle=base_style,
                             alpha=1.0 if is_active else 0.4,
                             label=name, color=line_color, linewidth=line_width, zorder=3 if is_active else 1)
                self.ax.plot(x_data_raw[excluded_mask], y_data_raw[excluded_mask],
                             marker='.', markersize=2, linestyle='none', alpha=0.3, color='grey', zorder=1)

        # --- Отрисовка деталей активного канала (границы, аппроксимация, сглаживание) ---
        if active_channel_name and active_channel_name in channel_states:
            active_state = channel_states[active_channel_name]
            if active_state.is_visible:
                self._draw_active_channel_details(
                    active_state, selected_segment_index, show_approximation, df, smoothed_df, x_col, dragged=dragged
                )
        
        self.ax.legend().set_visible(False); self.ax.set_xlabel(x_col)
        self.ax.set_ylabel("Значение"); self.ax.grid(True)
        
        if preserve_zoom: self.ax.set_xlim(xlim); self.ax.set_ylim(ylim)
        else: self.figure.tight_layout()
        self.canvas.draw()
        
    def _draw_active_channel_details(
        self, 
        active_state: ChannelState, 
        selected_segment_index: Optional[int], 
        show_approximation: bool,
        source_df: pd.DataFrame,
        smoothed_df: Optional[pd.DataFrame],
        x_col: str,
        dragged: bool = False
    ):
        print(f"[_draw_active_channel_details] dragged={dragged}, _force_no_segment_highlight={getattr(self, '_force_no_segment_highlight', None)}, selected_segment_index={selected_segment_index}, segments={len(active_state.segments) if hasattr(active_state, 'segments') else 'N/A'}")
        # Если drag, не выделять сегмент вообще
        if dragged:
            selected_segment_index = None
        # --- [НОВЫЙ БЛОК] Отрисовка сглаженного сигнала ---
        # Проверяем, есть ли сглаженные данные и видим ли мы исходные
        if smoothed_df is not None and not smoothed_df.empty:
            smoothed_col_name = f"{active_state.name}_smoothed"
            if smoothed_col_name in smoothed_df.columns:
                x_data = source_df[x_col] + active_state.time_offset
                y_data_smoothed = smoothed_df[smoothed_col_name]
                
                # Рисуем сглаженную линию тонкой и полупрозрачной
                self.ax.plot(x_data, y_data_smoothed, color='gray', linestyle='-', linewidth=1.2, alpha=0.8, label=f"{active_state.name} (сглаж.)")
        # --- [КОНЕЦ НОВОГО БЛОКА] ---

        if not active_state.segments: return
        
        # Отрисовка выделения активного сегмента (только если не происходит drag)
        #if not dragged and selected_segment_index is not None and selected_segment_index < len(active_state.segments):
        if not dragged and not self._force_no_segment_highlight and selected_segment_index is not None and selected_segment_index < len(active_state.segments):
            sel_segment = active_state.segments[selected_segment_index]
            print(f"[axvspan] DRAW: x_start={sel_segment.x_start}, x_end={sel_segment.x_end}, color={sel_segment.color}")
            self.ax.axvspan(sel_segment.x_start + active_state.time_offset, sel_segment.x_end + active_state.time_offset,
                            color=sel_segment.color, alpha=0.15, zorder=-1)
        
        # Отрисовка границ сегментов
        boundaries = sorted(list({s.x_start for s in active_state.segments} | {s.x_end for s in active_state.segments}))
        for bx in boundaries:
            line = Line2D([bx + active_state.time_offset] * 2, self.ax.get_ylim(), 
                          color='grey', linestyle='--', linewidth=1.5, picker=5)
            self.ax.add_line(line); self.boundary_lines.append(line)
        
        # Отрисовка линий аппроксимации
        if show_approximation:
            for segment in active_state.segments:
                if segment.fit_result and not segment.is_excluded:
                    x_fit = np.linspace(segment.x_start, segment.x_end, 200) + active_state.time_offset
                    y_fit = np.poly1d(segment.fit_result.coefficients)(x_fit - active_state.time_offset)
                    color = getattr(segment, 'color', '#FF0000')
                    thickness = getattr(segment, 'thickness', 1.5)
                    style = getattr(segment, 'line_style', '-')
                    self.ax.plot(x_fit, y_fit, color=color, linestyle=style, linewidth=thickness)