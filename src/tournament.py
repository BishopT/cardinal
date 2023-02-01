from typing import List, Dict

import pandas as pd

from model import Match, Player, Team
from ruleset import RuleSet

# def set_value(df, index_col_name, index_value, value_col_name, value):
#     df.loc[lambda df: df[index_col_name]
#            == index_value, lambda df: [value_col_name]] = value


class Tournament:

    def __init__(self):
        self.name = None
        self.team_size = None
        self.registration_opened = False
        self.admins = []
        self.players: List[Player] = []
        self.teams: List[Team] = []
        self.phases: Dict[int, RuleSet] = {}
        self.current_phase_idx = 0

        # self.df_matches = pd.DataFrame({
        #     "#": [],
        #     "team 1": [],
        #     "team 1 score": [],
        #     "team 2": [],
        #     "team 2 score": []
        # })

        # self.df_standings = pd.DataFrame({
        #     "#": [],
        #     "team": [],
        #     "played": [],
        #     "points": [],
        #     "OMW": []
        # })

    def setup(self, organizer, name, team_size):
        self.name = name
        self.admins.append(organizer)
        self.team_size = team_size

    def add_player(self, name, elo):
        p = Player(name, elo)
        self.players.append(p)
        # self.df_players = pd.concat(
        #     [self.df_players, p.asDataFrame()], ignore_index=True)

    # def add_team(self, name):
    #     t = team.Team(name)
        # self.df_teams = pd.concat(
        #     [self.df_teams, t.asDataFrame()], ignore_index=True)

    def add_to_team(self, team_name, *players_names):
        t = self.get_team(team_name)
        if t == None:
            t = Team(team_name, self.team_size)
            self.teams.append(t)
        for name in players_names:
            self.get_player(name).set_team(team_name)
            # self.df_teams = pd.concat(
            #     [self.df_teams, t.asDataFrame()], ignore_index=True)
            # for player_name in players:
            #     # self.df_players.loc[lambda df: df['name']
            #     #                     == player, lambda df: ['team']] = name
            #     set_value(self.df_players, 'name', player_name, 'team', team_name)

    def add_phase(self, order: int, ruleset: RuleSet):
        self.phases[order] = ruleset

    def get_player(self, name):
        for p in self.players:
            if p.name == name:
                return p
        return None

    def get_team(self, name):
        for t in self.teams:
            if t.name == name:
                return t
        return None

    def get_current_phase(self) -> RuleSet:
        return self.get_phase(self.current_phase_idx)

    def get_phase(self, phase_number) -> RuleSet:
        return self.phases[phase_number]

    def df_players(self):
        d = {}
        for i in range(len(self.players)):
            d[f'{i}'] = self.players[i].asSeries()
        return pd.DataFrame(d).T

    def df_teams(self):
        d = {}
        for i in range(len(self.teams)):
            d[f'{i}'] = self.teams[i].asSeries()
        return pd.DataFrame(d).T

    def init(self):
        for t in self.teams:
            first_phase = sorted(self.phases)[0]
            self.current_phase_idx = first_phase
            self.phases[first_phase].add_team(t)
