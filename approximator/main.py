import sys, os, json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget
from app.main_window import MainWindow
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

    # 💾 Автосохранение при выходе
    def autosave():
        try:
            debug("[autosave] 💾 Попытка автосохранения перед выходом")
            window.project_controller.save_project(AUTOSAVE_PATH)
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
            debug("[restore] ✅ Файл загружен, передаём в ProjectStateController")
            window.project_controller.load_project_from_dict(data)
        except Exception as e:
            error(f"[restore] ❌ Ошибка автозагрузки: {e}")
            QMessageBox.warning(window, "Автозагрузка", f"Ошибка автозагрузки состояния: {e}")

    # 🔁 Подключение восстановления в ImportTab (если нужно)
    def _handle_load_project_from_data(self, data):
        debug("[restore] 📥 Запущен импорт из _handle_load_project_from_data")
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'project_controller'):
            main_window = main_window.parent()
        if main_window and hasattr(main_window, 'project_controller'):
            main_window.project_controller.load_project_from_dict(data)
        else:
            error("[restore] ❌ main_window не найден или не содержит project_controller")

    QWidget._handle_load_project_from_data = _handle_load_project_from_data
    debug("[main] ✅ Метод _handle_load_project_from_data навешан на QWidget")

    sys.exit(app.exec_())


# 🔰 Точка входа
if __name__ == '__main__':
    main()