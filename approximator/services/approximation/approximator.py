import numpy as np
from approximator.data_models.fit_result import FitResult


class Approximator:
    def prepare_data_for_fitting(self, data, segments):
        """
        Подготавливает данные для аппроксимации с учетом масок.
        Возвращает данные, исключая области, помеченные масками.
        """
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        
        # Находим все маски
        masks = [seg for seg in segments if seg.segment_type == "Маска"]
        
        # Создаем маску для исключения данных
        mask = np.ones(len(data), dtype=bool)
        for mask_segment in masks:
            # Исключаем данные в диапазоне маски
            mask_range = (data[:, 0] >= mask_segment.x_start) & (data[:, 0] <= mask_segment.x_end)
            mask[mask_range] = False
        
        # Применяем маску к данным
        return data[mask]

    def fit_segment(self, segment, data):
        """
        Аппроксимирует данные для одного сегмента с учетом масок.
        """
        if segment.segment_type == "Маска":
            return None  # Маски не аппроксимируются
            
        # Получаем данные в диапазоне сегмента
        mask = (data[:, 0] >= segment.x_start) & (data[:, 0] <= segment.x_end)
        segment_data = data[mask]
        
        if len(segment_data) < segment.poly_degree + 1:
            return None
            
        try:
            # Аппроксимация полиномом заданной степени
            coeffs = np.polyfit(segment_data[:, 0], segment_data[:, 1], segment.poly_degree)
            
            # Вычисление метрик
            poly = np.poly1d(coeffs)
            y_pred = poly(segment_data[:, 0])
            rmse = np.sqrt(np.mean((segment_data[:, 1] - y_pred) ** 2))
            
            # R-squared
            y_mean = np.mean(segment_data[:, 1])
            ss_tot = np.sum((segment_data[:, 1] - y_mean) ** 2)
            ss_res = np.sum((segment_data[:, 1] - y_pred) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return FitResult(
                coefficients=tuple(coeffs),
                rmse=rmse,
                r_squared=r_squared,
                points_count=len(segment_data)
            )
        except Exception as e:
            print(f"Ошибка аппроксимации: {e}")
            return None

    def fit_segments(self, segments, data):
        """
        Аппроксимирует данные для всех сегментов с учетом масок.
        """
        # Подготавливаем данные, исключая области масок
        filtered_data = self.prepare_data_for_fitting(data, segments)
        
        results = []
        for segment in segments:
            if segment.segment_type == "Маска":
                results.append(None)
                continue
                
            result = self.fit_segment(segment, filtered_data)
            results.append(result)
            
        return results