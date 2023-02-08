# cardinal_bot.py

import os
from dotenv import load_dotenv
import configparser
import logging
import re

import discord

from tournament import Tournament
from ruleset import SimpleElimination

# from discord.ext import commands

# MAGIC_VALUES
# .env
ENV_VAR_DISCORD_TOKEN = 'DISCORD_TOKEN'
ENV_VAR_CONFIG_FILE = 'CARDINAL_CONF'
ENV_VAR_CONFIG_FILE_DEFAULT = 'cardinal.ini'
# .ini
CONF_SECTION_BOT = 'Bot'
CONF_PROP_BOT_CMD_PREFIX = 'CommandPrefix'
CONF_PROP_BOT_CMD_PREFIX_DEFAULT = '/'
CONF_SECTION_LOGGING = 'Log'
CONF_PROP_LOG_FILE = 'LogFile'
CONF_PROP_LOG_FILE_DEFAULT = 'cardinal.log'
CONF_PROP_LOG_FILE_ENC = 'LogFileEncoding'
CONF_PROP_LOG_FILE_ENC_DEFAULT = 'utf-8'
CONF_PROP_LOG_LEVEL = 'LogLevel'
CONF_PROP_LOG_LEVEL_DEFAULT = 'INFO'

# load environment variables
load_dotenv()
TOKEN = os.getenv(ENV_VAR_DISCORD_TOKEN)
CONFIG_FILE = os.getenv(ENV_VAR_CONFIG_FILE, ENV_VAR_CONFIG_FILE_DEFAULT)

# load configuration
conf = configparser.ConfigParser()
conf.read(CONFIG_FILE)
# bot section
BOT_CMD_PREFIX = conf.get(CONF_SECTION_BOT, CONF_PROP_BOT_CMD_PREFIX)
# logging section
LOG_FILE = conf.get(CONF_SECTION_LOGGING, CONF_PROP_LOG_FILE)
LOG_FILE_ENC = conf.get(CONF_SECTION_LOGGING, CONF_PROP_LOG_FILE_ENC)
LOG_LEVEL = logging.getLevelName(
    conf.get(CONF_SECTION_LOGGING, CONF_PROP_LOG_LEVEL))

logger = logging.getLogger('discord')
logger.setLevel(level=LOG_LEVEL)
log_file_handler = logging.FileHandler(
    filename=LOG_FILE, encoding=LOG_FILE_ENC, mode='w')
logger.addHandler(log_file_handler)
# discord.utils.setup_logging(handler=log_file_handler, level=LOG_LEVEL)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot()


tourneys_dict: dict[Tournament] = {}


def is_owner(ctx):
    return ctx.author.id == 216305229757415425


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord and following guilds:')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id})')


######################################
# Admin bot commands
######################################
# create Slash Command group with bot.create_group
admin = bot.create_group("admin", "administrate cardinal")


@admin.command(name='exit', description='shutdown the application')
@discord.guild_only()
async def exit(ctx: discord.ApplicationContext):
    if is_owner(ctx):
        await ctx.respond(f"I'm retiring now. See you soon {ctx.guild}' folks!")
        await bot.close()


@admin.command(description="Sends the bot's latency.")
# a slash command will be created with the name "ping"
async def ping(ctx: discord.ApplicationContext):
    latency_ms = (int)(bot.latency * 1000)
    await ctx.respond(f"Pong! Latency is {latency_ms}ms")

######################################
# Greetings bot commands
######################################
greetings = bot.create_group("greetings", "Greet people")


@greetings.command(name='hello', description='Be polite, come say hi :)')
async def hello_world(ctx: discord.ApplicationContext):
    # user: discord.User = ctx.Author
    await ctx.respond(f'Hey! Happy to see you there {ctx.author.mention}')


@greetings.command(name='bye', description='let me know you leave for now')
async def bye(ctx: discord.ApplicationContext):
    if (is_owner(ctx)):
        await ctx.respond(f"Good Bye, {ctx.author.mention}! I hope I'll see you again soon")

######################################
# Tournament bot commands
######################################
tournaments = bot.create_group("tournaments", "go tournament")


def is_tourney_admin(user_id, tourney: Tournament):
    return user_id in tourney.admins


@tournaments.command(description="create a tournament")
async def create(ctx: discord.ApplicationContext, tournament_name: str, team_size: int):
    if tournament_name not in tourneys_dict:
        tourney = Tournament()
        tourney.setup(ctx.author.id, tournament_name, team_size)
        tourneys_dict[tournament_name] = tourney
        v = TournamentView(ctx, tournament_name)
        main, embed = v.get_tournament_presentation()
        await ctx.respond(main, embed=embed, view=v)
    else:
        await ctx.respond(f'Tournament ***{tournament_name}*** already exists. Please delete first or choose another name.')


def delete(tournament_name: str, user):
    if tournament_name in tourneys_dict:
        t = tourneys_dict[tournament_name]
        print(f't.admins={t.admins}')
        if (is_tourney_admin(user.id, tourneys_dict[tournament_name])):
            del tourneys_dict[tournament_name]
            return (True, f'Tournament {tournament_name} deleted.')
        else:
            return (False, f'Cannot delete tournament {tournament_name} because {user.name} is not an admin of the tournament.')
    else:
        return (False, f'No tournament {tournament_name} existing.')


@tournaments.command(name='del', description="delete a tournament")
async def delete_command(ctx: discord.ApplicationContext, tournament_name: str):
    success, feedback = delete(tournament_name, ctx.author)
    await ctx.respond(feedback)

phase = tournaments.create_subgroup("phase", "manage tournament phases")


@phase.command(name='add', description="add a tournament phase")
async def add_phase(ctx: discord.ApplicationContext, tournament_name: str, rule: str, phase_order: int, phase_name: str, pool_size):
    # if tournament_name in tourneys_dict:
    #     t = tourneys_dict[tournament_name]
    #     if (is_tourney_admin(ctx, tourneys_dict[tournament_name])):
    #         # if phase_name == "SE":
    #         r = SimpleElimination(phase_name, pool_size)
    #         t.add_phase(phase_order, r)
    await ctx.respond(f'{phase_name} tournament phase added to {tournament_name}')

# player = tournaments.create_subgroup("player", "manage tournament players")


# @player.command(name="add", description="register an new player")
async def add_player(ctx: discord.ApplicationContext, tournament_name: str, player_name: str):
    if tournament_name in tourneys_dict:
        t: Tournament = tourneys_dict[tournament_name]
        if (is_tourney_admin(ctx, tourneys_dict[tournament_name])):
            t.add_player(player_name, 0)
            await ctx.respond(f'{player_name} player added to {tournament_name}')

# team = tournaments.create_subgroup('team')


# @team.command(name='add', description='create new team')
async def add_team(ctx: discord.ApplicationContext, tournament_name: str, team_name: str, * players_name: str):
    if tournament_name in tourneys_dict:
        t: Tournament = tourneys_dict[tournament_name]
        if (is_tourney_admin(ctx, tourneys_dict[tournament_name])):
            t.add_to_team(team_name, players_name)
            await ctx.respond(f'{team_name} team added to {tournament_name}')


class TournamentView(discord.ui.View):

    def __init__(self, ctx, tournament_name: str):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.tournament_name = tournament_name

    def get_tournament_presentation(self):
        players_df = tourneys_dict[self.tournament_name].df_players()
        teams_df = tourneys_dict[self.tournament_name].df_teams()
        try:
            players_field = """
                            {}
                            """.format("\n".join(players_df["name"].values.flatten()))

        except:
            players_field = ''
        try:
            teams_field = teams_df["name"]
        except:
            teams_field = ''
        try:
            standings_field = ''
        except:
            standings_field = ''

        embed = discord.Embed(
            title=f'{self.tournament_name} tournament',
            description=f'Welcome in {self.tournament_name} tournament. Register, get your next opponents, follow results... Stay tuned!',
            # Pycord provides a class with default colors you can choose from
            color=discord.Colour.gold(),
        )
        embed.add_field(name="Tournament description & rules",
                        value="Bla Bla ", inline=False)

        embed.add_field(name="PLAYERS",
                        value=players_field, inline=True)
        embed.add_field(name="TEAMS",
                        value=teams_field, inline=True)
        embed.add_field(name="STANDINGS",
                        value=standings_field, inline=True)

        # footers can have icons too
        embed.set_footer(text="Footer! No markdown here.")
        embed.set_author(name=f'{self.ctx.author.name}',
                         icon_url=self.ctx.author.avatar.url)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1062914387934990459/1063874292753903676/Logo_Transparent_noir.png")
        # embed.set_image(
        # url="https://cdn.discordapp.com/attachments/1062914387934990459/1063874292753903676/Logo_Transparent_noir.png")
        return ('', embed)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="You took too long! Disabled all the components.", view=self)

    @discord.ui.button(label="Register", row=0,  style=discord.ButtonStyle.primary)
    async def register_button_callback(self, button, interaction):
        tourneys_dict[self.tournament_name].add_player(
            interaction.user.mention, 0)
        main, embed = self.get_tournament_presentation()
        await interaction.response.edit_message(content=main, embed=embed)

    @discord.ui.button(label="Delete Tournament", row=1, style=discord.ButtonStyle.danger)
    async def del_button_callback(self, button, interaction):
        success, feedback = delete(self.tournament_name, interaction.user)
        if success:
            button.disabled = True  # assuming it can't fail
            button.label = feedback
            await interaction.response.edit_message(content=feedback, view=None)
        else:
            await interaction.response.send_message(feedback, view=self)


bot.run(TOKEN)
