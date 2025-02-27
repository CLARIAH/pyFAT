import json
from importlib import resources
import yaml
from typing import List, Dict

class Preprocessor:
    # Class attributes
    _instance = None

    def __new__(cls, settings):
        """Implement the singleton pattern"""
        if cls._instance is None:
            cls._instance = super(Preprocessor, cls).__new__(cls)
            cls._initialize(settings)
        else:
            print('Preprocessor already exists')
        return cls._instance

    @classmethod
    def _initialize(cls, settings):
        """Initialize the singleton instance"""
        cls._settings = settings
        cls._metrics_version = None
        cls._metrics_list = []
        cls._metrics_loc = None
        cls._metrics_total = 0
        cls._metrics_ns = None
        cls._metrics_created_by = None

    @classmethod
    def parse_metrics_yaml(cls):
        """Parse the YAML file containing metrics"""
        # cls._metrics_loc = resources.files(cls._settings.METRICS_PCKG).joinpath(cls._settings.METRICS_FILE)
        cls._metrics_loc = cls._settings.METRICS_FILE
        with open(cls._metrics_loc, 'r') as file:
            metrics_specs = yaml.load(file, Loader=yaml.FullLoader)
            cls._metrics_list = metrics_specs['metrics']
            cls._metrics_total = len(cls._metrics_list)
            cls._metrics_version = metrics_specs['config']['metric_version']
            cls._metrics_created_by = metrics_specs['created_by']
            cls._metrics_ns = metrics_specs['config']['metric_namespaces']

    @classmethod
    def get_total_metrics(cls) -> int:
        """Get the total number of metrics"""
        return cls._metrics_total

    @classmethod
    def get_metrics_created_by(cls) -> str:
        """Get the creator of the metrics"""
        return cls._metrics_created_by

    @classmethod
    def get_metrics_version(cls) -> str:
        """Get the version of the metrics"""
        return cls._metrics_version

    @classmethod
    def get_metrics(cls) -> List[dict]:
        """Get the list of metrics"""
        return cls._metrics_list

    @classmethod
    def get_nspace_map(cls) -> Dict[str, str]:
        """Get the namespace map of the metrics"""
        return cls._metrics_ns
