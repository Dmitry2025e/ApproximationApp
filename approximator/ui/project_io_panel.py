from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
import json

class ProjectIOPanel(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()
        self.save_btn = QPushButton('Сохранить проект')
        self.load_btn = QPushButton('Открыть проект')
        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_btn)
        self.setLayout(layout)
        self.save_btn.clicked.connect(self.save_project)
        self.load_btn.clicked.connect(self.load_project)

    def save_project(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить проект', '', 'JSON Files (*.json)')
        if not file_path:
            return
        state = self.main_window.state
        # Сериализация состояния
        data = {
            'channels': {},
            'segments': {},
            'settings': {
                'active_channel': state.active_channel_name,
                'selected_segment_index': state.selected_segment_index,
                'show_source_data': state.show_source_data,
                'show_approximation': state.show_approximation,
                'auto_recalculate': state.auto_recalculate
            }
        }
        for ch, ch_state in state.channel_states.items():
            data['channels'][ch] = ch_state.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, 'Сохранение', 'Проект успешно сохранён!')

    def load_project(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Открыть проект', '', 'JSON Files (*.json)')
        if not file_path:
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        state = self.main_window.state
        # Восстановление состояния
        state.active_channel_name = data['settings'].get('active_channel', '')
        state.selected_segment_index = data['settings'].get('selected_segment_index')
        state.show_source_data = data['settings'].get('show_source_data', True)
        state.show_approximation = data['settings'].get('show_approximation', True)
        state.auto_recalculate = data['settings'].get('auto_recalculate', True)
        # Восстановление каналов и сегментов
        from data_models.channel_state import ChannelState
        state.channel_states.clear()
        for ch, ch_data in data['channels'].items():
            state.channel_states[ch] = ChannelState.from_dict(ch_data)
        QMessageBox.information(self, 'Загрузка', 'Проект успешно загружен!')
