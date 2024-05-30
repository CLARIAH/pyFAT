import json
from importlib import resources

import yaml


class Preprocessor(object):
    # logger = logging.getLogger(__name__)
    # Class attributes
    _metrics_version = None
    _instance = None
    _settings = None
    _metrics_list: list = []
    _metrics_loc: str = None
    _metrics_total: int = 0
    _ns_map: dict = None

    def __new__(cls, settings):
        """Make it a singleton"""
        if cls._instance is None:
            cls._instance = super(Preprocessor, cls).__new__(cls)
            cls._settings = settings
        else:
            print('Preprocessor already exists')
        return cls._instance

    @classmethod
    def parse_metrics_yaml(cls):
        cls._metrics_loc = resources.files(cls._settings.METRICS_PCKG).joinpath(cls._settings.METRICS_FILE)
        with open(cls._metrics_loc, 'r') as file:
            metrics_specs = yaml.load(file, Loader=yaml.FullLoader)
            cls._metrics_list = metrics_specs['metrics']
            cls._metrics_total = len(cls._metrics_list)
            cls._metrics_version = metrics_specs['config']['metric_version']
            cls._metrics_created_by = metrics_specs['created_by']
            cls._metrics_ns = metrics_specs['config']['metric_namespaces']

    @classmethod
    def get_total_metrics(cls) -> int:
        return cls._metrics_total

    @classmethod
    def get_metrics_created_by(cls) -> str:
        return cls._metrics_created_by

    @classmethod
    def get_metrics_version(cls) -> str:
        return cls._metrics_version

    @classmethod
    def get_metrics(cls) -> list:
        return cls._metrics_list

    @classmethod
    def get_nspace_map(cls) -> dict:
        return cls._metrics_ns

