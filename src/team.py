import pandas as pd


class Team():

    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.elo = 0

    def set_name(self, name):
        self.name = name

    def asSeries(self):
        return pd.Series([self.name, self.elo], index=["name", "elo"])

    def __repr__(self):
        return f'{self.name}'
