import pandas as pd

import player
import team


def set_value(df, index_col_name, index_value, value_col_name, value):
    df.loc[lambda df: df[index_col_name]
           == index_value, lambda df: [value_col_name]] = value


class Tournament:

    def __init__(self):
        self.name = None
        self.team_size = None
        self.registration_opened = False
        self.admins = []
        self.df_players = pd.DataFrame({
            "name": [],
            "elo": []
        })
        self.df_teams = pd.DataFrame({
            "name": [],
            "elo": []
        })
        self.df_matches = pd.DataFrame({
            "#": [],
            "team 1": [],
            "team 1 score": [],
            "team 2": [],
            "team 2 score": []
        })
        self.df_standings = pd.DataFrame({
            "#": [],
            "team": [],
            "played": [],
            "points": [],
            "OMW": []
        })

    def setup(self, organizer, name, team_size):
        self.name = name
        self.admins.append(organizer)
        self.team_size = team_size

    def add_player(self, name, elo):
        p = player.Player(name, elo)
        self.df_players = pd.concat(
            [self.df_players, p.asDataFrame()], ignore_index=True)

    def add_team(self, name):
        t = team.Team(name)
        self.df_teams = pd.concat(
            [self.df_teams, t.asDataFrame()], ignore_index=True)

    def add_team(self, team_name, *players):
        t = team.Team(team_name, self.team_size)
        self.df_teams = pd.concat(
            [self.df_teams, t.asDataFrame()], ignore_index=True)
        for player_name in players:
            # self.df_players.loc[lambda df: df['name']
            #                     == player, lambda df: ['team']] = name
            set_value(self.df_players, 'name', player_name, 'team', team_name)
