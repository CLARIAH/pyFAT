import os
import sys
import pyfat
import logging

from dynaconf import Dynaconf
module_path = os.path.dirname(pyfat.__file__)

# TODO: now reads the conf from pyfat/conf/settings.toml; it should check for external conf and fall back to the default
settings = Dynaconf(settings_files=[os.path.join(module_path, "conf/settings.toml")],
                    secrets=[os.path.join(module_path, "conf/.secrets.toml")],
                    environments=True, default_env="default", load_dotenv=True)


def setup_logging():
    for log in settings.LOGGERS:
        # logfile_handler = logging.FileHandler(filename=log.get('log_file'), mode='a')
        # logfile_handler.setLevel(log.get('log_level'))
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(log.get('log_format')))
        # handlers = [logfile_handler, stdout_handler]
        handlers = [stdout_handler]
        logging.basicConfig(level=log.get('log_level'), format=log.get('log_format'), handlers=handlers, datefmt=log.get('log_date_format'))
        return logging.getLogger(log.get('name'))
