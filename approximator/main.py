import sys, os, json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget
from app.main_window import MainWindow
from services.state_loader import load_project_state
from utils.log import debug, error


# ┌────────────────────────────────────────────┐
# │  🔧 Настройка окружения                    │
# └────────────────────────────────────────────┘
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

AUTOSAVE_PATH = os.path.join(project_root, "autosave.json")


# ┌────────────────────────────────────────────┐
# │  🚀 Запуск приложения                      │
# └────────────────────────────────────────────┘
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    clear_console()
    debug("[startup] ⏳ Инициализация QApplication и MainWindow")

    app = QApplication(sys.argv)
    window = MainWindow()
    debug("[startup] ✅ MainWindow создан, запускаем .show()")

    # 💾 Автосохранение
    def autosave():
        try:
            debug("[autosave] 💾 Попытка автосохранения перед выходом")
            if hasattr(window, 'analysis_tab') and hasattr(window.analysis_tab, '_save_project'):
                original = __import__('PyQt5.QtWidgets').QtWidgets.QFileDialog.getSaveFileName
                __import__('PyQt5.QtWidgets').QtWidgets.QFileDialog.getSaveFileName = lambda *a, **kw: (AUTOSAVE_PATH, '')
                window.analysis_tab._save_project()
                __import__('PyQt5.QtWidgets').QtWidgets.QFileDialog.getSaveFileName = original
        except Exception as e:
            error(f"[autosave] ❌ Ошибка автосохранения: {e}")

    app.aboutToQuit.connect(autosave)
    debug("[autosave] 🔗 Подключено к aboutToQuit")

    window.show()
    debug("[startup] 🚀 Окно отображено, продолжаем")

    # 🔄 Автозагрузка состояния
    if os.path.exists(AUTOSAVE_PATH):
        debug("[restore] 📂 autosave.json найден — загружаем")
        try:
            with open(AUTOSAVE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            debug("[restore] ✅ Файл загружен, передаём в state_loader")
            load_project_state(window, data)
        except Exception as e:
            error(f"[restore] ❌ Ошибка автозагрузки: {e}")
            QMessageBox.warning(window, f"'Автозагрузка', f'Ошибка автозагрузки состояния: {e}")

    # ┌────────────────────────────────────────────┐
    # │  🔁 Подключение восстановления в ImportTab │
    # └────────────────────────────────────────────┘

    def _handle_load_project_from_data(self, data):
        debug("[restore] 📥 Запущен импорт из _handle_load_project_from_data")

        main_window = self.parent()
        while main_window and not hasattr(main_window, 'import_event_handler'):
            main_window = main_window.parent()

        if main_window and hasattr(main_window, 'import_event_handler'):
            load_project_state(main_window, data)
        else:
            error("[restore] ❌ main_window не найден или не содержит import_event_handler")

    QWidget._handle_load_project_from_data = _handle_load_project_from_data
    debug("[main] ✅ Метод _handle_load_project_from_data навешан на QWidget")

    sys.exit(app.exec_())   # тут выход из приложения!!




# 🔰 Точка входа
if __name__ == '__main__':
    main()