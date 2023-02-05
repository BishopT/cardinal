# cardinal_bot.py

import os
from dotenv import load_dotenv
import configparser
import logging

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
async def exit(ctx):
    if is_owner(ctx):
        await ctx.respond(f"I'm retiring now. See you soon {ctx.guild}' folks!")
        await bot.close()


@admin.command(description="Sends the bot's latency.")
async def ping(ctx):  # a slash command will be created with the name "ping"
    latency_ms = (int)(bot.latency * 1000)
    await ctx.respond(f"Pong! Latency is {latency_ms}ms")

######################################
# Greetings bot commands
######################################
greetings = bot.create_group("greetings", "Greet people")


@greetings.command(name='hello', description='Be polite, come say hi :)')
async def hello_world(ctx):
    # user: discord.User = ctx.Author
    await ctx.respond(f'Hey! Happy to see you there {ctx.author.mention}')


@greetings.command(name='bye', description='let me know you leave for now')
async def bye(ctx):
    if (is_owner(ctx)):
        await ctx.respond(f"Good Bye, {ctx.author.mention}! I hope I'll see you again soon")

######################################
# Tournament bot commands
######################################
tournaments = bot.create_group("tournaments", "go tournament")


def is_tourney_admin(user_id, tourney: Tournament):
    return user_id in tourney.admins


@tournaments.command(description="create a tournament")
async def create(ctx, tournament_name: str, team_size: int):
    if tournament_name not in tourneys_dict:
        tourney = Tournament()
        tourney.setup(ctx.author.id, tournament_name, team_size)
        tourneys_dict[tournament_name] = tourney
        await ctx.respond(f'Tournament: {tournament_name}', view=TournamentView(ctx))
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
async def delete_command(ctx, tournament_name: str):
    success, feedback = delete(tournament_name, ctx.author)
    await ctx.respond(feedback)


@tournaments.command(description="add a tournament phase")
async def add_phase(ctx, tournament_name: str, rule: str, phase_order: int, phase_name: str, pool_size):
    if tournament_name in tourneys_dict:
        t = tourneys_dict[tournament_name]
        if (is_tourney_admin(ctx, tourneys_dict[tournament_name])):
            if phase_name == "SE":
                r = SimpleElimination(phase_name, pool_size)
            t.add_phase(phase_order, r)


class TournamentView(discord.ui.View):

    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="You took too long! Disabled all the components.", view=self)

    @discord.ui.button(label="Register", row=0,  style=discord.ButtonStyle.primary)
    async def register_button_callback(self, button, interaction):
        tournament_name = interaction.message.content.split(':')[1].strip()
        tourneys_dict[tournament_name].add_player()
        await interaction.response.edit_message(f'{interaction.message.content}')

    @discord.ui.button(label="Delete Tournament", row=1, style=discord.ButtonStyle.danger)
    async def del_button_callback(self, button, interaction):
        tournament_name = interaction.message.content.split(':')[1].strip()
        success, feedback = delete(tournament_name, interaction.user)
        if success:
            button.disabled = True  # assuming it can't fail
            button.label = feedback
            await interaction.response.edit_message(content=feedback, view=None)
        else:
            await interaction.response.send_message(feedback)


bot.run(TOKEN)
