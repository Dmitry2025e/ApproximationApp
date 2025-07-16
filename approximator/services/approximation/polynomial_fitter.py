# Путь: services/approximation/polynomial_fitter.py

import numpy as np
from typing import Optional, Tuple
from approximator.data_models.data_structures import FitResult

class PolynomialFitter:
    """Выполняет полиномиальную аппроксимацию данных."""
    
    def fit(self, x_data, y_data, degree: int) -> Optional[FitResult]:
        """Аппроксимирует данные полиномом заданной степени."""
        if len(x_data) < degree + 1:
            return None
            
        try:
            coeffs = np.polyfit(x_data, y_data, degree)
            poly = np.poly1d(coeffs)
            y_pred = poly(x_data)
            
            # Вычисляем метрики
            rmse = np.sqrt(np.mean((y_data - y_pred) ** 2))
            y_mean = np.mean(y_data)
            ss_tot = np.sum((y_data - y_mean) ** 2)
            ss_res = np.sum((y_data - y_pred) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return FitResult(
                coefficients=tuple(coeffs),
                rmse=rmse,
                r_squared=r_squared,
                points_count=len(x_data)
            )
        except Exception as e:
            print(f"Ошибка аппроксимации: {e}")
            return None
