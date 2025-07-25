# Путь: approximator/data_models/segment.py


from dataclasses import dataclass
from typing import Optional

from approximator.data_models.fit_result import FitResult


@dataclass
class Segment:
    """Представляет сегмент данных для аппроксимации."""
    x_start: float
    x_end: float
    label: str = ""
    poly_degree: int = 3
    segment_type: str = "Обычный"  # Только "Обычный" или "Маска"
    color: str = "#1f77b4"
    thickness: float = 1.5
    line_style: str = "-"
    fit_result: Optional[FitResult] = None

    def to_dict(self):
        return {
            'x_start': self.x_start,
            'x_end': self.x_end,
            'label': self.label,
            'poly_degree': self.poly_degree,
            'segment_type': self.segment_type,
            'color': self.color,
            'thickness': self.thickness,
            'fit_result': self.fit_result.to_dict() if self.fit_result else None,
            'line_style': self.line_style
        }

    @staticmethod
    def from_dict(d):
        """Создает объект Segment из словаря."""
        # Конвертируем старый формат is_excluded в новый формат типов
        if 'is_excluded' in d and d.get('is_excluded', False):
            segment_type = "Маска"
        else:
            segment_type = d.get('segment_type', 'Обычный')
            
        return Segment(
            x_start=d['x_start'],
            x_end=d['x_end'],
            label=d.get('label', ''),
            poly_degree=d.get('poly_degree', 3),
            color=d.get('color', '#1f77b4'),
            segment_type=segment_type,
            thickness=d.get('thickness', 1.5),
            line_style=d.get('line_style', '-'),
            fit_result=FitResult.from_dict(d.get('fit_result'))
        )

    def update_label(self):
        """Обновляет текстовую метку сегмента на основе его границ."""
        self.label = f"[{self.x_start:.2f} : {self.x_end:.2f}]"
        if self.segment_type == "Маска":
            self.label += " (Маска)"