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
        self.players_dict: dict[Player] = {}
        self.teams_dict: dict[Team] = {}
        self.phases: Dict[int, RuleSet] = {}
        self.current_phase_idx = 0

    def setup(self, organizer, name, team_size):
        self.name = name
        self.admins.append(organizer)
        self.team_size = team_size

    def add_player(self, name, elo):
        p = Player(name, elo)
        if name not in self.players_dict.keys():
            self.players_dict[name] = p

    def remove_player(self, name):
        if name in self.players_dict.keys():
            del self.players_dict[name]

    def add_to_team(self, team_name, *players_names) -> (bool, str):
        try:
            t = self.teams_dict[team_name]
        except KeyError:
            t = Team(team_name)
            self.teams_dict[team_name] = t
        if t.size < self.team_size:
            for name in players_names:
                try:
                    p = self.players_dict[name]
                    p.set_team(team_name)
                    t.size += 1
                    return True, f'{name} is now in team {t} ({t.size})'
                except KeyError:
                    return False, f'{name} is not subscribed to tournament'
        else:
            return False, f'Cannot add any player to {team_name} because team is already complete'

    def add_phase(self, order: int, ruleset: RuleSet):
        self.phases[order] = ruleset

    def get_current_phase(self) -> RuleSet:
        return self.get_phase(self.current_phase_idx)

    def get_phase(self, phase_number) -> RuleSet:
        return self.phases[phase_number]

    def is_admin(self, user_id: str) -> bool:
        return user_id in self.admins

    def df_players(self):
        d = {}
        for i in range(len(self.players)):
            d[f'{i}'] = self.players[i].as_series()
        return pd.DataFrame(d).T

    def df_teams(self):
        d = {}
        for key, value in self.teams_dict.items():
            d[f'{key}'] = value.as_series()
        # TODO: sort by seeding
        return pd.DataFrame(d).T.sort_values(['elo'], ascending=False, ignore_index=True)

    def df_phases(self):
        d = {}
        for i in range(len(self.phases)):
            d[f'{i}'] = self.phases[i].as_series()
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
                return True, f'{phase_name} phase added to {tournament_name} tournament.'
            else:
                return False, f'{phase_name} phase cannot be added to {tournament_name}. Missing admin rights.'
        else:
            return False, f'{tournament_name} does not exist.'

    def start_next_phase(self, tournament_name: str, user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            if self.is_admin(tournament_name, user_id):
                t: Tournament = self.tourneys_dict[tournament_name]
                # Retrieve list of teams eligible for next phase:
                # 1st case: no phase performed yet, every team should be added
                if t.current_phase_idx == 0:
                    teams_names = t.df_teams()['name']
                # 2nd case: get list of teams sorted by their rankings.
                else:
                    previous_phase = t.get_phase(t.current_phase_idx - 1)
                    teams_names = previous_phase.get_standings()['name']
                next_phase = t.get_current_phase()
                # adding previously retrieved list of teams. Will be added following team rank from previous phase.
                # will not accept team if next phase pool is complete.
                for team_name in teams_names:
                    # next_phase.add_team(t.get_team(team_name))
                    next_phase.add_team(t.teams_dict[team_name])
                if not next_phase.running:
                    next_phase.init_bracket()
                    next_phase.start()
                    return True, f'{next_phase.name} phase started.'
                else:
                    return False, f'{next_phase.name} already running.'
            else:
                return False, f'Cannot start next phase of {tournament_name}. Missing admin rights.'
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

    def add_team(self, tournament_name: str, team_name: str, players_name: str, user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            if self.is_admin(tournament_name, user_id) or user_id in players_name:
                t: Tournament = self.tourneys_dict[tournament_name]
                success, feedback = t.add_to_team(team_name, players_name)
                return success, feedback
            else:
                return False, f'Cannot form a team. Missing admin rights'
        else:
            return False, f'Tournament {tournament_name} does not exists'

    def get_tournaments_list(self) -> []:
        return self.tourneys_dict.keys()

    def get_tournament(self, tournament_name: str) -> Tournament:
        return self.tourneys_dict[tournament_name]
