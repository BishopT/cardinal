import logging

import discord

import utils

logger = logging.getLogger('discord')
logger.setLevel(level=utils.LOG_LEVEL)
log_file_handler = logging.FileHandler(
    filename=utils.LOG_FILE, encoding=utils.LOG_FILE_ENC, mode='w')
logger.addHandler(log_file_handler)
# discord.utils.setup_logging(handler=log_file_handler, level=LOG_LEVEL)

intents = discord.Intents.default()
# intents.message_content = True

bot = discord.Bot(owner_id=utils.OWNER_ID)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord and following guilds:')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id})')


cogs_list = [
    'greetings',
    'admin',
    'tournaments'
]

for cog in cogs_list:
    bot.load_extension(f'cogs.{cog}')

bot.run(utils.TOKEN)
