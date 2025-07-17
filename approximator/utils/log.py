import logging

logging.getLogger('matplotlib').setLevel(logging.WARNING) # отключаем лог matplotlib


# 🔧 Инициализация логгера
logging.basicConfig(
    level=logging.DEBUG,  # Меняешь на INFO чтобы отключить debug-логи
    format='[%(levelname)s] %(message)s'
)

# 🎯 Экспортируем удобные короткие функции
def debug(msg: str):
    logging.debug(msg)

def info(msg: str):
    logging.info(msg)

def warn(msg: str):
    logging.warning(msg)

def error(msg: str):
    logging.error(msg)