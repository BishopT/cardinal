import pandas as pd
import team


class Player():

    def __init__(self, name):
        self.__init__(name, None)

    def __init__(self, name, elo):
        self.id = None
        self.name = name
        self.elo = elo
        self.team = None

    def set_id(self, id):
        self.id = id

    def set_team(self, team):
        self.team = team

    def asSeries(self):
        return pd.Series(
            [self.name, self.elo, self.team],
            index=["name", "elo", "team"]
        )
