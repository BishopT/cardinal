# cardinal_bot.py

import os

import discord
from dotenv import load_dotenv
import logging

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

log_file_handler = logging.FileHandler(
    filename="cardinal.log", encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=log_file_handler, level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord and following guilds:')
    for guild in client.guilds:
        print(f'{guild.name} (id: {guild.id})')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hey! Happy to here from you')

    if message.content.startswith('$exit'):
        await message.channel.send("I'm retiring now. See you soon!")
        await client.close()

client.run(TOKEN)
