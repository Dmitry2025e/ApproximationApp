# Путь: approximator/data_models/channel_state.py

from dataclasses import dataclass, field
from typing import List, Optional, Set
from .data_structures import Segment


@dataclass
class ChannelState:
    """
    Хранит полное состояние анализа для одного канала данных.
    """
    name: str
    display_name: str = ""
    segments: List[Segment] = field(default_factory=list)
    time_offset: float = 0.0
    is_visible: bool = True
    base_color: str = "#1f77b4"
    excluded_indices: Set[int] = field(default_factory=set)
    thickness: float = 1.5
    line_style: str = "-"  # '-', '--', '-.', ':'
    stitch_enabled: bool = False
    stitch_method: int = 1  # 0 = C0, 1 = C1, 2 = C2

    def to_dict(self):
        return {
            'name': self.name,
            'display_name': self.display_name if self.display_name else self.name,
            'segments': [s.to_dict() for s in (self.segments or [])],
            'time_offset': self.time_offset,
            'is_visible': self.is_visible,
            'base_color': self.base_color,
            'excluded_indices': list(self.excluded_indices),
            'thickness': self.thickness,
            'line_style': self.line_style,
            'stitch_enabled': self.stitch_enabled,
            'stitch_method': self.stitch_method
        }

    @staticmethod
    def from_dict(d):
        """Безопасно создает объект ChannelState из словаря."""
        if not isinstance(d, dict):
            return ChannelState(name="unknown")
            
        try:
            # Безопасная десериализация сегментов
            segments = []
            for s in d.get('segments', []):
                try:
                    segment = Segment.from_dict(s)
                    if segment:
                        segments.append(segment)
                except Exception:
                    continue
                    
            return ChannelState(
                name=d.get('name', 'unknown'),
                display_name=d.get('display_name', ''),
                segments=segments,
                time_offset=float(d.get('time_offset', 0.0)),
                is_visible=bool(d.get('is_visible', True)),
                base_color=d.get('base_color', '#1f77b4'),
                excluded_indices=set(d.get('excluded_indices', [])),
                thickness=float(d.get('thickness', 1.5)),
                line_style=d.get('line_style', '-'),
                stitch_enabled=bool(d.get('stitch_enabled', False)),
                stitch_method=int(d.get('stitch_method', 1))
            )
        except Exception:
            return ChannelState(name="unknown")

    def __post_init__(self):
        if self.segments is None:
            self.segments = []

    def regenerate_segments(self, boundaries: List[float]):
        if len(boundaries) < 2:
            self.segments.clear()
            return

        old_segments = self.segments[:]
        self.segments.clear()

        for i in range(len(boundaries) - 1):
            start, end = boundaries[i], boundaries[i+1]
            new_segment = Segment(x_start=start, x_end=end)

            mid_point = start + (end - start) / 2
            best_match = None
            for old_seg in old_segments:
                if old_seg.x_start <= mid_point < old_seg.x_end:
                    best_match = old_seg
                    break
            
            if best_match:
                new_segment.poly_degree = best_match.poly_degree
                new_segment.is_excluded = best_match.is_excluded
                new_segment.color = best_match.color
            else:
                new_segment.color = self.base_color
            
            self.segments.append(new_segment)