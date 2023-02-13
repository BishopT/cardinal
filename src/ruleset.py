import math
import time
from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd

from model import Match, Team

WINNING_POINTS = 3
LOSING_POINTS = 0
DRAW_POINTS = 1


class RulesetEnum(Enum):
    SIMPLE_ELIMINATION = 'Simple-Elimination'
    DOUBLE_ELIMINATION = 'Double-Elimination'
    ROUND_ROBIN = 'Round-Robin'
    SWISS_SYSTEM = 'Swiss-System'

    @classmethod
    def aslist(cls):
        return [e.value for e in cls]

    def get_ruleset(self, name: str, pool_size: int, bo: int):
        if self is RulesetEnum.SIMPLE_ELIMINATION:
            return SimpleElimination(name, self, pool_size, bo)
        if self is RulesetEnum.DOUBLE_ELIMINATION:
            pass  # TODO: implement double elimination bracket
        if self is RulesetEnum.ROUND_ROBIN:
            pass  # TODO: implement round robin bracket
        if self is RulesetEnum.SWISS_SYSTEM:
            pass  # TODO: implement swiss system bracket


class RuleSet(ABC):

    def __init__(self, name: str, rules_type: RulesetEnum, size: int, bo: int):
        self.name = name
        self.rules_type = rules_type
        self.pool: list[Team] = []
        self.poolsize_max = size
        self.bo = bo
        self.match_history: list[Match] = []
        self.bracket = {}
        self.match_queue: list[str] = []
        self.running = False

    def add_team(self, team):
        self.pool.append(team)

    def get_teams(self):
        return self.pool

    def get_team(self, team_name):
        for t in self.pool:
            if t.name == team_name:
                return t

    def get_match(self, id: str) -> Match:
        return self.bracket[id]

    def get_history(self):
        d = {}
        for i in range(len(self.match_history)):
            d[f'{i}'] = pd.Series(self.match_history[i].get_result(), index=[
                                  "blue team", "blue score",
                                  "red team", "red score",
                                  "winner"])
        return pd.DataFrame(d).T

    @abstractmethod
    def next_match(self, team):
        pass

    @abstractmethod
    def start(self):
        pass

    # @abstractmethod
    def get_standings(self):
        for t in self.pool:
            t.points = 0
            t.goals_scored = 0
            t.goals_taken = 0
        # print('standings>>>>')
        for m in list(filter(lambda x: x.get_winner() != None, self.match_history)):
            # print(f'm.get_winner()={m.get_winner()}')
            if m.get_winner() == m.blue_team:
                # print('blue_team')
                blue_team = self.get_team(m.blue_team)
                blue_team.points += WINNING_POINTS
                blue_team.goals_scored += sum(m.blue_score)
                blue_team.goals_taken += sum(m.red_score)
            else:
                # print('red team')
                red_team = self.get_team(m.red_team)
                red_team.points += WINNING_POINTS
                red_team.goals_scored += sum(m.red_score)
                red_team.goals_taken += sum(m.blue_score)
        d = {}
        for i in range(len(self.pool)):
            d[f'{i}'] = self.pool[i].asSeries()
        return pd.DataFrame(d).T.sort_values(['points', 'goals diff'], ascending=[False, False], ignore_index=True)

    @ abstractmethod
    def init_bracket(self):
        pass

    @ abstractmethod
    def get_bracket(self):
        pass

    @ abstractmethod
    def report_match_result(self, match: Match, *games_score: tuple):
        pass

    def asSeries(self):
        return pd.Series(
            [self.name, self.poolsize_max, self.rules_type.value, self.running],
            index=["name", "size", "type", "running"]
        )


class SimpleElimination(RuleSet):

    def next_match(self, team):
        for m in list(map(self.get_match, self.match_queue)):
            # m = self.get_match(m_id)
            if (team == m.blue_team or team == m.red_team):
                return m
        return None

    def start(self):
        self.running = True

    def get_bracket(self) -> pd.DataFrame:
        return pd.DataFrame(self.bracket, index=["matches"]).T.sort_index(ascending=False)

    # def get_standings(self) -> pd.DataFrame:
    #     pass

    def report_match_result(self, match: Match, *games_score: tuple):
        if (self.running):
            for gs in games_score:
                blue_score, red_score = gs
                match.add_game_result(blue_score, red_score)
                match.compute_bo()
            if (match.ended):
                print(f'match ended: {match}')
                self.match_queue.remove(match.id)
                self.match_history.append(match)
                winner = match.get_winner()
                replace = f'winner({match.id})'
                next_match = self.next_match(replace)
                if (next_match != None):
                    nid = next_match.id
                    nblue = next_match.blue_team
                    nred = next_match.red_team
                    if replace == nblue:
                        self.bracket[nid] = Match(
                            nid, next_match.bo, winner, nred)
                    elif replace == nred:
                        self.bracket[nid] = Match(
                            nid, next_match.bo, nblue, winner)
                    else:
                        raise Exception(
                            f"Cannot program next match for {winner}")
                else:  # no more match in phase
                    self.running = False

        else:
            raise Exception('Cannot report match. phase not started')

    def init_bracket(self, bo) -> dict:
        no_of_teams = len(self.pool)
        # print(f'pool={self.pool}, {no_of_teams} teams')

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
