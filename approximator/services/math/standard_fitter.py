# Путь: services/math/standard_fitter.py
# =================================================================================
# МОДУЛЬ СТАНДАРТНОГО РЕЖИМА АППРОКСИМАЦИИ
# =================================================================================
import numpy as np
import pandas as pd
from typing import Optional
from approximator.data_models.fit_result import FitResult

class StandardFitter:

    def _make_fit_result_from_poly(self, poly, df, time_column, channel_name, x_start, x_end):
        """
        Создаёт FitResult из np.poly1d для заданного сегмента и данных.
        """
        mask = (df[time_column] >= x_start) & (df[time_column] <= x_end)
        x_data = df.loc[mask, time_column]
        y_data = df.loc[mask, channel_name]
        if len(x_data) == 0 or len(y_data) == 0:
            return None
        y_predicted = poly(x_data)
        residuals = y_data - y_predicted
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        rmse = np.sqrt(np.mean(residuals ** 2))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 1e-9 else 1.0
        return FitResult(
            coefficients=tuple(poly.coefficients),
            rmse=rmse,
            r_squared=r_squared,
            points_count=len(x_data)
        )
    """Выполняет независимую аппроксимацию для каждого сегмента."""
    
    def fit(self, x_data: pd.Series, y_data: pd.Series, degree: int) -> Optional[FitResult]:
        """
        Аппроксимирует данные полиномом заданной степени.
        """
        if len(x_data) <= degree:
            print(f"Предупреждение: недостаточно точек ({len(x_data)}) для аппроксимации полиномом {degree}-й степени.")
            return None

        try:
            coeffs = np.polyfit(x_data, y_data, degree)
            poly_func = np.poly1d(coeffs)
            y_predicted = poly_func(x_data)
            
            residuals = y_data - y_predicted
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y_data - np.mean(y_data))**2)
            
            rmse = np.sqrt(np.mean(residuals**2))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 1e-9 else 1.0

            return FitResult(
                coefficients=tuple(coeffs), 
                rmse=rmse, 
                r_squared=r_squared,
                points_count=len(x_data)
            )

        except Exception as e:
            print(f"Ошибка при аппроксимации: {e}")
            return None