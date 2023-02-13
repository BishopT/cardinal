from typing import List, Dict

import pandas as pd

from model import Match, Player, Team
from ruleset import RuleSet, RulesetEnum

# def set_value(df, index_col_name, index_value, value_col_name, value):
#     df.loc[lambda df: df[index_col_name]
#            == index_value, lambda df: [value_col_name]] = value


class Tournament:

    def __init__(self):
        self.name = None
        self.team_size = None
        self.registration_opened = False
        self.admins: List[str] = []
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
        if name not in list(map(lambda x: x.name, self.players)):
            self.players.append(p)
        # self.df_players = pd.concat(
        #     [self.df_players, p.asDataFrame()], ignore_index=True)

    def remove_player(self, name):
        p = list(filter(lambda x: (x.name == name), self.players))[0]
        if p is not None:
            self.players.remove(p)

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

    def get_player(self, name) -> Player:
        for p in self.players:
            if p.name == name:
                return p
        return None

    def get_team(self, name) -> Team:
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

    def df_phases(self):
        d = {}
        for i in range(len(self.phases)):
            d[f'{i}'] = self.phases[i].asSeries()
        return pd.DataFrame(d).T

    # def init(self):
    #     first_phase = sorted(self.phases)[0]
    #     self.current_phase_idx = first_phase

    #     for t in self.teams:
    #         self.phases[first_phase].add_team(t)


class TournamentsMgr():

    def __init__(self):
        self.tourneys_dict: dict[Tournament] = {}

    def is_tourney_admin(self, t: Tournament, user_id: str) -> bool:
        return user_id in t.admins

    def exists(self, tournament_name: str):
        return tournament_name in self.tourneys_dict.keys()

    def createTournament(self, tournament_name: str, team_size: int, user_id: str) -> bool:
        if not self.exists(tournament_name):
            tourney = Tournament()
            tourney.setup(user_id, tournament_name, team_size)
            self.tourneys_dict[tournament_name] = tourney
            return True
        else:
            return False

    def deleteTournament(self, tournament_name: str, user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            t = self.tourneys_dict[tournament_name]
            if (self.is_tourney_admin(t, user_id)):
                del self.tourneys_dict[tournament_name]
                return (True, f'Tournament {tournament_name} deleted.')
            else:
                return (False, f'Cannot delete tournament {tournament_name}. Missing admin rights.')
        else:
            return (False, f'No tournament {tournament_name} existing.')

    def add_phase(self, tournament_name: str, phase_name: str, rules_name: str, pool_size: int, bo: int, user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            t: Tournament = self.tourneys_dict[tournament_name]
            if (self.is_tourney_admin(t, user_id)):
                ruleset = RulesetEnum(rules_name).get_ruleset(
                    phase_name, pool_size, bo)
                t.add_phase(len(t.phases), ruleset)
            else:
                return (False, f'{phase_name} phase cannot be added to {tournament_name}. Missing admin rights.')
        else:
            return (False, f'{tournament_name} does not exist.')
        # if tournament_name in tourneys_dict:
        #     t = tourneys_dict[tournament_name]
        #     if (is_tourney_admin(ctx, tourneys_dict[tournament_name])):
        #         # if phase_name == "SE":
        #         r = SimpleElimination(phase_name, pool_size)
        #         t.add_phase(phase_order, r)

    def add_player(self, tournament_name: str, player_name: str, user_id: str) -> (bool, str):
        # user_id = user.id of admin or user.name of player
        if self.exists(tournament_name):
            t: Tournament = self.tourneys_dict[tournament_name]
            # players can self register. Admins can register anyone
            if (self.is_tourney_admin(t, user_id) or player_name == user_id):
                t.add_player(player_name, 0)
                return (True, f'{player_name} player registered to {tournament_name}')
            else:
                return (False, f'{player_name} player cannot be registered to {tournament_name}. Missing admin rights')
        else:
            return (False, f'{player_name} player cannot be registered to {tournament_name}. Tournament does not exists')

    def remove_player(self, tournament_name: str, player_name: str, user_id: str) -> (bool, str):
        # user_id = user.id of admin or user.name of player
        if self.exists(tournament_name):
            t: Tournament = self.tourneys_dict[tournament_name]
            # players can self unregister. Admins can unregister anyone
            if (self.is_tourney_admin(t, user_id) or player_name == user_id):
                t.remove_player(player_name)
                return (True, f'{player_name} player unregistered from {tournament_name}')
            else:
                return (False, f'{player_name} player cannot be unregistered from {tournament_name}. Missing admin rights')
        else:
            return (False, f'{player_name} player cannot be unregistered from {tournament_name}. Tournament does not exists')

    def add_team(self, tournament_name: str, team_name: str, *players_name: str, user_id: str) -> bool:
        if self.exists(tournament_name):
            t: Tournament = self.tourneys_dict[tournament_name]
            if (self.is_tourney_admin(t, user_id) or user_id in players_name):
                t.add_to_team(team_name, players_name)
                return (True, f'{team_name} team added to {tournament_name}')
            else:
                return (False, f'Cannot form a team. Missing admin rights')
        else:
            return (False, f'Tournament {tournament_name} does not exists')

    def getTournamentList(self) -> []:
        return self.tourneys_dict.keys()

    def getTournament(self, tournament_name: str) -> Tournament:
        return self.tourneys_dict[tournament_name]
