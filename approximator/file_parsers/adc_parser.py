# Путь: approximator/file_parsers/adc_parser.py

# =================================================================================
# МОДУЛЬ ПАРСЕРА ДЛЯ ФАЙЛОВ АЦП (TERMOSOFT)
#
# НАЗНАЧЕНИЕ:
#   Этот модуль отвечает за чтение и преобразование данных из файлов,
#   созданных программой TermoSoft.
#
# ЛОГИКА РАБОТЫ:
#   1.  Метод `can_parse` ищет ключевое слово "TermoSoft" в первой строке.
#       Файл должен быть в кодировке cp1251 (ANSI).
#   2.  Метод `parse` выполняет следующие шаги:
#       - Находит строку-маркер "#Tаблица:", чтобы определить начало данных.
#       - Извлекает имена каналов из строки после маркера, очищая их от
#         единиц измерения (", C").
#       - Читает табличные данные, используя в качестве разделителя табуляцию.
#       - Преобразует относительное время из формата "ЧЧ:ММ:СС:мс"
#         в общее количество секунд от начала записи.
#       - Возвращает DataFrame, где первая колонка - 'Time' (в секундах),
#         а остальные - данные из каждого канала.
#
# =================================================================================

import pandas as pd
import re
from .base_parser import BaseParser
from io import StringIO

class AdcParser(BaseParser):
    """Парсер для файлов формата 'АЦП (Терекс/TermoSoft)'."""

    def can_parse(self, file_path: str) -> bool:
        try:
            # Эти файлы часто используют старую кириллическую кодировку
            with open(file_path, 'r', encoding='cp1251') as f:
                return "TermoSoft" in f.readline()
        except Exception:
            return False

    def parse(self, file_path: str) -> pd.DataFrame:
        try:
            with open(file_path, 'r', encoding='cp1251') as f:
                lines = f.readlines()
            
            data_start_idx = -1
            for i, line in enumerate(lines):
                if "#Tаблица:" in line:
                    data_start_idx = i
                    break
            
            if data_start_idx == -1:
                return pd.DataFrame()

            header_line = lines[data_start_idx + 1].strip()
            
            # --- [ИСПРАВЛЕНИЕ ЗДЕСЬ] ---
            # 1. Разделяем строку по табуляции.
            split_headers = header_line.split('\t')
            # 2. Фильтруем список, чтобы удалить пустые строки, которые
            #    могут возникнуть из-за двойных или конечных табуляций.
            # 3. Затем очищаем каждое имя от единиц измерения и нормализуем.
            column_names = [
                str(re.sub(r',.*', '', col).strip()) 
                for col in split_headers if col.strip()
            ]
            
            data_string = ''.join(lines[data_start_idx + 2:])
            df = pd.read_csv(
                StringIO(data_string), 
                sep='\t', 
                header=None,
                # Используем только то количество колонок, сколько у нас валидных имен
                names=column_names,
                usecols=range(len(column_names)),
                on_bad_lines='skip'
            )

            time_col_name = column_names[0]

            def parse_rel_time(time_str):
                if not isinstance(time_str, str): return None
                try:
                    h, m, s, ms = map(int, time_str.split(':'))
                    return h * 3600 + m * 60 + s + ms / 1000.0
                except (ValueError, TypeError):
                    return None

            df[time_col_name] = df[time_col_name].apply(parse_rel_time)
            df.dropna(subset=[time_col_name], inplace=True)
            df.rename(columns={time_col_name: 'Time'}, inplace=True)
            
            return df
        
        except Exception as e:
            print(f"Ошибка при парсинге файла АЦП {file_path}: {e}")
            return pd.DataFrame()