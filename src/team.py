import pandas as pd


class Team():

    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.elo = 0

    def set_name(self, name):
        self.name = name

    def asDataFrame(self):
        return pd.DataFrame({
            "name": [self.name],
            "elo": [self.elo],
        })
