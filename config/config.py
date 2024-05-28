import os
from dotenv import load_dotenv
import yaml
from typing import Any, Dict

class NestedConfig:
    def __init__(self, data: Dict[str, Any]):
        for key, value in data.items():
            if isinstance(value, dict):
                value = NestedConfig(value)
            setattr(self, key, value)

    def to_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, NestedConfig):
                value = value.to_dict()
            result[key] = value
        return result


class Config:
    def __init__(self, config_file: str):
        with open(config_file, "r") as file:
            self._config = yaml.safe_load(file)
        self._nested_config = NestedConfig(self._config)

    def __getattr__(self, item):
        return getattr(self._nested_config, item)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        for k in keys:
            value = value.get(k)
            if value is None:
                return default
        return value


# Load the configuration when the module is imported
config = Config("config/config.yaml")