from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class FitResult:
    """Хранит результат аппроксимации для одного сегмента."""
    coefficients: Tuple[float, ...] = field(default_factory=tuple)
    rmse: float = 0.0
    r_squared: float = 0.0
    # Количество точек, использованных для аппроксимации
    points_count: int = 0

    def to_dict(self):
        return {
            'coefficients': list(self.coefficients),
            'rmse': self.rmse,
            'r_squared': self.r_squared,
            'points_count': self.points_count
        }

    @staticmethod
    def from_dict(d):
        if not d:
            return None
        return FitResult(
            coefficients=tuple(d.get('coefficients', [])),
            rmse=d.get('rmse', 0.0),
            r_squared=d.get('r_squared', 0.0),
            points_count=d.get('points_count', 0)
        )
