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
    def get_player_field(tournament: Tournament) -> str:
        players = list(
            map(lambda x: f'{RocketLeagueRank.from_elo(x.elo).value["emoji"]} {x.name}',
                sorted(tournament.players_dict.values(), key=lambda p: -p.elo)))
        return """
               {}
               """.format("\n".join(players))

    @staticmethod
    def get_team_field(tournament: Tournament) -> str:
        teams = list(map(lambda team: f'{team} ({int(tournament.get_team_elo(team))})',
                         sorted(tournament.teams_dict.keys(), key=lambda t: -tournament.get_team_elo(t))))
        return """
               {}
               """.format("\n".join(teams))

    @staticmethod
    def get_stage_fields(tournament: Tournament) -> (str, str, str):
        stage_names = list(map(lambda stage_key: f'{tournament.stages_dict[stage_key].name}',
                               sorted(tournament.stages_dict.keys())))
        stage_names_field = """
                            {}
                            """.format("\n".join(stage_names))
        stage_rules = list(map(lambda stage_key: f'{tournament.stages_dict[stage_key].rules_type}',
                               sorted(tournament.stages_dict.keys())))
        stage_rules_field = """
                            {}
                            """.format("\n".join(stage_rules))
        stage_sizes = list(map(lambda stage_key: f'{tournament.stages_dict[stage_key].pool_max_size}',
                               sorted(tournament.stages_dict.keys())))
        stage_sizes_field = """
                            {}
                            """.format("\n".join(stage_sizes))
        return stage_names_field, stage_rules_field, stage_sizes_field

    @staticmethod
    def get_standings_field(tournament: Tournament) -> str:
        for stage in tournament.stages_dict.values():
            stage.get_standings()
        teams_sorted_ga = sorted(tournament.teams_dict.values(),
                                 key=lambda team: (team.goals_scored - team.goals_taken),
                                 reverse=True)
        teams_sorted = sorted(teams_sorted_ga, key=lambda team: team.points, reverse=True)
        teams_sorted_format = list(
            map(lambda team: f'{team.name} (PT={team.points} / GA={(team.goals_scored - team.goals_taken)})',
                teams_sorted))
        standings = [f'{i}: {x}' for i, x in enumerate(teams_sorted_format, start=1)]
        return """
               {}
               """.format("\n".join(standings))

    def get_tournament_presentation(self):
        t: Tournament = self.manager.get_tournament(self.tournament_name)

        # phases_df = t.df_phases().astype('str')
        try:
            #     phases_name_field = """
            #                     {}
            #                     """.format("\n".join(phases_df["name"].values.flatten()))
            #     phases_type_field = """
            #                     {}
            #                     """.format("\n".join(phases_df["type"].values.flatten()))
            #     phases_size_field = """
            #                     {}
            #                     """.format("\n".join(phases_df["size"].values.flatten()))
            bracket = f'{self.manager.get_tournament(self.tournament_name).get_current_phase().bracket}'[-1024:]
        except (KeyError, TypeError):
            #     phases_name_field = ''
            #     phases_type_field = ''
            #     phases_size_field = ''
            bracket = ''

        # try:
        #     standings_field = ''
        # except (KeyError, TypeError):
        #     standings_field = ''

        embed = discord.Embed(
            title=f'{t.name} tournament',
            description=f'Welcome in {t.name} tournament. Register, get your next opponents, follow results... Stay '
                        f'tuned!',
            # Pycord provides a class with default colors you can choose from
            color=discord.Colour.gold(),
        )
        embed.add_field(name="Tournament description & rules", value="Contact tournament owner.", inline=False)

        # embed.add_field(name="STAGE NAME", value=phases_name_field, inline=True)
        # embed.add_field(name="STAGE RULE", value=phases_type_field, inline=True)
        # embed.add_field(name="MAX TEAM", value=phases_size_field, inline=True)
        stage_name_field, stage_rule_field, stage_size_field = TournamentView.get_stage_fields(t)
        embed.add_field(name="STAGE NAME", value=stage_name_field, inline=True)
        embed.add_field(name="STAGE RULE", value=stage_rule_field, inline=True)
        embed.add_field(name="MAX TEAM", value=stage_size_field, inline=True)

        embed.add_field(name="PLAYERS", value=self.get_player_field(t), inline=True)
        embed.add_field(name="TEAMS", value=self.get_team_field(t), inline=True)
        embed.add_field(name="STANDINGS", value=TournamentView.get_standings_field(t), inline=True)

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
        # print(f't.get_current_phase()={t.get_current_phase()}')
        try:
            if t.get_current_phase().running:
                b_next: discord.ui.button = self.get_item('button_next_game')
                b_next.disabled = False
            if not t.get_current_phase().running:
                b_start: discord.ui.button = self.get_item('button_start_phase')
                b_start.disabled = False
                b_start.label = f'Start {t.get_current_phase().name} (admin only)'
        except KeyError:
            pass
        main, embed = self.get_tournament_presentation()
        await interaction.response.edit_message(content=main, embed=embed, view=self)

    @discord.ui.button(custom_id='button_get_my_team', label='Get my team', row=1, style=discord.ButtonStyle.secondary)
    async def get_team_button_callback(self, button, interaction):
        t: Tournament = self.manager.get_tournament(self.tournament_name)
        if interaction.user.display_name in t.players_dict.keys():
            team = t.players_dict[interaction.user.display_name].team
            if team is not None:
                await interaction.response.send_message(f'{interaction.user.mention}, your team is {team}',
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(f'{interaction.user.mention}, you are not part of a team',
                                                        ephemeral=True)
        else:
            await interaction.response.send_message(
                f'{interaction.user.mention}, you are not registered in this tournament', ephemeral=True)

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
        team = t.players_dict[interaction.user.display_name].team
        m: Match = t.get_current_phase().next_match(team)
        if m is not None:
            v: MatchView = MatchView(t, m, interaction.message.channel, interaction.user)
            main, embed = v.get_match_presentation()
            await interaction.response.send_message(content=main, embed=embed, view=v, ephemeral=True)
        else:
            await interaction.response.send_message(content=f'No incoming match found for team {team}', ephemeral=True)

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
