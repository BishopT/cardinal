import discord
import math
from discord.ext import commands

import tournapy.rocketleague.rankenum
from tournapy.core.model import Match
from tournapy.core.ruleset import RulesetEnum
from tournapy.manager import TournamentManager as TournamentsMgr
from tournapy.tournament import Tournament


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


class Tournaments(commands.Cog):
    tournaments = discord.SlashCommandGroup("tournaments")

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.manager = TournamentsMgr()
        self.view: discord.ui.View = None

    async def ac_tournaments(self, ctx: discord.AutocompleteContext):
        return self.manager.get_tournaments_list()

    async def ac_players(self, ctx: discord.AutocompleteContext):
        t: Tournament = self.manager.get_tournament(ctx.options['tournament_name'])
        return t.players_dict.keys()

    async def ac_teams(self, ctx: discord.AutocompleteContext):
        t: Tournament = self.manager.get_tournament(ctx.options['tournament_name'])
        try:
            # command is set_result so we want only blue team & red team
            match = t.get_current_phase().get_match(ctx.options['match_id'])
            if ctx.focused.name == 'blue_team':
                return [match.blue_team]
            else:
                return [match.red_team]
        except KeyError:
            # other commands where we want all teams
            return t.teams_dict.keys()

    async def ac_matches(self, ctx: discord.AutocompleteContext):
        t: Tournament = self.manager.get_tournament(ctx.options['tournament_name'])
        return list(map(lambda m: m.id, t.get_current_phase().match_history)) + t.get_current_phase().match_queue

    @tournaments.command(name='create', description="create a tournament")
    async def create(self, ctx: discord.ApplicationContext, tournament_name: str, team_size: int, logo_url=None):
        if self.manager.create_tournament(tournament_name, team_size, str(ctx.user.id), logo_url):
            self.view = TournamentView(ctx, tournament_name, self.manager, logo_url)
            main, embed = self.view.get_tournament_presentation()
            await ctx.respond(content=main, embed=embed, view=self.view)
        else:
            await ctx.respond(
                f'Tournament ***{tournament_name}*** already exists. Please delete first or choose another name.')

    @tournaments.command(name='get', description="retrieve a tournament")
    async def get(self, ctx: discord.ApplicationContext,
                  tournament_name: discord.Option(str, autocomplete=ac_tournaments)):
        t: Tournament = self.manager.get_tournament(tournament_name)
        if t is not None:
            self.view = TournamentView(ctx, t.name, self.manager, t.logo_url)
            main, embed = self.view.get_tournament_presentation()
            await ctx.respond(content=main, embed=embed, view=self.view)
        else:
            await ctx.respond(
                f'Tournament ***{tournament_name}*** does not exist. Please create one first or choose another name.')

    @tournaments.command(name='del', description="delete a tournament")
    async def delete_command(self, ctx: discord.ApplicationContext,
                             tournament_name: discord.Option(str, autocomplete=ac_tournaments)):
        success, feedback = self.manager.delete_tournament(
            tournament_name, str(ctx.user.id))
        await ctx.respond(feedback)

    phase = tournaments.create_subgroup("phase", "manage tournament phases")

    @phase.command(name='add', description="add a tournament phase")
    async def add_phase(self, ctx: discord.ApplicationContext,
                        tournament_name: discord.Option(str, autocomplete=ac_tournaments), phase_name: str,
                        rules_name: discord.Option(str, choices=RulesetEnum.as_list()),
                        pool_size: discord.Option(int, autocomplete=ac_pool),
                        bo: discord.Option(int, autocomplete=ac_bo)):
        success, feedback = self.manager.add_phase(tournament_name, phase_name,
                                                   rules_name, pool_size, bo, str(ctx.user.id))
        if success:
            b_start: discord.ui.button = self.view.get_item('button_start_phase')
            b_start.disabled = False
            await ctx.respond(feedback)
            # b_update = self.view.get_item('button_update')
            # await b_update.callback(self.view.message.interaction)
        else:
            await ctx.respond(feedback)

    player = tournaments.create_subgroup("player", "manage tournament players")

    @player.command(name="add", description="register an new player")
    async def add_player(self, ctx: discord.ApplicationContext,
                         tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                         player_name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(ac_members))):
        success, feedback = self.manager.add_player(
            tournament_name, player_name, str(ctx.user.id))
        await ctx.respond(feedback)

    @player.command(name='remove', description="remove a registered player")
    async def remove_player(self, ctx: discord.ApplicationContext,
                            tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                            player_name: discord.Option(str, autocomplete=ac_players)):
        success, feedback = self.manager.remove_player(
            tournament_name, player_name, str(ctx.user.id))
        await ctx.respond(feedback)

    team = tournaments.create_subgroup('team')

    @team.command(name='add', description='create new team')
    async def add_team(self, ctx: discord.ApplicationContext,
                       tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                       team_name: discord.Option(str, autocomplete=ac_teams),
                       players_name: discord.Option(str, autocomplete=ac_players)):
        success, feedback = self.manager.add_team(
            tournament_name, team_name, players_name, user_id=str(ctx.user.id))
        await ctx.respond(feedback)

    match = tournaments.create_subgroup('match')

    @match.command(name='get', description='get match UI')
    async def get_match(self, ctx: discord.ApplicationContext,
                        tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                        match_id: discord.Option(str, autocomplete=ac_matches)):
        t = self.manager.get_tournament(tournament_name)
        m = t.get_current_phase().get_match(match_id)
        v: MatchView = MatchView(t, m, ctx.channel, ctx.user)
        main, embed = v.get_match_presentation()
        await ctx.response.send_message(content=main, embed=embed, view=v)

    @match.command(name='result', description='set match result (admin only)')
    async def set_result(self, ctx: discord.ApplicationContext,
                         tournament_name: discord.Option(str, autocomplete=ac_tournaments),
                         match_id: discord.Option(str, autocomplete=ac_matches),
                         blue_team: discord.Option(str, autocomplete=ac_teams),
                         blue_score: int,
                         red_team: discord.Option(str, autocomplete=ac_teams),
                         red_score: int):
        m = self.manager.get_tournament(tournament_name).get_current_phase().get_match(match_id)
        self.manager.get_tournament(tournament_name).get_current_phase().report_match_result(m, (1, 0), (0, 1), (1, 0))
        await ctx.response.send_message(f'match {m} updated.')


class TournamentView(discord.ui.View):

    def __init__(self, ctx, tournament_name: str, manager: TournamentsMgr, logo_url: str):
        super().__init__(timeout=None)
        self.ctx: discord.ApplicationContext = ctx
        self.tournament_name = tournament_name
        self.manager: TournamentsMgr = manager
        self.tournament = self.manager.get_tournament(self.tournament_name)
        if logo_url is not None:
            self.logo_url = logo_url
            self.tournament.logo_url = logo_url
        else:
            self.logo_url = ctx.user.avatar.url
            self.tournament.logo_url = ctx.user.avatar.url

    def get_tournament_presentation(self):
        t: Tournament = self.manager.get_tournament(self.tournament_name)
        players_list = list(map(lambda x: f'{x}', t.players_dict.values()))
        teams_list = t.teams_dict.keys()
        players_field = """
                        {}
                        """.format("\n".join(players_list))

        teams_field = """
                        {}
                        """.format("\n".join(teams_list))

        phases_df = t.df_phases().astype('str')
        try:
            phases_name_field = """
                            {}
                            """.format("\n".join(phases_df["name"].values.flatten()))
            phases_type_field = """
                            {}
                            """.format("\n".join(phases_df["type"].values.flatten()))
            phases_size_field = """
                            {}
                            """.format("\n".join(phases_df["size"].values.flatten()))
            bracket = self.manager.get_tournament(self.tournament_name).get_current_phase().bracket
        except (KeyError, TypeError):
            phases_name_field = ''
            phases_type_field = ''
            phases_size_field = ''
            bracket = ''

        try:
            standings_field = ''
        except (KeyError, TypeError):
            standings_field = ''

        embed = discord.Embed(
            title=f'{t.name} tournament',
            description=f'Welcome in {t.name} tournament. Register, get your next opponents, follow results... Stay '
                        f'tuned!',
            # Pycord provides a class with default colors you can choose from
            color=discord.Colour.gold(),
        )
        embed.add_field(name="Tournament description & rules", value="Bla Bla ", inline=False)

        embed.add_field(name="PHASES NAMES", value=phases_name_field, inline=True)
        embed.add_field(name="PHASES RULES", value=phases_type_field, inline=True)
        embed.add_field(name="PHASES MAX TEAMS", value=phases_size_field, inline=True)

        embed.add_field(name="PLAYERS", value=players_field, inline=True)
        embed.add_field(name="TEAMS", value=teams_field, inline=True)
        embed.add_field(name="STANDINGS", value=standings_field, inline=True)

        embed.add_field(name="BRACKET", value=bracket, inline=False)

        # footers can have icons too
        embed.set_footer(text=f'Bishop > God.')
        embed.set_author(name=f'{self.ctx.user.name}',
                         icon_url=discord.utils.get(self.ctx.interaction.guild.members,
                                                    id=int(self.tournament.admins[0])).avatar.url)
        embed.set_thumbnail(url=self.tournament.logo_url)
        # url="https://cdn.discordapp.com/attachments/1062914387934990459/1063874292753903676/Logo_Transparent_noir.png")
        # embed.set_image(
        #     url="https://cdn.discordapp.com/attachments/1062914387934990459/1063874292753903676/Logo_Transparent_noir.png")
        return '', embed

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content='You took too long! Disabled all the components.', view=self)

    @discord.ui.button(custom_id='button_register', label='Register', row=0, style=discord.ButtonStyle.primary)
    async def register_button_callback(self, button, interaction):
        success, feedback = self.manager.add_player(
            self.tournament_name, interaction.user.display_name, interaction.user.display_name)
        if success:
            main, embed = self.get_tournament_presentation()
            await interaction.response.edit_message(content=main, embed=embed)
        else:
            await interaction.response.send_message(feedback, view=self)

    @discord.ui.button(custom_id='button_unregister', label='Unregister', row=0, style=discord.ButtonStyle.secondary)
    async def unregister_button_callback(self, button, interaction):
        success, feedback = self.manager.remove_player(
            self.tournament_name, interaction.user.display_name, interaction.user.display_name)
        if success:
            main, embed = self.get_tournament_presentation()
            await interaction.response.edit_message(content=main, embed=embed)
        else:
            await interaction.response.send_message(feedback, view=self)

    @discord.ui.button(custom_id='button_update', label='Update', row=0, style=discord.ButtonStyle.secondary)
    async def update_button_callback(self, button, interaction):
        t: Tournament = self.manager.get_tournament(self.tournament_name)
        try:
            if t.get_current_phase().running:
                b_next: discord.ui.button = self.get_item('button_next_game')
                b_next.disabled = False
            if not t.get_current_phase().running:
                b_start: discord.ui.button = self.get_item('button_start_phase')
                b_start.disabled = False
        except KeyError:
            pass
        main, embed = self.get_tournament_presentation()
        await interaction.response.edit_message(content=main, embed=embed, view=self)

    @discord.ui.button(custom_id='button_start_phase', label='Start next phase (admin only)', disabled=True, row=1,
                       style=discord.ButtonStyle.primary)
    async def start_button_callback(self, button, interaction):
        success, feedback = self.manager.start_next_phase(self.tournament_name, str(interaction.user.id))
        if success:
            b: discord.ui.button = self.get_item('button_next_game')
            b.disabled = False
        await interaction.response.send_message(feedback)

    @discord.ui.button(custom_id='button_next_game', label='Get my next match', disabled=True, row=2,
                       style=discord.ButtonStyle.primary)
    async def next_button_callback(self, button, interaction: discord.Interaction):
        t: Tournament = self.manager.get_tournament(self.tournament_name)
        m: Match = t.get_current_phase().next_match(t.players_dict[interaction.user.display_name].team)
        v: MatchView = MatchView(t, m, interaction.message.channel, interaction.user)
        main, embed = v.get_match_presentation()
        await interaction.response.send_message(content=main, embed=embed, view=v)

    @discord.ui.button(label='Delete Tournament (admin only)', row=3, style=discord.ButtonStyle.danger)
    async def del_button_callback(self, button, interaction):
        await interaction.response.edit_message(content=f'Please confirm you want to delete {self.tournament_name}',
                                                view=DeleteConfirmationView(self))

    # TODO: use Enum ; configure authorized ranks
    @staticmethod
    def select_rank_list():
        rank_options = list(map(lambda rank: discord.SelectOption(value=str(rank[1]),
                                                                  label=rank[0],
                                                                  emoji=rank[2]),
                                tournapy.rocketleague.ranks.RankEnum.as_list()))
        return rank_options

    @discord.ui.select(placeholder='Select your rank!', custom_id='select_rank', min_values=1, max_values=1,
                       options=select_rank_list())
    async def rank_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        print(select.values)
        await interaction.response.send_message(f'You have selected {select.values[0]} rank!')


class DeleteConfirmationView(discord.ui.View):

    def __init__(self, view: TournamentView):
        super().__init__(timeout=None)
        self.view = view

    @discord.ui.button(label='Cancel', row=0, style=discord.ButtonStyle.secondary)
    async def cancel_button_callback(self, button, interaction):
        main, embed = self.view.get_tournament_presentation()
        await interaction.response.edit_message(content=main, embed=embed, view=self.view)

    @discord.ui.button(label='Delete', row=0, style=discord.ButtonStyle.danger)
    async def confirmation_button_callback(self, button, interaction):
        success, feedback = self.view.manager.delete_tournament(
            self.view.tournament_name, str(interaction.user.id))
        if success:
            # button.disabled = True
            # button.label = feedback
            await interaction.response.edit_message(content=feedback, view=None)
        else:
            await interaction.response.edit_message(content=feedback, view=self.view)


class MatchView(discord.ui.View):

    def __init__(self, tournament: Tournament, match: Match, ctx_channel, ctx_user):
        super().__init__(timeout=None)
        self.tournament = tournament
        self.admins = tournament.admins
        self.blue_players = tournament.get_team_players(match.blue_team)
        self.red_players = tournament.get_team_players(match.red_team)
        self.match = match
        self.match_channel_name = f'{self.match.id}_{self.match.blue_team}_{self.match.red_team}'.lower()
        self.match_channel = discord.utils.get(ctx_channel.category.channels, name=self.match_channel_name)
        self.blue_voice = discord.utils.get(ctx_channel.category.channels, name=self.match.blue_team)
        self.red_voice = discord.utils.get(ctx_channel.category.channels, name=self.match.red_team)
        if self.match_channel is not None:
            self.get_item('button_room').disabled = True
        if self.blue_voice and self.red_voice is not None:
            self.get_item('button_vocal').disabled = True

        self.main = f'{ctx_user.mention}, here is your next match: {self.match.blue_team} VS {self.match.red_team}'

    def get_match_presentation(self):
        # m = self.manager.get_tournament(self.tournament_name).get_phase(self.phase_idx).get_match(self.match_id)
        m = self.match
        embed = discord.Embed(
            title=f'{m.id} match',
            description=f'Welcome in {m.id} match: {m.blue_team} vs {m.red_team}',
            # Pycord provides a class with default colors you can choose from
            color=discord.Colour.blue(),
        )
        if self.match_channel is not None:
            embed.add_field(name='match channel', value=self.match_channel.mention, inline=True)
        if self.blue_voice and self.red_voice is not None:
            embed.add_field(name='Blue vocal', value=self.blue_voice.mention, inline=True)
            embed.add_field(name='Red vocal', value=self.red_voice.mention, inline=True)
        for r in range(min(len(m.blue_score), len(m.red_score))):
            embed.add_field(name=f'Game {r + 1}', value=f'[{m.blue_score[r]} - {m.red_score[r]}]', inline=False)
        return self.main, embed

    @discord.ui.button(custom_id='button_room', label="Create Room", style=discord.ButtonStyle.primary)
    async def room_callback(self, button, interaction: discord.Interaction):
        button.disabled = True
        if self.match_channel is None:
            # TODO fix that
            overwrites = MatchView.get_overwrites(interaction.guild, self.admins, self.blue_players + self.red_players)
            self.match_channel = await interaction.guild.create_text_channel(
                name=self.match_channel_name,
                category=interaction.channel.category,
                overwrites=overwrites)
        m, e = self.get_match_presentation()
        await interaction.response.edit_message(content=m, embed=e, view=self)

    @discord.ui.button(custom_id='button_vocal', label="Create Vocal", style=discord.ButtonStyle.primary)
    async def vocal_callback(self, button, interaction):
        button.disabled = True
        if self.blue_voice is None:
            overwrites_blue = MatchView.get_overwrites(interaction.guild, self.admins, self.blue_players)
            self.blue_voice = await interaction.guild.create_voice_channel(name=f'{self.match.blue_team}',
                                                                           category=interaction.channel.category,
                                                                           overwrites=overwrites_blue)
        if self.red_voice is None:
            overwrites_red = MatchView.get_overwrites(interaction.guild, self.admins, self.red_players)
            self.red_voice = await interaction.guild.create_voice_channel(name=f'{self.match.red_team}',
                                                                          category=interaction.channel.category,
                                                                          overwrites=overwrites_red)
        m, e = self.get_match_presentation()
        await interaction.response.edit_message(content=m, embed=e, view=self)

    @discord.ui.button(custom_id='button_report', label="Report Game Result", style=discord.ButtonStyle.primary)
    async def report_callback(self, button, interaction):
        modal = MatchResultModal(self, title="Report game result")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Ask for help", style=discord.ButtonStyle.primary)
    async def help_callback(self, button, interaction: discord.Interaction):
        # TODO retrieve admins
        for admin_id in self.admins:
            admin_member: discord.Member = interaction.guild.get_member(int(admin_id))
            if admin_member.dm_channel is None:
                await admin_member.create_dm()
            await admin_member.dm_channel.send(
                f'{interaction.user.mention} asked for help on match {self.match.id} ({interaction.message.jump_url})')
        await interaction.response.send_message(
            f'Tournament admins have been notified. They will come back to you {interaction.user.mention}.')

    @staticmethod
    def get_overwrites(guild: discord.Guild, admins: list[str], players: list[str]) -> \
            dict[discord.Role, discord.PermissionOverwrite]:
        """

        :rtype: dict[discord.Role, discord.PermissionOverwrite]
        """
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        for admin_id in admins:
            admin_member = guild.get_member(int(admin_id))
            overwrites[admin_member] = discord.PermissionOverwrite(read_messages=True)
        for player in players:
            member = discord.utils.find(lambda m: m.display_name == player.name, guild.members)
            overwrites[member] = discord.PermissionOverwrite(read_messages=True)
        return overwrites


class MatchResultModal(discord.ui.Modal):
    def __init__(self, match_view: MatchView, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.match_view = match_view
        game_to_report = len(match_view.match.blue_score) + 1
        self.title = f'Game {game_to_report}'
        self.add_item(discord.ui.InputText(label=f'Team {match_view.match.blue_team}'))
        self.add_item(discord.ui.InputText(label=f'Team {match_view.match.red_team}'))

    async def callback(self, interaction: discord.Interaction):
        self.match_view.tournament.get_current_phase().report_match_result(self.match_view.match,
                                                                           (self.children[0].value,
                                                                            self.children[1].value))
        m, e = self.match_view.get_match_presentation()
        await interaction.response.edit_message(content=m, embed=e)
