import logging
import pickle

import atexit
import discord
from discord.ext.commands import Bot
from discord.ext.commands import MinimalHelpCommand

import utils

logger = logging.getLogger('discord')
logger.setLevel(level=utils.LOG_LEVEL)
log_file_handler = logging.FileHandler(
    filename=utils.LOG_FILE, encoding=utils.LOG_FILE_ENC, mode='w')
logger.addHandler(log_file_handler)


def exit_handler():
    print('Exit catched!')
    with open(utils.TOURNAMENT_DATA_FILE_PATH, 'wb') as file:
        # Pickle the 'data' dictionary using the highest protocol available.
        pickle.dump(bot.cogs['Tournaments'].manager, file, pickle.HIGHEST_PROTOCOL)


atexit.register(exit_handler)

intents = discord.Intents.default()
intents.members = True

bot = Bot(owner_id=utils.OWNER_ID, intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord and following guilds:')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id}):')
        # guild.fetch_members()
        # for channel in guild.text_channels:
        #     # c: discord.TextChannel = await guild.fetch_channel(channel.id)
        #     # print(f'  {c.name}:')
        #     for member in channel.members:
        #         print(f'    {member.name}')


cogs_list = [
    'greetings',
    'admin',
    'tournaments'
]

for cog in cogs_list:
    bot.load_extension(f'cogs.{cog}')

with open(utils.TOURNAMENT_DATA_FILE_PATH, 'rb') as f:
    # The protocol version used is detected automatically, so we do not
    # have to specify it.
    bot.cogs['Tournaments'].manager = pickle.load(f)

bot.help_command = MinimalHelpCommand()
bot.run(utils.TOKEN)
