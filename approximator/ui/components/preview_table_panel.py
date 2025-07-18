# Путь: ui/components/preview_table_panel.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
import pandas as pd


class PreviewTablePanel(QWidget):
    """
    Компонент для отображения DataFrame в виде таблицы.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table = QTableWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)

    def set_dataframe(self, df: pd.DataFrame):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns.astype(str))
        self.table.setRowCount(len(df.index))
        df_str = df.astype(str)
        for i, row in enumerate(df_str.itertuples(index=False)):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def clear(self):
        self.table.clearContents()
        self.table.setRowCount(0)