# Путь: interactive_approximator/file_parsers/pyrometer_parser.py

# =================================================================================
# МОДУЛЬ ПАРСЕРА ДЛЯ ФАЙЛОВ ПИРОМЕТРА
# ... (описание остается тем же) ...
# =================================================================================

import pandas as pd
from .base_parser import BaseParser
from io import StringIO

class PyrometerParser(BaseParser):
    """Парсер для обработки двух форматов файлов от пирометра."""

    def _get_file_content_and_type(self, file_path: str):
        encodings_to_try = ['utf-8', 'cp1251']
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Читаем несколько первых строк для надежности
                    header_content = "".join(f.readlines(500)) # Читаем ~500 байт
                
                # Ищем ключевые слова без учета регистра
                if "irttsd" in header_content.lower():
                    # Если нашли, перечитываем весь файл целиком
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read(), "irttsd", encoding
                if "start time" in header_content.lower():
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read(), "excel", encoding
            except (UnicodeDecodeError, IndexError):
                continue
        return None, None, None

    def can_parse(self, file_path: str) -> bool:
        _, file_type, _ = self._get_file_content_and_type(file_path)
        return file_type is not None

    def parse(self, file_path: str) -> pd.DataFrame:
        content, file_type, encoding = self._get_file_content_and_type(file_path)
        
        if not content:
            return pd.DataFrame()
            
        try:
            if file_type == "irttsd":
                print(f"  -> Обнаружен формат пирометра: IRTTSD (кодировка: {encoding})")
                return self._parse_irttsd(content)
            elif file_type == "excel":
                print(f"  -> Обнаружен формат пирометра: Excel-копия (кодировка: {encoding})")
                return self._parse_excel_copy(content)
            return pd.DataFrame()
        except Exception as e:
            print(f"Ошибка при парсинге файла пирометра {file_path}: {e}")
            return pd.DataFrame()

    def _parse_irttsd(self, content: str) -> pd.DataFrame:
        data = StringIO(content)
        df = pd.read_csv(data, skiprows=4, header=None, usecols=[1, 2], sep=',')
        df.columns = ['Timestamp_ms', 'Temperature']
        df['Timestamp_ms'] = pd.to_numeric(df['Timestamp_ms'], errors='coerce')
        df.dropna(inplace=True)
        if df.empty: return pd.DataFrame()
        
        t_start = df['Timestamp_ms'].iloc[0]
        df['Time'] = (df['Timestamp_ms'] - t_start) / 1000.0
        return df[['Time', 'Temperature']]

    def _parse_excel_copy(self, content: str) -> pd.DataFrame:
        lines = content.splitlines()
        header_row_index = -1
        for i, line in enumerate(lines):
            if line.strip().upper().startswith("INDEX"):
                header_row_index = i
                break
        if header_row_index == -1: return pd.DataFrame()

        data_string = '\n'.join(lines[header_row_index:])
        df = pd.read_csv(StringIO(data_string), sep='\t', decimal=',')
        required_cols = {'DATE', 'TIME', 'VALUE'}
        if not required_cols.issubset(df.columns): return pd.DataFrame()

        df['datetime'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'])
        if df.empty: return pd.DataFrame()

        t_start = df['datetime'].iloc[0]
        df['Time'] = (df['datetime'] - t_start).dt.total_seconds()
        df.rename(columns={'VALUE': 'Temperature'}, inplace=True)
        return df[['Time', 'Temperature']]