# cardinal_bot.py

import os
from dotenv import load_dotenv
import configparser
import logging

import discord
from discord.ext import commands

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

log_file_handler = logging.FileHandler(
    filename=LOG_FILE, encoding=LOG_FILE_ENC, mode='w')
discord.utils.setup_logging(handler=log_file_handler, level=LOG_LEVEL)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=BOT_CMD_PREFIX, intents=intents)


def is_owner(ctx):
    async def predicate(ctx):
        return ctx.author.id == 216305229757415425


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord and following guilds:')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id})')


@bot.slash_command(name='hello', description='Be polite, come say hi :)')
async def hello_world(ctx, user: discord.User = commands.Author):
    await ctx.send(f'Hey! Happy to here from you {user.mention}')


@bot.command(name='exit')
async def exit(ctx):
    await ctx.send(f"I'm retiring now. See you soon {ctx.guild}' folks!")
    await bot.close()


@bot.command(name='ban')
@commands.check(is_owner)
async def ban(ctx, username):
    await ctx.send(f'{username} is banned')

bot.run(TOKEN)
