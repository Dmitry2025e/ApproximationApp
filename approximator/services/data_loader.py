# Путь: approximator/services/data_loader.py

import pandas as pd
from typing import List
from file_parsers.base_parser import BaseParser

class DataLoader:
    """
    Сервис для загрузки данных, который автоматически определяет
    нужный парсер для каждого файла.
    """
    def __init__(self, parsers: List[BaseParser]):
        """
        :param parsers: Список экземпляров всех доступных парсеров.
                        Порядок важен: GenericCsvParser должен быть последним.
        """
        self.parsers = parsers

    def load_file(self, file_path: str) -> pd.DataFrame:
        print(f"Загрузка файла: {file_path}")
        for parser in self.parsers:
            if parser.can_parse(file_path):
                print(f"  -> Используется парсер: {parser.__class__.__name__}")
                return parser.parse(file_path)
        
        print(f"  -> Ошибка: Не найден подходящий парсер для файла {file_path}")
        return pd.DataFrame()