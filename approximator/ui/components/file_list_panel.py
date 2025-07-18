# Путь: ui/components/file_list_panel.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget
)
from PyQt5.QtCore import Qt


class FileListPanel(QWidget):
    """
    Компонент для управления списком файлов:
    - Добавление, удаление, очистка
    - Отображение списка
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Виджеты ---
        self.add_button = QPushButton("1. Добавить файлы...")
        self.preview_button = QPushButton("2. Показать в таблице")
        self.remove_button = QPushButton("Удалить выбранный")
        self.reset_button = QPushButton("Очистить все")

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)

        # --- Компоновка ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.add_button)
        layout.addWidget(self.preview_button)
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)

    # --- API ---

    def set_files(self, file_paths: list[str]):
        """Установить список файлов."""
        self.list_widget.clear()
        self.list_widget.addItems(file_paths)

    def get_selected_files(self) -> list[str]:
        """Получить список всех файлов в списке."""
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def get_current_selection(self) -> list[str]:
        """Получить выбранные пользователем файлы."""
        return [item.text() for item in self.list_widget.selectedItems()]

    def clear(self):
        """Очистить список файлов."""
        self.list_widget.clear()