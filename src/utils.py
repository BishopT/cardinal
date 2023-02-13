import configparser
import logging
import os

import discord
from dotenv import load_dotenv

# MAGIC_VALUES
# .env
ENV_VAR_DISCORD_TOKEN = 'DISCORD_TOKEN'
ENV_VAR_CONFIG_FILE = 'CARDINAL_CONF'
ENV_VAR_CONFIG_FILE_DEFAULT = 'cardinal.ini'
# .ini
CONF_SECTION_BOT = 'Bot'
CONF_PROP_OWNER = 'OwnerId'
# CONF_PROP_BOT_CMD_PREFIX = 'CommandPrefix'
# CONF_PROP_BOT_CMD_PREFIX_DEFAULT = '/'
CONF_SECTION_LOGGING = 'Log'
CONF_PROP_LOG_FILE = 'LogFile'
# CONF_PROP_LOG_FILE_DEFAULT = 'cardinal.log'
CONF_PROP_LOG_FILE_ENC = 'LogFileEncoding'
# CONF_PROP_LOG_FILE_ENC_DEFAULT = 'utf-8'
CONF_PROP_LOG_LEVEL = 'LogLevel'
# CONF_PROP_LOG_LEVEL_DEFAULT = 'INFO'

# load environment variables
load_dotenv()
TOKEN = os.getenv(ENV_VAR_DISCORD_TOKEN)
CONFIG_FILE = os.getenv(ENV_VAR_CONFIG_FILE, ENV_VAR_CONFIG_FILE_DEFAULT)

# load configuration
conf = configparser.ConfigParser()
conf.read(CONFIG_FILE)

# bot section
OWNER_ID = int(conf.get(CONF_SECTION_BOT, CONF_PROP_OWNER))
# BOT_CMD_PREFIX = conf.get(CONF_SECTION_BOT, CONF_PROP_BOT_CMD_PREFIX)
# logging section
LOG_FILE = conf.get(CONF_SECTION_LOGGING, CONF_PROP_LOG_FILE)
LOG_FILE_ENC = conf.get(CONF_SECTION_LOGGING, CONF_PROP_LOG_FILE_ENC)
LOG_LEVEL = logging.getLevelName(
    conf.get(CONF_SECTION_LOGGING, CONF_PROP_LOG_LEVEL))


def is_owner(ctx: discord.ApplicationContext):
    return ctx.user.id == OWNER_ID
