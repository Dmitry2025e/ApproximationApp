# Путь: app/app_state.py

import pandas as pd
from typing import Dict, List, Any, Optional

from data_models.channel_state import ChannelState
from data_models.data_structures import Segment  # Импортируем тип Segment

class AppState:
    """
    Хранит все состояние приложения, не связанное с UI.
    """
    def __init__(self):
        # Состояние вкладки "Импорт"
        self.loaded_dataframes: Dict[str, pd.DataFrame] = {}
        
        # Состояние вкладки "Анализ"
        self.merged_dataframe: pd.DataFrame = pd.DataFrame()
        self.channel_states: Dict[str, ChannelState] = {}
        self.channel_list: List[str] = []
        self.segments: List[Segment] = []  # Список сегментов для анализа
        self.active_channel_name: str = ""
        self.selected_segment_index: Optional[int] = None
        
        # Флаги для управления видимостью и поведением
        self.show_source_data: bool = True
        self.show_approximation: bool = True
        self.auto_recalculate: bool = True

        # Состояние для перетаскивания границ
        self.dragged_boundary_index: Optional[int] = None
        self.dragged_line: Optional[Any] = None