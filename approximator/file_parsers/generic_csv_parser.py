# Путь: file_parsers/generic_csv_parser.py

import pandas as pd
from pathlib import Path
from .base_parser import BaseParser

class GenericCsvParser(BaseParser):
    """
    Универсальный парсер для CSV и текстовых файлов.
    Пытается определить разделитель автоматически.
    """
    
    def can_parse(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in ['.csv', '.txt', '.dat']
        
    def parse(self, file_path: str) -> pd.DataFrame:
        try:
            # Пробуем разные разделители
            for sep in [',', ';', '\t', ' ']:
                try:
                    df = pd.read_csv(file_path, sep=sep)
                    if len(df.columns) > 1:  # Если получилось разделить на колонки
                        print(f"[GenericCsvParser] Successfully parsed with separator '{sep}'")
                        return df
                except Exception:
                    continue
                    
            print("[GenericCsvParser] Failed to parse with any known separator")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"[GenericCsvParser] Error during parsing: {e}")
            return pd.DataFrame()
