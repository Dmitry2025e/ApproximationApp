# Путь: interactive_approximator/file_parsers/generic_parser.py
import pandas as pd
from .base_parser import BaseParser

class GenericCsvParser(BaseParser):
    """
    Парсер для стандартных CSV файлов. Является "запасным вариантом".
    """
    def can_parse(self, file_path: str) -> bool:
        # Этот парсер может попытаться обработать любой файл, поэтому он всегда
        # возвращает True и должен быть последним в списке проверки.
        return True

    def parse(self, file_path: str) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path, sep=';', decimal=',', encoding='utf-8')
        except Exception:
            try:
                # Вторая попытка с другими популярными разделителями
                return pd.read_csv(file_path, sep=',', decimal='.', encoding='utf-8')
            except Exception as e:
                print(f"Ошибка при парсинге файла {file_path} как Generic CSV: {e}")
                return pd.DataFrame()