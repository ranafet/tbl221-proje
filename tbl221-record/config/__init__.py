import tomllib

class Config:
    def __init__(self, config_path: str, record_period: int):
        self.config_path = config_path
        self.record_period = record_period
        self.load_config()

    def load_config(self):
        with open(self.config_path, "rb") as f:
            self.config = tomllib.load(f)

    def get(self, key):
        return self.config.get(key)

    def __getitem__(self, key):
        return self.get(key)
