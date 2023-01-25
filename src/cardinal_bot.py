# cardinal_bot.py

import os
from dotenv import load_dotenv
import configparser
import logging

import discord
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

# bot = commands.Bot(command_prefix=BOT_CMD_PREFIX, intents=intents)
bot = discord.Bot()


def is_owner(ctx):
    async def predicate(ctx):
        return ctx.author.id == 216305229757415425


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord and following guilds:')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id})')


# create Slash Command group with bot.create_group
greetings = bot.create_group("greetings", "Greet people")
admin = bot.create_group("admin", "administrate cardinal")


@greetings.command(name='hello', description='Be polite, come say hi :)')
async def hello_world(ctx):
    # user: discord.User = ctx.Author
    await ctx.respond(f'Hey! Happy to see you there {ctx.author.mention}')


@greetings.command(name='bye', description='let me know you leave for now')
async def bye(ctx):
    await ctx.respond(f"Good Bye, {ctx.author.mention}! I hope I'll see you again soon")


@admin.command(name='exit', description='shutdown the application')
@discord.guild_only()
async def exit(ctx):
    await ctx.respond(f"I'm retiring now. See you soon {ctx.guild}' folks!")
    await bot.close()


# @bot.command(name='ban')
# @commands.check(is_owner)
# async def ban(ctx, username):
#     await ctx.send(f'{username} is banned')


# this decorator makes a slash command
@admin.command(description="Sends the bot's latency.")
async def ping(ctx):  # a slash command will be created with the name "ping"
    latency_ms = (int)(bot.latency * 1000)
    await ctx.respond(f"Pong! Latency is {latency_ms}ms")


class MyView(discord.ui.View):  # Create a class called MyView that subclasses discord.ui.View

    # def __init__(self, ctx):
    #     self.ctx = ctx

    # Create a button with the label "😎 Click me!" with color Blurple
    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.primary, emoji="😎")
    async def button_callback(self, button, interaction):
        # Send a message when the button is clicked
        await interaction.response.send_message(f"{interaction.user.mention}, You clicked the button!")


@bot.slash_command()  # Create a slash command
async def button(ctx):
    # Send a message with our View class that contains the button
    await ctx.respond("This is a button!", view=MyView())


bot.run(TOKEN)
