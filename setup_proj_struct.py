import os
from pathlib import Path

# Список всех файлов и пустых __init__.py для нашего проекта.
# Папки будут созданы автоматически на основе этих путей.
PROJECT_PATHS = [
    "main.py",
    "app/__init__.py",
    "app/main_window.py",
    "app/app_state.py",
    "app/project_manager.py",
    "data_models/__init__.py",
    "data_models/channel_state.py",
    "data_models/segment.py",
    "services/__init__.py",
    "services/data_loader.py",
    "services/data_merger.py",
    "services/data_exporter.py",
    "services/math/__init__.py",
    "services/math/fit_strategy.py",
    "services/math/standard_fitter.py",
    "services/math/smooth_fitter.py",
    "services/math/through_fitter.py",
    "file_parsers/__init__.py",
    "file_parsers/base_parser.py",
    "file_parsers/pyrometer_parser.py",
    "file_parsers/adc_parser.py",
    "file_parsers/generic_parser.py",
    "ui/__init__.py",
    "ui/plot_manager.py",
    "ui/event_handler.py",
    "ui/error_dialog.py",
    "ui/widgets/__init__.py",
    "ui/widgets/segment_table.py",
    "ui/tabs/__init__.py",
    "ui/tabs/import_tab.py",
    "ui/tabs/analysis_tab.py",
    "utils/__init__.py",
    "utils/constants.py",
]

# Имя корневой папки проекта
PROJECT_ROOT = "approximator"

def create_project_structure():
    """
    Создает всю структуру папок и пустых файлов для проекта.
    """
    root_path = Path(PROJECT_ROOT)
    
    if root_path.exists():
        print(f"Ошибка: Директория '{root_path}' уже существует. Удалите ее и попробуйте снова.")
        return

    print(f"Создание структуры проекта в папке '{root_path}'...")
    
    # Создаем корневую папку
    root_path.mkdir()
    
    for path_str in PROJECT_PATHS:
        # Формируем полный путь к файлу
        file_path = root_path / path_str
        
        # Создаем все родительские директории для этого файла, если их еще нет
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Создаем пустой файл
        file_path.touch()
        
        print(f"  ✓ Создан: {file_path}")
        
    print("\nСтруктура проекта успешно создана!")


if __name__ == "__main__":
    create_project_structure()