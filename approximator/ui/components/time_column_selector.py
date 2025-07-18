# Путь: ui/components/time_column_selector.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox

class TimeColumnSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.combo = QComboBox()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("3. Выберите общую колонку времени:"))
        layout.addWidget(self.combo)

    def set_columns(self, columns: list[str]):
        self.combo.clear()
        self.combo.addItems(columns)

    def get_selected(self) -> str:
        return self.combo.currentText()


    def on_change(self, callback):
        self.combo.currentIndexChanged.connect(callback)

    def set_selected(self, column_name: str):
        idx = self.combo.findText(column_name)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)

            # ✅ Синхронизация с AppState
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'state'):
                main_window = main_window.parent()
            if main_window and hasattr(main_window, 'state'):
                main_window.state.time_column = column_name
                print(f"[TimeSelector] ✅ Синхронизировано: time_column = '{column_name}'")