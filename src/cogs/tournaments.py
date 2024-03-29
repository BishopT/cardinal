import csv

import discord
import math
from discord.ext import commands, pages

from tournapy.core.ruleset import RulesetEnum
from tournapy.manager import TournamentManager as TournamentsMgr
from tournapy.rocketleague.rank_enum import RocketLeagueRank
from tournapy.tournament import Tournament
from views.bracket_view import BracketView
from views.match_view import MatchView
from views.tournament_view import TournamentView


def setup(bot):  # this is called by Pycord to set up the cog
    bot.add_cog(Tournaments(bot))  # add the cog to the bot


async def ac_ruleset(ctx: discord.AutocompleteContext):
    return RulesetEnum.as_list()


async def ac_bo(ctx: discord.AutocompleteContext):
    return range(1, 11, 2)


async def ac_pool(ctx: discord.AutocompleteContext):
    return list(map(lambda x: int(math.pow(2, x)), range(1, 7, 1)))


async def ac_members(ctx: discord.AutocompleteContext):
    return list(map(lambda m: m.display_name, ctx.interaction.channel.members))


async def ac_ranks(ctx: discord.AutocompleteContext):
    return list(map(lambda rank: f"{rank['label']}", RocketLeagueRank.as_list()))


class Tournaments(commands.Cog):
    tournaments = discord.SlashCommandGroup("tournaments")

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.manager = TournamentsMgr()

    async def ac_tournaments(self, ctx: discord.AutocompleteContext):
        return self.manager.get_tournaments_list()

    async def ac_players(self, ctx: discord.AutocompleteContext):
        t: Tournament = self.manager.get_tournament(ctx.options['tournament_name'])
        return t.players_dict.keys()

    async def ac_teams(self, ctx: discord.AutocompleteContext):
        t: Tournament = self.manager.get_tournament(ctx.options['tournament_name'])
        try:
            # command is set_result, so we want only blue team & red team
            match = t.get_current_phase().get_match(ctx.options['match_id'])
            if ctx.focused.name == 'blue_team':
                return [match.blue_team]
            else:
                return [match.red_team]
        except KeyError:
            # other commands, so we want all teams
            return t.teams_dict.keys()

    async def ac_stages(self, ctx: discord.AutocompleteContext):
        t: Tournament = self.manager.get_tournament(ctx.options['tournament_name'])
        return list(map(lambda s: s.name, t.stages_dict.values()))

    async def ac_matches(self, ctx: discord.AutocompleteContext):
        t: Tournament = self.manager.get_tournament(ctx.options['tournament_name'])
        return list(map(lambda m: m.id, t.get_current_phase().match_history)) + t.get_current_phase().match_queue

    @tournaments.command(name='create', description="create a tournament")
    async def create(self, ctx: discord.ApplicationContext, tournament_name: str, team_size: int, logo_url=None):
        if self.manager.create_tournament(tournament_name, team_size, str(ctx.user.id), logo_url):
            view = TournamentView(ctx, tournament_name, self.manager, logo_url)
            main, embed = view.get_tournament_presentation()
            await ctx.respond(content=main, embed=embed, view=view)
        else:
            await ctx.respond(
                f'Tournament ***{tournament_name}*** already exists. Please delete first or choose another name.',
                ephemeral=True)

    @tournaments.command(name='get', description="retrieve a tournament")
    async def get(self, ctx: discord.ApplicationContext,
                  tournament_name: discord.Option(str, autocomplete=ac_tournaments)):
        t: Tournament = self.manager.get_tournament(tournament_name)
        if t is not None:
            view = TournamentView(ctx, t.name, self.manager, t.logo_url)
            main, embed = view.get_tournament_presentation()
            await ctx.respond(content=main, embed=embed, view=view)
        else:
            await ctx.respond(
                f'Tournament ***{tournament_name}*** does not exist. Please create one first or choose another name.',
                ephemeral=True)

    @tournaments.command(name='del', description="delete a tournament")
    async def delete_command(self, ctx: discord.ApplicationContext,
                             tournament_name: discord.Option(str, autocomplete=ac_tournaments)):
        success, feedback = self.manager.delete_tournament(
            tournament_name, str(ctx.user.id))
        await ctx.respond(feedback, ephemeral=True)

    stage = tournaments.create_subgroup("stage", "manage tournament stages_dict")

    @stage.command(name='add', description="add a tournament phase")
    async def add_stage(self, ctx: discord.ApplicationContext,
                        tournament_name: discord.Option(str, autocomplete=ac_tournaments), phase_name: str,
                        rules_name: discord.Option(str, choices=RulesetEnum.as_list()),
                        pool_size: discord.Option(int, autocomplete=ac_pool),
                        bo: discord.Option(int, autocomplete=ac_bo)):
        success, feedback = self.manager.add_phase(tournament_name, phase_name,
                                                   rules_name, pool_size, bo, str(ctx.user.id))
        await ctx.respond(feedback, ephemeral=True)

    @stage.command(name='reset', description='')
    async def reset_command(self, ctx: discord.ApplicationContext,
                            tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                            stage_name: discord.Option(str, autocomplete=ac_stages)):
        stage = self.manager.get_tournament(tournament_name).get_stage(stage_name)
        stage.running = False
        stage.init_bracket()
        await ctx.respond(f'stage reinitialized', ephemeral=True)

    @stage.command(name='set')
    async def set_active(self, ctx: discord.ApplicationContext,
                         tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                         stage_idx):
        self.manager.get_tournament(tournament_name).current_phase_idx = int(stage_idx)

    player = tournaments.create_subgroup("player", "manage tournament players")

    @player.command(name="add", description="register an new player")
    async def add_player(self, ctx: discord.ApplicationContext,
                         tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                         player_name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(ac_members)),
                         rank: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(ac_ranks))):
        success, feedback = self.manager.add_player(
            tournament_name, player_name, RocketLeagueRank.from_label(rank).elo, str(ctx.user.id))
        await ctx.respond(feedback, ephemeral=True)

    @player.command(name='remove', description="remove a registered player")
    async def remove_player(self, ctx: discord.ApplicationContext,
                            tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                            player_name: discord.Option(str, autocomplete=ac_players)):
        success, feedback = self.manager.remove_player(
            tournament_name, player_name, str(ctx.user.id))
        await ctx.respond(feedback, ephemeral=True)

    @player.command(name='export')
    async def export_players(self, ctx: discord.ApplicationContext,
                             tournament_name: discord.Option(str, autocomplete=ac_tournaments)):
        players = self.manager.get_tournament(tournament_name).players_dict.values()
        # TODO: choose file to export to using discord option
        with open(f'{tournament_name}_players.csv', 'w', newline='') as csvfile:
            fieldnames = ['name', 'elo']
            csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csvwriter.writeheader()
            for player in players:
                csvwriter.writerow({'name': player.name, 'elo': player.elo})
        await ctx.respond('players list exported', ephemeral=True)

    @player.command(name='import')
    async def import_players(self, ctx: discord.ApplicationContext,
                             tournament_name: discord.Option(str, autocomplete=ac_tournaments)):
        # TODO: choose file to import from using discord option
        with open(f'{tournament_name}_players.csv', 'r', newline='') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                self.manager.add_player(tournament_name, row['name'], int(row['elo']), str(ctx.user.id))
        await ctx.respond('players list imported', ephemeral=True)

    @player.command(name='get', description='Retrieve team of a player')
    async def get_team(self, ctx: discord.ApplicationContext,
                       tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                       players_name: discord.Option(str, autocomplete=ac_players)):
        team = self.manager.get_tournament(tournament_name).players_dict[players_name].team
        if team is not None:
            await ctx.respond(f'{players_name} is in team {team}', ephemeral=True)
        else:
            await ctx.respond(f'{players_name} is not part of a team', ephemeral=True)

    team = tournaments.create_subgroup('team')

    @team.command(name='add', description='create new team')
    async def add_team(self, ctx: discord.ApplicationContext,
                       tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                       team_name: discord.Option(str, autocomplete=ac_teams),
                       players_name: discord.Option(str, autocomplete=ac_players)):
        success, feedback = self.manager.add_team(
            tournament_name, team_name, players_name, user_id=str(ctx.user.id))
        await ctx.respond(feedback, ephemeral=True)

    @team.command(name='get', description='Retrieve players of a team')
    async def get_players(self, ctx: discord.ApplicationContext,
                          tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                          team_name: discord.Option(str, autocomplete=ac_teams)):
        players = list(map(lambda p: p.name, self.manager.get_tournament(tournament_name).get_team_players(team_name)))
        await ctx.respond(f'{team_name} is composed of {players}', ephemeral=True)

    @team.command(name='clean', description='Remove all teams')
    async def clean_teams(self, ctx: discord.ApplicationContext,
                          tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                          ):
        success, feedback = self.manager.clean_teams(tournament_name, user_id=str(ctx.user.id))
        await ctx.respond(feedback, ephemeral=True)

    @team.command(name='generate', description='Automatically generate balanced teams')
    async def generate_teams(self, ctx: discord.ApplicationContext,
                             tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                             ):
        success, feedback = self.manager.generate_teams(tournament_name, user_id=str(ctx.user.id))
        await ctx.respond(feedback, ephemeral=True)

    @team.command(name='remove', description='remove existing team')
    async def rem_team(self, ctx: discord.ApplicationContext,
                       tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                       team_name: discord.Option(str, autocomplete=ac_teams)):
        success, feedback = self.manager.remove_team(tournament_name, team_name, user_id=str(ctx.user.id))
        await ctx.respond(feedback, ephemeral=True)

    match = tournaments.create_subgroup('match')

    @match.command(name='get', description='get match UI')
    async def get_match(self, ctx: discord.ApplicationContext,
                        tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                        match_id: discord.Option(str, autocomplete=ac_matches)):
        t = self.manager.get_tournament(tournament_name)
        m = t.get_current_phase().get_match(match_id)
        v: MatchView = MatchView(t, m, ctx.channel, ctx.user)
        main, embed = v.get_match_presentation()
        await ctx.response.send_message(content=main, embed=embed, view=v, ephemeral=True)

    @match.command(name='result', description='set match result (admin only)')
    async def set_result(self, ctx: discord.ApplicationContext,
                         tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                         match_id: discord.Option(str, autocomplete=ac_matches),
                         blue_team: discord.Option(str, autocomplete=ac_teams),
                         blue_score: int,
                         red_team: discord.Option(str, autocomplete=ac_teams),
                         red_score: int):
        m = self.manager.get_tournament(tournament_name).get_current_phase().get_match(match_id)
        feedback = self.manager.get_tournament(tournament_name).get_current_phase().report_match_result(m, blue_score,
                                                                                                        red_score)
        await ctx.response.send_message(feedback, ephemeral=True)

        m = self.match

    bracket = tournaments.create_subgroup("bracket")

    @bracket.command(name="show")
    async def show_brackets(self, ctx: discord.ApplicationContext,
                            tournament_name: discord.Option(str, autocomplete=ac_tournaments)):
        tournament = self.manager.get_tournament(tournament_name)
        """Demonstrates using page groups to switch between different sets of pages."""

        # view = discord.ui.View()
        # view.add_item(
        #     discord.ui.Select(
        #         placeholder="Test Select Menu, Does Nothing",
        #         options=[
        #             discord.SelectOption(
        #                 label="Example Option",
        #                 value="Example Value",
        #                 description="This menu does nothing!",
        #             )
        #         ],
        #     )
        # )
        page_groups = []
        for k, v in tournament.stages_dict.items():
            bracket_view = BracketView(v)
            page_groups.append(bracket_view.get_page_group())
        paginator = pages.Paginator(pages=page_groups, show_menu=True, timeout=None)
        await paginator.respond(ctx.interaction, ephemeral=False)
