from typing import List, Dict

import pandas as pd

from model import Player, Team
from ruleset import RuleSet, RulesetEnum


class Tournament:

    def __init__(self):
        self.name = None
        self.team_size = None
        self.registration_opened = False
        self.admins: List[str] = []
        # TODO: move to dict players
        self.players: List[Player] = []
        #  TODO : move to dict teams
        self.teams: List[Team] = []
        self.phases: Dict[int, RuleSet] = {}
        self.current_phase_idx = 0

    def setup(self, organizer, name, team_size):
        self.name = name
        self.admins.append(organizer)
        self.team_size = team_size

    def add_player(self, name, elo):
        p = Player(name, elo)
        if name not in list(map(lambda x: x.name, self.players)):
            self.players.append(p)

    def remove_player(self, name):
        p = list(filter(lambda x: (x.name == name), self.players))[0]
        if p is not None:
            self.players.remove(p)

    def add_to_team(self, team_name, *players_names):
        t = self.get_team(team_name)
        if t is None:
            t = Team(team_name, self.team_size)
            self.teams.append(t)
        for name in players_names:
            p = self.get_player(name)
            if p is not None:
                p.set_team(team_name)

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

    def is_admin(self, user_id) -> bool:
        return user_id in self.admins

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


class TournamentsMgr:

    def __init__(self):
        self.tourneys_dict: dict[str, Tournament] = {}

    def is_admin(self, tournament_name: str, user_id: str) -> bool:
        if self.exists(tournament_name):
            return self.get_tournament(tournament_name).is_admin(user_id)

    def exists(self, tournament_name: str):
        return tournament_name in self.tourneys_dict.keys()

    def create_tournament(self, tournament_name: str, team_size: int, user_id: str) -> bool:
        if not self.exists(tournament_name):
            tourney = Tournament()
            tourney.setup(user_id, tournament_name, team_size)
            self.tourneys_dict[tournament_name] = tourney
            return True
        else:
            return False

    def delete_tournament(self, tournament_name: str, user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            if self.is_admin(tournament_name, user_id):
                del self.tourneys_dict[tournament_name]
                return True, f'Tournament {tournament_name} deleted.'
            else:
                return False, f'Cannot delete tournament {tournament_name}. Missing admin rights.'
        else:
            return False, f'No tournament {tournament_name} existing.'

    def add_phase(self, tournament_name: str, phase_name: str, rules_name: str, pool_size: int, bo: int,
                  user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            if self.is_admin(tournament_name, user_id):
                ruleset = RulesetEnum(rules_name).get_ruleset(
                    phase_name, pool_size, bo)
                t: Tournament = self.tourneys_dict[tournament_name]
                t.add_phase(len(t.phases), ruleset)
            else:
                return False, f'{phase_name} phase cannot be added to {tournament_name}. Missing admin rights.'
        else:
            return False, f'{tournament_name} does not exist.'

    def add_player(self, tournament_name: str, player_name: str, user_id: str) -> (bool, str):
        # user_id = user.id of admin or user.name of player
        if self.exists(tournament_name):
            # players can self register. Admins can register anyone
            if self.is_admin(tournament_name, user_id) or player_name == user_id:
                t: Tournament = self.tourneys_dict[tournament_name]
                t.add_player(player_name, 0)
                return True, f'{player_name} player registered to {tournament_name}'
            else:
                return False, f'{player_name} player cannot be registered to {tournament_name}. Missing admin rights'
        else:
            return (
                False, f'{player_name} player cannot be registered to {tournament_name}. Tournament does not exists')

    def remove_player(self, tournament_name: str, player_name: str, user_id: str) -> (bool, str):
        # user_id = user.id of admin or user.name of player
        if self.exists(tournament_name):
            # players can self unregister. Admins can unregister anyone
            if self.is_admin(tournament_name, user_id) or player_name == user_id:
                t: Tournament = self.tourneys_dict[tournament_name]
                t.remove_player(player_name)
                return True, f'{player_name} player unregistered from {tournament_name}'
            else:
                return (
                    False, f'{player_name} player cannot be unregistered from {tournament_name}. Missing admin rights')
        else:
            return (
                False,
                f'{player_name} player cannot be unregistered from {tournament_name}. Tournament does not exists')

    def add_team(self, tournament_name: str, team_name: str, *players_name: str, user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            if self.is_admin(tournament_name, user_id) or user_id in players_name:
                t: Tournament = self.tourneys_dict[tournament_name]
                t.add_to_team(team_name, players_name)
                return True, f'{team_name} team added to {tournament_name}'
            else:
                return False, f'Cannot form a team. Missing admin rights'
        else:
            return False, f'Tournament {tournament_name} does not exists'

    def get_tournaments_list(self) -> []:
        return self.tourneys_dict.keys()

    def get_tournament(self, tournament_name: str) -> Tournament:
        return self.tourneys_dict[tournament_name]
