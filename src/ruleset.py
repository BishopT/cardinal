from abc import ABC, abstractmethod
from typing import List
import pandas as pd

import match
import team


class RuleSet(ABC):

    def __init__(self, size):
        self.pool: List[team.Team] = []
        self.poolsize_max = size
        self.matches: list[match.Match] = []
        self.bracket = {}

    def add_team(self, team):
        self.pool.append(team)

    def get_teams(self):
        return self.pool

    def get_history(self, team):
        d = {}
        for i in len(self.matches):
            d[f'{i}'] = pd.Series(self.matches[i].get_result(), index=[
                                  "blue team", "blue score",
                                  "red team", "red score",
                                  "winner"])
        return pd.DataFrame(d)

    @abstractmethod
    def next_match(self, team):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def get_standings(self):
        pass

    @abstractmethod
    def init_bracket(self):
        pass

    @abstractmethod
    def report_match_result(self, match_id, blue_score, red_score):
        pass
