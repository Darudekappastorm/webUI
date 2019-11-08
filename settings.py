import logging


def init():
    global machinekit_running
    global controller
    global file_queue
    global logger
    machinekit_running = False
    controller = None
    file_queue = []

    logger = logging.getLogger(__name__)
    f_handler = logging.FileHandler('app.log')
    f_handler.setLevel(logging.ERROR)

    f_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)