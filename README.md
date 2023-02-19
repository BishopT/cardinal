# cardinal

discord bot to create, manage and run tournaments right into guilds 

written in python with [Pycord](https://pycord.dev/)

## run

Register your bot in discord developer portal to generate a token.

create a .env file with

```text
DISCORD_TOKEN=<your discord bot token>
CARDINAL_CONF=path/to/cardinal.ini
```

`python src/cardinal_bot.py`

## Usage

Start by creating tournament by using slash command `/tournament create`

One a tournament is created, some actions are available directly from UI (e.g. buttons)

For all others action search for slash commands in `/tournament`
