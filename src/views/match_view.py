import discord

from tournapy.core.model import Match, Player
from tournapy.tournament import Tournament


class MatchView(discord.ui.View):

    def __init__(self, tournament: Tournament, match: Match, ctx_channel, ctx_user):
        super().__init__(timeout=None)
        self.tournament = tournament
        self.admins = tournament.admins
        self.blue_players: list[Player] = tournament.get_team_players(match.blue_team)
        self.red_players: list[Player] = tournament.get_team_players(match.red_team)
        self.match = match
        self.match_channel_name = f'{self.match.id}_{self.match.blue_team}_{self.match.red_team}'.lower()
        self.match_channel = discord.utils.get(ctx_channel.category.channels, name=self.match_channel_name)
        self.blue_voice = discord.utils.get(ctx_channel.category.channels, name=self.match.blue_team)
        self.red_voice = discord.utils.get(ctx_channel.category.channels, name=self.match.red_team)
        if self.match_channel is not None:
            self.get_item('button_room').disabled = True
        if self.blue_voice and self.red_voice is not None:
            self.get_item('button_vocal').disabled = True
        self.main = f'{ctx_user.mention}, here is the match: {self.match.blue_team} VS {self.match.red_team}'
        if self.match.ended:
            self.get_item(custom_id='button_report').disabled = True

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
            embed.add_field(name=f'Game {r + 1}', value=f'[{m.blue_score[r]} - {m.red_score[r]}]', inline=True)
        if m.ended:
            embed.add_field(name='WINNER', value=m.get_winner(), inline=False)
        return self.main, embed

    @discord.ui.button(custom_id='button_room', label="Create Room", style=discord.ButtonStyle.primary)
    async def room_callback(self, button, interaction: discord.Interaction):
        button.disabled = True
        if self.match_channel is None:
            # TODO fix that
            overwrites = MatchView.get_overwrites(interaction.guild, self.admins, self.blue_players + self.red_players)
            print(f'overwrites={overwrites}')
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
        for admin_id in self.admins:
            admin_member: discord.Member = interaction.guild.get_member(int(admin_id))
            if admin_member.dm_channel is None:
                await admin_member.create_dm()
            await admin_member.dm_channel.send(
                f'{interaction.user.mention} asked for help on match {self.match.id} ({interaction.message.jump_url})')
        await interaction.response.send_message(
            f'Tournament admins have been notified. They will come back to you {interaction.user.mention}.')

    @staticmethod
    def get_overwrites(guild: discord.Guild, admins: list[str], players: list[Player]) -> \
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
            if member is not None:
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
                                                                           blue_score=int(self.children[0].value),
                                                                           red_score=int(self.children[1].value))
        m, e = self.match_view.get_match_presentation()
        if self.match_view.match.ended:
            self.match_view.get_item(custom_id='button_report').disabled = True
        await interaction.response.edit_message(content=m, embed=e)
