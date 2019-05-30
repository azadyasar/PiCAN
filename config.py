"""
Initialize with a YAML config filepath. Parses and returns
the config YAML file as a dict object

"""

import yaml

class Config:

    def __init__(self, filename):
        self.filename = filename
        
    def set_filename(self, filename):
        self.filename = filename
    
    def read_config(self):
        with open(self.filename, "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print("Exception occured while parsing config file", exc)
                return None

        
        
