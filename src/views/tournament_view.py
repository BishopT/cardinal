import discord

from tournapy.core.model import Match
from tournapy.manager import TournamentManager as TournamentsMgr
from tournapy.rocketleague.rank_enum import RocketLeagueRank
from tournapy.tournament import Tournament
from views.match_view import MatchView


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

    @staticmethod
    def get_player_field(tournament: Tournament):
        players = list(
            map(lambda x: f'{RocketLeagueRank.from_elo(x.elo).value["emoji"]} {x}',
                sorted(tournament.players_dict.values(), key=lambda p: -p.elo)))
        return """
               {}
               """.format("\n".join(players))

    @staticmethod
    def get_team_field(tournament: Tournament):
        teams = list(map(lambda team: f'{team} ({tournament.get_team_elo(team)})',
                         sorted(tournament.teams_dict.keys(), key=lambda t: -tournament.get_team_elo(t))))
        return """
               {}
               """.format("\n".join(teams))

    def get_tournament_presentation(self):
        t: Tournament = self.manager.get_tournament(self.tournament_name)

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

        embed.add_field(name="STAGES NAMES", value=phases_name_field, inline=True)
        embed.add_field(name="STAGES RULES", value=phases_type_field, inline=True)
        embed.add_field(name="STAGES MAX TEAMS", value=phases_size_field, inline=True)

        embed.add_field(name="PLAYERS", value=self.get_player_field(t), inline=True)
        embed.add_field(name="TEAMS", value=self.get_team_field(t), inline=True)
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

    @discord.ui.button(custom_id='button_register', label='Register', row=1, style=discord.ButtonStyle.primary)
    async def register_button_callback(self, button, interaction: discord.Interaction):
        register_view = RegisterView(self.manager, self.tournament_name)
        await interaction.response.send_message(f'Complete your registration by giving us your rank:',
                                                view=register_view, ephemeral=True)

    @discord.ui.button(custom_id='button_unregister', label='Unregister', row=1, style=discord.ButtonStyle.secondary)
    async def unregister_button_callback(self, button, interaction):
        success, feedback = self.manager.remove_player(
            self.tournament_name, interaction.user.display_name, interaction.user.display_name)
        if success:
            main, embed = self.get_tournament_presentation()
            await interaction.response.edit_message(content=main, embed=embed)
        else:
            await interaction.response.send_message(feedback, view=self, ephemeral=True)

    @discord.ui.button(custom_id='button_update', label='Update', row=1, style=discord.ButtonStyle.secondary)
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

    @discord.ui.button(custom_id='button_start_phase', label='Start next phase (admin only)', disabled=True, row=2,
                       style=discord.ButtonStyle.primary)
    async def start_button_callback(self, button, interaction):
        success, feedback = self.manager.start_next_phase(self.tournament_name, str(interaction.user.id))
        if success:
            b: discord.ui.button = self.get_item('button_next_game')
            b.disabled = False
        await interaction.response.send_message(feedback, ephemeral=True)

    @discord.ui.button(custom_id='button_next_game', label='Get my next match', disabled=True, row=2,
                       style=discord.ButtonStyle.primary)
    async def next_button_callback(self, button, interaction: discord.Interaction):
        t: Tournament = self.manager.get_tournament(self.tournament_name)
        m: Match = t.get_current_phase().next_match(t.players_dict[interaction.user.display_name].team)
        v: MatchView = MatchView(t, m, interaction.message.channel, interaction.user)
        main, embed = v.get_match_presentation()
        await interaction.response.send_message(content=main, embed=embed, view=v, ephemeral=True)

    @discord.ui.button(label='Delete Tournament (admin only)', row=3, style=discord.ButtonStyle.danger)
    async def del_button_callback(self, button, interaction):
        await interaction.response.edit_message(content=f'Please confirm you want to delete {self.tournament_name}',
                                                view=DeleteConfirmationView(self))


class RegisterView(discord.ui.View):

    def __init__(self, manager, tournament_name):
        super().__init__(timeout=None)
        self.manager = manager
        self.tournament_name = tournament_name

    # TODO configure authorized ranks
    @staticmethod
    def select_rank_list():
        rank_options = list(
            map(lambda rank: discord.SelectOption(label=rank['label'], emoji=rank['emoji']),
                RocketLeagueRank.as_list()))
        return rank_options

    @discord.ui.select(placeholder='Select your rank', custom_id='select_rank', min_values=1, max_values=1,
                       options=select_rank_list(), row=0)
    async def rank_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        rank = RocketLeagueRank.from_label(select.values[0])
        print(f'rank={rank}')
        success, feedback = self.manager.add_player(
            self.tournament_name, interaction.user.display_name, rank.value['elo'], interaction.user.display_name)
        if success:
            await interaction.response.edit_message(
                content=f"You are registered as {rank.value['emoji']} {rank.value['label']}", view=None)
        else:
            await interaction.response.edit_message(content=feedback, view=None)


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
