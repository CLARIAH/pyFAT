import datetime
import platform
import sys
from logging.handlers import TimedRotatingFileHandler
from typing import Any

from dynaconf import Dynaconf
import logging

# from pyfip.fip.xpathhandler import XpathHandler

settings = Dynaconf(settings_files=["conf/settings.toml"], secrets=["conf/.secrets.toml"], environments=True, default_env="default", load_dotenv=True)

def setup_logging():
    for log in settings.LOGGERS:
        logfile_handler = logging.FileHandler(filename=log.get('log_file'), mode='a')
        logfile_handler.setLevel(log.get('log_level'))
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(log.get('log_format')))
        handlers = [logfile_handler, stdout_handler]
        logging.basicConfig(level=log.get('log_level'), format=log.get('log_format'), handlers=handlers, datefmt=log.get('log_date_format'))
        return logging.getLogger(log.get('name'))


# def get_handler_class(str_test: str) -> Any:
#     parts = str_test.split(':', 1)
#     if len(parts) == 2:
#         handler = parts[0]
#         if handler.upper() == 'XPATH':
#             return XpathHandler()
#         else:
#             raise ValueError(str_test)
#     raise ValueError(str_test)
