import math

import discord
from discord.ext import commands

import model
from ruleset import RulesetEnum
from tournament import Tournament, TournamentsMgr


def setup(bot):  # this is called by Pycord to set up the cog
    bot.add_cog(Tournaments(bot))  # add the cog to the bot


async def ac_ruleset(ctx: discord.AutocompleteContext):
    return RulesetEnum.as_list()


async def ac_bo(ctx: discord.AutocompleteContext):
    return range(1, 11, 2)


async def ac_pool(ctx: discord.AutocompleteContext):
    return list(map(lambda x: int(math.pow(2, x)), range(1, 7, 1)))


async def ac_members(ctx: discord.AutocompleteContext):
    return list(map(lambda x: x.display_name, ctx.interaction.guild.members))


class Tournaments(commands.Cog):
    tournaments = discord.SlashCommandGroup("tournaments", "go tournament")

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
        return t.teams_dict.keys()

    @tournaments.command(description="create a tournament")
    async def create(self, ctx: discord.ApplicationContext, tournament_name: str, team_size: int, logo_url=None):
        if self.manager.create_tournament(tournament_name, team_size, str(ctx.user.id)):
            self.view = TournamentView(ctx, tournament_name, self.manager, logo_url)
            main, embed = self.view.get_tournament_presentation()
            await ctx.respond(content=main, embed=embed, view=self.view)
        else:
            await ctx.respond(
                f'Tournament ***{tournament_name}*** already exists. Please delete first or choose another name.')

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
                        rules_name: discord.Option(str, autocomplete=ac_ruleset),
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
                         player_name: discord.Option(str, autocomplete=ac_members)):
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


class TournamentView(discord.ui.View):

    def __init__(self, ctx, tournament_name: str, manager: TournamentsMgr, logo_url: str):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.tournament_name = tournament_name
        self.manager: TournamentsMgr = manager
        if logo_url is not None:
            self.logo_url = logo_url
        else:
            self.logo_url = ctx.user.avatar.url

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
                         icon_url=self.ctx.user.avatar.url)
        embed.set_thumbnail(url=self.logo_url)
        # url="https://cdn.discordapp.com/attachments/1062914387934990459/1063874292753903676/Logo_Transparent_noir.png")
        # embed.set_image(
        #     url="https://cdn.discordapp.com/attachments/1062914387934990459/1063874292753903676/Logo_Transparent_noir.png")
        return '', embed

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content='You took too long! Disabled all the components.', view=self)

    @discord.ui.button(label='Register', row=0, style=discord.ButtonStyle.primary)
    async def register_button_callback(self, button, interaction):
        success, feedback = self.manager.add_player(
            self.tournament_name, interaction.user.display_name, interaction.user.display_name)
        if success:
            main, embed = self.get_tournament_presentation()
            await interaction.response.edit_message(content=main, embed=embed)
        else:
            await interaction.response.send_message(feedback, view=self)

    @discord.ui.button(label='Unregister', row=0, style=discord.ButtonStyle.secondary)
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
    async def next_button_callback(self, button, interaction):
        t: Tournament = self.manager.get_tournament(self.tournament_name)
        player = t.players_dict[interaction.user.display_name]
        print(f'next match for my team : player={player}, team={player.team}')
        m: model.Match = t.get_current_phase().next_match(t.players_dict[interaction.user.display_name].team)
        # TODO: create chat room with all participants
        await interaction.response.send_message(f'{interaction.user.mention}, here is your next match: {m}')

    @discord.ui.button(label='Delete Tournament (admin only)', row=3, style=discord.ButtonStyle.danger)
    async def del_button_callback(self, button, interaction):
        await interaction.response.edit_message(content=f'Please confirm you want to delete {self.tournament_name}',
                                                view=DeleteConfirmationView(self))


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
