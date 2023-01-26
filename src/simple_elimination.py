import math
import ruleset
import match

import pandas as pd

import time


class SimpleElimination(ruleset.RuleSet):

    def __init__(self, size):
        ruleset.RuleSet.__init__(self, size)
        self.match_queue: match.Match = []
        self.running = False

    def next_match(self, team):
        pass

    def start(self):
        self.running = True
        while (self.running):
            time.sleep(2)
            for m in self.match_queue:
                if (m.get_winner() != None):
                    self.match_queue.remove(m)

    def get_standings(self):
        return pd.DataFrame(self.bracket, index=["matches"]).T

    def report_match_result(self, match_id, blue_score, red_score):
        if (self.running):
            print('do something')
        else:
            print('Cannot report match. phase not started')

    def init_bracket(self, bo):
        no_of_teams = len(self.pool)
        print(f'pool={self.pool}, {no_of_teams} teams')

        bracket_depth = int(math.ceil(math.log(no_of_teams, 2)))
        self.bracket = {}
        for round in range(bracket_depth):
            matches_count = int(math.pow(2, (round)))
            teams_in_round = matches_count * 2
            # matches = {}
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
                self.bracket[match_id] = [match.Match(bo, blue_team, red_team)]
            #     matches[match_id] = match.Match(bo, blue_team, red_team)
            # self.bracket[round] = matches

        return self.bracket
