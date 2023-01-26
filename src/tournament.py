from typing import List
import pandas as pd

import player
import team
import ruleset
import match


# def set_value(df, index_col_name, index_value, value_col_name, value):
#     df.loc[lambda df: df[index_col_name]
#            == index_value, lambda df: [value_col_name]] = value


class Tournament:

    def __init__(self):
        self.name = None
        self.team_size = None
        self.registration_opened = False
        self.admins = []
        self.players: List[player.Player] = []
        self.teams: List[team.Team] = []
        self.phases: List[ruleset.Ruleset] = []

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
        p = player.Player(name, elo)
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
            t = team.Team(team_name, self.team_size)
            self.teams.append(t)
        for name in players_names:
            self.get_player(name).set_team(team_name)
            # self.df_teams = pd.concat(
            #     [self.df_teams, t.asDataFrame()], ignore_index=True)
            # for player_name in players:
            #     # self.df_players.loc[lambda df: df['name']
            #     #                     == player, lambda df: ['team']] = name
            #     set_value(self.df_players, 'name', player_name, 'team', team_name)

    def add_phase(self, ruleset: ruleset):
        self.phases.append(ruleset)

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

    def get_phase(self, phase_number) -> ruleset:
        return self.phases[phase_number - 1]

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
            self.phases[0].add_team(t)
