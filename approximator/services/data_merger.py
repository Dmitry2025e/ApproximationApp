# Путь: approximator/services/data_merger.py
# Путь: interactive_approximator/services/data_merger.py

# =================================================================================
# МОДУЛЬ ОБЪЕДИНЕНИЯ ДАННЫХ
#
# НАЗНАЧЕНИЕ:
#   Этот модуль отвечает за слияние нескольких DataFrame'ов, полученных
#   от разных парсеров, в одну общую таблицу.
#
# ЛОГИКА РАБОТЫ:
#   Предполагается, что все входящие DataFrame'ы уже содержат колонку
#   'Time' с относительным временем в секундах.
#
#   1.  Фильтрует список, оставляя только те DataFrame'ы, где есть 'Time'.
#   2.  Выполняет внешнее объединение (outer merge) по колонке 'Time'.
#       Это сохраняет все временные метки из всех файлов.
#   3.  Сортирует итоговую таблицу по времени.
#
# =================================================================================

import pandas as pd
from typing import List

class DataMerger:
    """
    Сервис для объединения нескольких DataFrame'ов в один
    на основе общей колонки времени 'Time'.
    """
    def merge_dataframes(self, dataframes: List[pd.DataFrame], on_column: str = 'Time') -> pd.DataFrame:
        """
        Объединяет список DataFrame'ов по общей колонке.

        :param dataframes: Список DataFrame'ов для объединения.
        :param on_column: Имя общей колонки (по умолчанию 'Time').
        :return: Один объединенный и отсортированный DataFrame.
        """
        if not dataframes:
            return pd.DataFrame()

        # Оставляем только те таблицы, где есть нужная колонка
        valid_dfs = [df for df in dataframes if on_column in df.columns]

        if not valid_dfs:
            print(f"Ошибка: Ни в одном из файлов не найдена колонка '{on_column}' для объединения.")
            return pd.DataFrame()

        # Начинаем с первой таблицы в списке
        merged_df = valid_dfs[0]

        # Последовательно присоединяем остальные
        for i in range(1, len(valid_dfs)):
            merged_df = pd.merge(merged_df, valid_dfs[i], on=on_column, how='outer')

        # Сортируем данные по времени и сбрасываем индекс
        merged_df = merged_df.sort_values(by=on_column).reset_index(drop=True)
        
        print(f"Объединение завершено. Итоговая таблица: {merged_df.shape[0]} строк, {merged_df.shape[1]} колонок.")
        return merged_df