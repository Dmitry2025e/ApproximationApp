from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout
from PyQt5.QtCore import Qt

class ExportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        # Настройки времени
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel('Шаг по времени (сек):'))
        self.time_step_spin = QDoubleSpinBox()
        self.time_step_spin.setDecimals(3)
        self.time_step_spin.setMinimum(0.001)
        self.time_step_spin.setMaximum(10000)
        self.time_step_spin.setValue(1.0)
        time_layout.addWidget(self.time_step_spin)
        layout.addLayout(time_layout)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel('Начальная точка:'))
        self.start_point_spin = QDoubleSpinBox()
        self.start_point_spin.setDecimals(3)
        self.start_point_spin.setMinimum(0.0)
        self.start_point_spin.setMaximum(10000)
        self.start_point_spin.setValue(0.0)
        start_layout.addWidget(self.start_point_spin)
        layout.addLayout(start_layout)


        # Варианты экспорта
        self.export_mode_combo = QComboBox()
        self.export_mode_combo.addItems([
            'Экспортировать с заданным числом точек на весь диапазон',
            'Указать число точек на каждом сегменте'
        ])
        layout.addWidget(QLabel('Вариант экспорта:'))
        layout.addWidget(self.export_mode_combo)

        # --- Новый блок: режим сшивки и метод ---
        self.stitch_checkbox = QCheckBox("Плавная сшивка")
        self.stitch_checkbox.setChecked(False)
        self.stitch_method_combo = QComboBox()
        self.stitch_method_combo.addItems([
            "C0 (по значению)",
            "C1 (значение+производная)",
            "C2 (значение+1-я+2-я производная)"
        ])
        self.stitch_method_combo.setCurrentIndex(1)
        self.stitch_method_combo.setEnabled(False)
        self.stitch_checkbox.stateChanged.connect(lambda state: self.stitch_method_combo.setEnabled(state == 2))
        stitch_layout = QHBoxLayout()
        stitch_layout.addWidget(self.stitch_checkbox)
        stitch_layout.addWidget(self.stitch_method_combo)
        layout.addLayout(stitch_layout)

        # Общее число точек (только для первого варианта)
        total_points_layout = QHBoxLayout()
        total_points_layout.addWidget(QLabel('Общее число точек:'))
        self.total_points_spin = QSpinBox()
        self.total_points_spin.setMinimum(2)
        self.total_points_spin.setMaximum(1000000)
        self.total_points_spin.setValue(500)
        total_points_layout.addWidget(self.total_points_spin)
        layout.addLayout(total_points_layout)

        # Конечная точка (по умолчанию максимальная из данных)
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel('Конечная точка:'))
        self.end_point_spin = QDoubleSpinBox()
        self.end_point_spin.setDecimals(3)
        self.end_point_spin.setMinimum(0.0)
        self.end_point_spin.setMaximum(100000)
        self.end_point_spin.setValue(0.0)  # будет обновлено при первом экспорте
        end_layout.addWidget(self.end_point_spin)
        layout.addLayout(end_layout)

        # --- Автообновление конечной точки по данным ---
        def update_end_point_from_data():
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'state'):
                main_window = main_window.parent()
            if not main_window:
                return
            df = getattr(main_window.state, 'merged_dataframe', None)
            if df is not None and not df.empty:
                time_col = None
                for col in df.columns:
                    if col.lower() == 'time':
                        time_col = col
                        break
                if not time_col:
                    time_col = df.columns[0]
                max_val = df[time_col].max()
                self.end_point_spin.setValue(float(max_val))

        self.update_end_point_from_data = update_end_point_from_data
        self.update_end_point_from_data()

        # Скрываем поля по умолчанию
        self.total_points_spin.setVisible(True)
        for w in total_points_layout.children():
            if hasattr(w, 'setVisible'): w.setVisible(True)
        self.end_point_spin.setVisible(True)
        for w in end_layout.children():
            if hasattr(w, 'setVisible'): w.setVisible(True)

        def update_export_mode_fields():
            is_range = self.export_mode_combo.currentIndex() == 0
            self.total_points_spin.setVisible(is_range)
            for w in total_points_layout.children():
                if hasattr(w, 'setVisible'): w.setVisible(is_range)
            self.end_point_spin.setVisible(is_range)
            for w in end_layout.children():
                if hasattr(w, 'setVisible'): w.setVisible(is_range)
        self.export_mode_combo.currentIndexChanged.connect(update_export_mode_fields)
        update_export_mode_fields()

        # Таблица для каналов и точек
        self.channel_table = QTableWidget(0, 3)
        self.channel_table.setHorizontalHeaderLabels(['Название', 'Число точек', 'Стиль линии'])
        layout.addWidget(QLabel('Настройка каналов и точек на сегмент:'))
        layout.addWidget(self.channel_table)

        # Кнопка экспорта
        self.export_btn = QPushButton('Экспортировать в Excel')
        layout.addWidget(self.export_btn)
        self.export_btn.clicked.connect(self.export_to_excel)

        # Кнопка для сохранения состояния в JSON
        self.save_state_btn = QPushButton('Сохранить состояние (JSON)')
        layout.addWidget(self.save_state_btn)
        self.save_state_btn.clicked.connect(self.save_state_to_json)

        # Кнопка для восстановления состояния из JSON
        self.load_state_btn = QPushButton('Восстановить состояние (JSON)')
        layout.addWidget(self.load_state_btn)
        self.load_state_btn.clicked.connect(self.load_state_from_json)

        self.setLayout(layout)
        self.channel_table.itemChanged.connect(self.on_channel_table_item_changed)
        self.refresh_channel_table()

    def refresh_channel_table(self):
        """
        Заполняет таблицу каналов с editable display_name и стилем линии.
        """
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'state'):
            main_window = main_window.parent()
        if not main_window:
            return
        channel_states = main_window.state.channel_states
        self.channel_table.setRowCount(len(channel_states))
        line_styles = ['-', '--', '-.', ':']
        for row, (ch_name, ch_state) in enumerate(channel_states.items()):
            # Название (editable)
            display_name = ch_state.display_name if ch_state.display_name else ch_name
            name_item = QTableWidgetItem(display_name)
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            self.channel_table.setItem(row, 0, name_item)
            # Число точек
            self.channel_table.setItem(row, 1, QTableWidgetItem(str(100)))
            # Стиль линии (editable combo)
            style_combo = QComboBox(); style_combo.addItems(line_styles)
            style_combo.setCurrentText(ch_state.line_style)
            def on_style_change(idx, st=ch_state, combo=style_combo):
                st.line_style = combo.currentText()
            style_combo.currentIndexChanged.connect(on_style_change)
            self.channel_table.setCellWidget(row, 2, style_combo)

    def on_channel_table_item_changed(self, item):
        # Сохраняем новое название канала в display_name
        row, col = item.row(), item.column()
        if col == 0:
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'state'):
                main_window = main_window.parent()
            if not main_window:
                return
            channel_states = list(main_window.state.channel_states.values())
            if row < len(channel_states):
                channel_states[row].display_name = item.text().strip()

    def save_state_to_json(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import json
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'state'):
            main_window = main_window.parent()
        if not main_window:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось получить состояние приложения.')
            return
        app_state = main_window.state
        # Сохраняем всё состояние каналов, сегментов, масок и т.д.
        # Получаем список файлов из вкладки Импорт
        imported_files = []
        if hasattr(main_window, 'import_tab') and hasattr(main_window.import_tab, 'file_list_widget'):
            imported_files = [main_window.import_tab.file_list_widget.item(i).text() for i in range(main_window.import_tab.file_list_widget.count())]
        data = {
            'channels': {ch: ch_state.to_dict() for ch, ch_state in app_state.channel_states.items()},
            'settings': {
                'active_channel': app_state.active_channel_name,
                'selected_segment_index': app_state.selected_segment_index,
                'show_source_data': app_state.show_source_data,
                'show_approximation': app_state.show_approximation,
                'auto_recalculate': app_state.auto_recalculate,
                'stitch_enabled': self.stitch_checkbox.isChecked(),
                'stitch_method': self.stitch_method_combo.currentIndex(),
                'export_mode': self.export_mode_combo.currentIndex(),
                'total_points': self.total_points_spin.value(),
                'start_point': self.start_point_spin.value(),
                'end_point': self.end_point_spin.value()
            },
            'imported_files': imported_files
        }
        file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить состояние', '', 'JSON Files (*.json)')
        if not file_path:
            return
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, 'Сохранение', 'Состояние успешно сохранено!')

    def load_state_from_json(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import json
        from data_models.channel_state import ChannelState
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'state'):
            main_window = main_window.parent()
        if not main_window:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось получить состояние приложения.')
            return
        app_state = main_window.state
        file_path, _ = QFileDialog.getOpenFileName(self, 'Открыть состояние', '', 'JSON Files (*.json)')
        if not file_path:
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Восстанавливаем каналы
        app_state.channel_states.clear()
        for ch, ch_data in data.get('channels', {}).items():
            app_state.channel_states[ch] = ChannelState.from_dict(ch_data)
        # Восстанавливаем настройки
        settings = data.get('settings', {})
        app_state.active_channel_name = settings.get('active_channel', '')
        app_state.selected_segment_index = settings.get('selected_segment_index')
        app_state.show_source_data = settings.get('show_source_data', True)
        app_state.show_approximation = settings.get('show_approximation', True)
        app_state.auto_recalculate = settings.get('auto_recalculate', True)
        # Восстанавливаем режим сшивки и метод
        self.stitch_checkbox.setChecked(settings.get('stitch_enabled', False))
        self.stitch_method_combo.setCurrentIndex(settings.get('stitch_method', 1))
        # Восстанавливаем вариант экспорта
        self.export_mode_combo.setCurrentIndex(settings.get('export_mode', 0))
        # Восстанавливаем параметры диапазона
        self.total_points_spin.setValue(settings.get('total_points', 500))
        self.start_point_spin.setValue(settings.get('start_point', 0.0))
        self.end_point_spin.setValue(settings.get('end_point', 0.0))
        # Обновить конечную точку по данным, если нужно
        self.update_end_point_from_data()
        # Восстанавливаем список импортированных файлов на вкладке Импорт
        imported_files = data.get('imported_files', [])
        if hasattr(main_window, 'import_tab') and hasattr(main_window.import_tab, 'file_list_widget'):
            main_window.import_tab.file_list_widget.clear()
            for f in imported_files:
                main_window.import_tab.file_list_widget.addItem(f)
        QMessageBox.information(self, 'Восстановление', 'Состояние успешно восстановлено!')
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        # Настройки времени
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel('Шаг по времени (сек):'))
        self.time_step_spin = QDoubleSpinBox()
        self.time_step_spin.setDecimals(3)
        self.time_step_spin.setMinimum(0.001)
        self.time_step_spin.setMaximum(10000)
        self.time_step_spin.setValue(1.0)
        time_layout.addWidget(self.time_step_spin)
        layout.addLayout(time_layout)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel('Начальная точка:'))
        self.start_point_spin = QDoubleSpinBox()
        self.start_point_spin.setDecimals(3)
        self.start_point_spin.setMinimum(0.0)
        self.start_point_spin.setMaximum(10000)
        self.start_point_spin.setValue(0.0)
        start_layout.addWidget(self.start_point_spin)
        layout.addLayout(start_layout)

        # Варианты экспорта
        self.export_mode_combo = QComboBox()
        self.export_mode_combo.addItems([
            'Экспортировать с заданным числом точек на весь диапазон',
            'Указать число точек на каждом сегменте'
        ])
        layout.addWidget(QLabel('Вариант экспорта:'))
        layout.addWidget(self.export_mode_combo)

        # Таблица для каналов и точек
        self.channel_table = QTableWidget(0, 3)
        self.channel_table.setHorizontalHeaderLabels(['Канал', 'Число точек', 'Толщина линии'])
        layout.addWidget(QLabel('Настройка каналов и точек на сегмент:'))
        layout.addWidget(self.channel_table)

        # Кнопка экспорта
        self.export_btn = QPushButton('Экспортировать в Excel')
        layout.addWidget(self.export_btn)

        self.setLayout(layout)

        # Обработчик кнопки экспорта

        self.export_btn.clicked.connect(self.export_to_excel)

    def export_to_excel(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import pandas as pd
        import numpy as np
        from data_models.data_structures import Segment

        # Получаем путь для сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить файл', '', 'Excel Files (*.xlsx)')
        if not file_path:
            return

        # Получаем состояние приложения через MainWindow
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'state'):
            main_window = main_window.parent()
        if not main_window:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось получить состояние приложения.')
            return
        app_state = main_window.state
        df = app_state.merged_dataframe.copy()
        channel_states = app_state.channel_states
        time_col = None
        # Определяем столбец времени
        for col in df.columns:
            if col.lower().startswith('time') or col.lower() == 't':
                time_col = col
                break
        if time_col is None:
            time_col = df.columns[0]

        # Получаем выбранные каналы (или все)
        channels = [self.channel_table.item(row, 0).text() for row in range(self.channel_table.rowCount())]
        if not channels:
            channels = list(channel_states.keys())

        # Получаем параметры экспорта
        time_step = self.time_step_spin.value()
        start_point = self.start_point_spin.value()
        mode = self.export_mode_combo.currentIndex()
        total_points = self.total_points_spin.value()
        end_point = self.end_point_spin.value()
        points_per_channel = {}
        for row in range(self.channel_table.rowCount()):
            ch = self.channel_table.item(row, 0).text()
            try:
                n = int(self.channel_table.item(row, 1).text())
            except Exception:
                n = 100
            points_per_channel[ch] = n

        # Если выбран режим "на весь диапазон" — обновляем конечную точку по данным
        if mode == 0:
            # Определяем максимальную точку по всем каналам
            max_x = None
            for ch in channels:
                ch_data = df[time_col] if ch not in df.columns else df[ch]
                ch_max = ch_data.max()
                if max_x is None or ch_max > max_x:
                    max_x = ch_max
            if max_x is not None:
                self.end_point_spin.setValue(float(max_x))
            end_point = self.end_point_spin.value()

        # Формируем лист с исходными данными
        orig_data = df[[time_col] + channels].copy()
        orig_data['t_abs'] = orig_data[time_col]
        orig_data['t_rel'] = orig_data[time_col] - start_point
        cols = ['t_abs', 't_rel'] + channels
        orig_data = orig_data[cols]

        # Формируем лист с масками (исключёнными интервалами/индексами)
        mask_rows = []
        for ch in channels:
            ch_state = channel_states[ch]
            if ch_state.excluded_indices:
                mask_rows.append({'Канал': ch, 'Исключённые индексы': ', '.join(map(str, sorted(ch_state.excluded_indices)))})
            else:
                mask_rows.append({'Канал': ch, 'Исключённые индексы': ''})
        mask_df = pd.DataFrame(mask_rows)

        # Формируем лист с аппроксимацией и статистикой
        approx_rows = []
        for ch in channels:
            ch_state = channel_states[ch]
            for seg in ch_state.segments:
                if seg.is_excluded or not seg.fit_result:
                    continue
                # Вычисляем точки для экспорта
                if mode == 0:
                    # Для всего диапазона: равномерно по диапазону сегментов канала
                    x_min = min(s.x_start for s in ch_state.segments if not s.is_excluded)
                    x_max = end_point
                    x_vals = np.linspace(x_min, x_max, total_points)
                else:
                    n_points = points_per_channel.get(ch, 100)
                    x_vals = np.linspace(seg.x_start, seg.x_end, n_points)
                y_vals = np.polyval(seg.fit_result.coefficients, x_vals)
                for i, (x, y) in enumerate(zip(x_vals, y_vals)):
                    approx_rows.append({
                        'Канал': ch,
                        'Сегмент': seg.label,
                        't_abs': x,
                        't_rel': x - start_point,
                        'Значение': y,
                        'Степень': seg.poly_degree,
                        'RMSE': seg.fit_result.rmse,
                        'R2': seg.fit_result.r_squared,
                        'Коэффициенты': str(seg.fit_result.coefficients),
                        'Число точек': seg.fit_result.points_count
                    })

        approx_df = pd.DataFrame(approx_rows)

        # Лист с настройками экспорта
        settings = {
            'Шаг по времени': time_step,
            'Начальная точка': start_point,
            'Режим': self.export_mode_combo.currentText(),
            'Каналы': ', '.join(channels)
        }
        settings_df = pd.DataFrame(list(settings.items()), columns=['Параметр', 'Значение'])

        # Сохраняем в Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            orig_data.to_excel(writer, sheet_name='Исходные данные', index=False)
            approx_df.to_excel(writer, sheet_name='Аппроксимация', index=False)
            mask_df.to_excel(writer, sheet_name='Маски', index=False)
            settings_df.to_excel(writer, sheet_name='Настройки', index=False)

        QMessageBox.information(self, 'Экспорт завершён', f'Данные успешно экспортированы в {file_path}')
