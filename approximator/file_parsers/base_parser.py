# Путь: interactive_approximator/file_parsers/base_parser.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseParser(ABC):
    """
    Абстрактный базовый класс для всех парсеров файлов.
    Определяет общий интерфейс, которому должны следовать все парсеры.
    """

    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        Проверяет, может ли этот парсер обработать данный файл.
        Обычно это проверка по заголовку или ключевому слову в файле.

        :param file_path: Путь к файлу.
        :return: True, если парсер подходит, иначе False.
        """
        pass

    @abstractmethod
    def parse(self, file_path: str) -> pd.DataFrame:
        """
        Загружает данные из файла в DataFrame.

        :param file_path: Путь к файлу.
        :return: DataFrame с данными или пустой DataFrame в случае ошибки.
        """
        pass