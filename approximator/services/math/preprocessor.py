# Путь: services/math/preprocessor.py
# =================================================================================
# МОДУЛЬ ПРЕДВАРИТЕЛЬНОЙ ОБРАБОТКИ ДАННЫХ
# =================================================================================

import pandas as pd
from scipy.signal import savgol_filter

class Preprocessor:
    """
    Содержит методы для предварительной обработки сигналов.
    """
    
    @staticmethod
    def apply_savgol_filter(
        source_data: pd.Series, 
        window_size: int, 
        poly_degree: int
    ) -> pd.Series:
        """
        Применяет фильтр Савицкого-Голея к ряду данных (одному каналу).

        :param source_data: Исходный временной ряд (объект pandas.Series).
        :param window_size: Размер окна фильтра. Должен быть нечетным и > poly_degree.
        :param poly_degree: Степень полинома для аппроксимации внутри окна.
        :return: Новый pandas.Series со сглаженными данными.
        """
        # --- Блок защиты от некорректных параметров ---
        if not isinstance(source_data, pd.Series) or source_data.empty:
            return pd.Series(dtype=float) # Возвращаем пустой ряд, если нет данных

        # Фильтр требует, чтобы в окне было достаточно точек
        if len(source_data) < window_size:
            print(
                f"Предупреждение: Длина данных ({len(source_data)}) меньше размера окна "
                f"({window_size}). Сглаживание не будет применено."
            )
            return source_data.copy() # Возвращаем копию исходных данных

        # Убедимся, что размер окна нечетный
        if window_size % 2 == 0:
            window_size += 1
            print(f"Предупреждение: Размер окна должен быть нечетным. Изменено на {window_size}.")

        if window_size <= poly_degree:
            print(
                f"Предупреждение: Размер окна ({window_size}) должен быть больше степени "
                f"полинома ({poly_degree}). Сглаживание не будет применено."
            )
            return source_data.copy()

        # --- Применение фильтра ---
        try:
            # Обрабатываем пропуски (NaN), интерполируя их линейно,
            # чтобы фильтр не выдал ошибку. Затем возвращаем NaN на свои места.
            nan_mask = source_data.isna()
            interpolated_data = source_data.interpolate(method='linear', limit_direction='both')
            
            smoothed_values = savgol_filter(interpolated_data, window_size, poly_degree)
            
            smoothed_series = pd.Series(smoothed_values, index=source_data.index)
            smoothed_series[nan_mask] = None # Возвращаем NaN туда, где они были
            
            return smoothed_series

        except Exception as e:
            print(f"Ошибка при применении фильтра Савицкого-Голея: {e}")
            return source_data.copy() # В случае ошибки возвращаем исходные данные