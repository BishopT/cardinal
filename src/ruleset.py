import math
import time
from abc import ABC, abstractmethod
from typing import List

import pandas as pd

from model import Match, Team


class RuleSet(ABC):

    def __init__(self, name, size):
        self.name = name
        self.pool: list[Team] = []
        self.poolsize_max = size
        self.match_history: list[Match] = []
        self.bracket = {}
        self.match_queue: list[str] = []
        self.running = False

    def add_team(self, team):
        self.pool.append(team)

    def get_teams(self):
        return self.pool

    def get_match(self, id: str) -> Match:
        return self.bracket[id]

    def get_history(self, team):
        d = {}
        for i in len(self.match_history):
            d[f'{i}'] = pd.Series(self.match_history[i].get_result(), index=[
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
    def get_bracket(self):
        pass

    @abstractmethod
    def report_match_result(self, match: Match, *games_score: tuple):
        pass


class SimpleElimination(RuleSet):

    def next_match(self, team):
        for m in list(map(self.get_match, self.match_queue)):
            # m = self.get_match(m_id)
            if (team == m.blue_team or team == m.red_team):
                return m
        return None

    def start(self):
        self.running = True
        # while (self.running):
        #     time.sleep(2)

        #     for m in list(map(self.get_match, self.match_queue)):
        #         # m = self.bracket[m_id]
        #         if (m.get_winner() != None):
        #             self.match_queue.remove(m)
        #             self.match_history.append(m)

    def get_bracket(self) -> pd.DataFrame:
        return pd.DataFrame(self.bracket, index=["matches"]).T.sort_index(ascending=False)

    def get_standings(self) -> pd.DataFrame:
        pass

    def report_match_result(self, match: Match, *games_score: tuple):
        if (self.running):
            for gs in games_score:
                blue_score, red_score = gs
                match.add_game_result(blue_score, red_score)
                match.compute_bo()
                # print(f'match.ended={match.ended}')
            if (match.ended):
                winner = match.get_winner()
                # print(f'winner={winner}')
                replace = f'winner({match.id})'
                # print(f'replace={replace}')
                next_match = self.next_match(replace)
                nid = next_match.id
                nblue = next_match.blue_team
                # print(f'nblue={nblue}')
                nred = next_match.red_team
                if replace == nblue:
                    self.bracket[nid] = Match(
                        nid, next_match.bo, winner, nred)
                elif replace == nred:
                    self.bracket[nid] = Match(
                        nid, next_match.bo, nblue, winner)
                else:
                    raise Exception(f"Cannot program next match for {winner}")
                # print(f'next_match={self.bracket[nid]}')
        else:
            raise Exception('Cannot report match. phase not started')

    def init_bracket(self, bo) -> dict:
        no_of_teams = len(self.pool)
        print(f'pool={self.pool}, {no_of_teams} teams')

        bracket_depth = int(math.ceil(math.log(no_of_teams, 2)))
        self.bracket = {}
        for round in range(bracket_depth):
            matches_count = int(math.pow(2, (round)))
            teams_in_round = matches_count * 2
            for i in range(matches_count):
                match_id = f'{round}-{i+1}'
                if round != bracket_depth - 1:
                    blue_team = f'winner({(round + 1)}-{i + 1})'
                    red_team = f'winner({(round + 1)}-{teams_in_round - i})'
                else:  # "first" round to be played, we know the teams
                    blue_seed = i+1
                    blue_team = self.pool[blue_seed-1].name
                    red_seed = teams_in_round-i
                    try:
                        red_team = self.pool[red_seed-1].name
                    except:
                        red_team = 'forfeit'
                self.match_queue.append(match_id)
                self.bracket[match_id] = Match(
                    match_id, bo, blue_team, red_team)

        return self.bracket
