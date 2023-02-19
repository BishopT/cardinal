import atexit
import logging

import discord

import utils

logger = logging.getLogger('discord')
logger.setLevel(level=utils.LOG_LEVEL)
log_file_handler = logging.FileHandler(
    filename=utils.LOG_FILE, encoding=utils.LOG_FILE_ENC, mode='w')
logger.addHandler(log_file_handler)


# discord.utils.setup_logging(handler=log_file_handler, level=LOG_LEVEL)

def exit_handler():
    print('Exit catched!')


atexit.register(exit_handler)

intents = discord.Intents.default()
intents.members = True

bot = discord.Bot(owner_id=utils.OWNER_ID, intents=intents)


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

# bot.help_command = SupremeHelpCommand()
bot.run(utils.TOKEN)
