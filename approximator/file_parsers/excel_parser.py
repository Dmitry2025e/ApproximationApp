# Путь: file_parsers/excel_parser.py

# =================================================================================
# МОДУЛЬ ПАРСЕРА ДЛЯ БИНАРНЫХ ФАЙЛОВ EXCEL (.xls, .xlsx)
#
# НАЗНАЧЕНИЕ:
#   Этот модуль отвечает за чтение данных непосредственно из бинарных
#   файлов Excel, созданных пирометрическим ПО.
#
# ЛОГИКА РАБОТЫ:
#   1.  Метод `can_parse` проверяет расширение файла (.xls или .xlsx).
#   2.  Метод `parse` использует библиотеку pandas, которая "под капотом"
#       использует `xlrd` или `openpyxl` для чтения файла.
#   3.  Он ищет в прочитанных данных строку "INDEX", чтобы найти начало
#       таблицы с данными.
#   4.  Выполняет нормализацию времени (вычисляет секунды от начала
#       записи) аналогично текстовому парсеру пирометра.
#
# =================================================================================

import pandas as pd
from .base_parser import BaseParser

class ExcelParser(BaseParser):
    """Парсер для бинарных файлов Excel (.xls, .xlsx)."""

    def can_parse(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.xls', '.xlsx'))

    def parse(self, file_path: str) -> pd.DataFrame:
        try:
            # Pandas автоматически выберет нужный "движок" (xlrd или openpyxl)
            # header=None говорит pandas не искать заголовки самостоятельно
            df_full = pd.read_excel(file_path, header=None)
            
            # Ищем строку, где находится заголовок нашей таблицы
            header_row_index = -1
            for i, row in df_full.iterrows():
                # Проверяем, есть ли 'INDEX' в первой ячейке строки
                if str(row.iloc[0]).strip().upper() == 'INDEX':
                    header_row_index = i
                    break
            
            if header_row_index == -1:
                print(f"Ошибка: в Excel файле не найдена строка с заголовком 'INDEX'.")
                return pd.DataFrame()
            
            # Перечитываем файл, начиная с нужной строки как с заголовка
            df = pd.read_excel(file_path, header=header_row_index)

            # Проверяем наличие необходимых колонок
            required_cols = {'DATE', 'TIME', 'VALUE'}
            if not required_cols.issubset(df.columns):
                print(f"Ошибка: в Excel файле отсутствуют необходимые колонки (DATE, TIME, VALUE).")
                return pd.DataFrame()
            
            # Преобразуем в datetime и нормализуем время
            df['datetime'] = pd.to_datetime(df['DATE'].astype(str) + ' ' + df['TIME'].astype(str))
            t_start = df['datetime'].iloc[0]
            df['Time'] = (df['datetime'] - t_start).dt.total_seconds()
            
            df.rename(columns={'VALUE': 'Temperature'}, inplace=True)
            
            print(f"  -> Обнаружен и обработан Excel файл: {file_path}")
            return df[['Time', 'Temperature']]

        except Exception as e:
            print(f"Ошибка при парсинге Excel файла {file_path}: {e}")
            return pd.DataFrame()

