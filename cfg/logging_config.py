import os
import logging
from logging import basicConfig, getLogger
from logging import DEBUG, INFO
from logging import error, warning, debug, info, critical
from logging import FileHandler, StreamHandler


CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho para o diretório de logs, relativo à raiz do projeto
ROOT_DIR = os.path.join(CONFIG_DIR, '..',)

class LoggingConfig:

    @staticmethod
    def default_setup_logging(file_handler_path, file_handler_mode, loggin_level=INFO):

        LOG_FILE_PATH = os.path.join(ROOT_DIR, file_handler_path)

        basicConfig(
            level=loggin_level,
            encoding='utf-8',
            format='%(asctime)s - [%(levelname)s]: - Executando arquivo: %(filename)s - LOG: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                FileHandler(LOG_FILE_PATH, file_handler_mode),
                StreamHandler()
            ],
        )

    @staticmethod
    def get_logger(logger__name__):

        logger = getLogger(logger__name__)

        return logger


if __name__ == '__main__':
    logger = getLogger()