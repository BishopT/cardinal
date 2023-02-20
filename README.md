# Cardinal

discord bot to create, manage and run tournaments right into guilds

written in python with [Pycord](https://pycord.dev/)

## Dependencies

- python 3.8 or above
- pandas
- pycord
- [tournapy](https://github.com/BishopT/tournapy)

## Run

Register your bot in discord developer portal to generate a token.

create a .env file with

```text
DISCORD_TOKEN=<your discord bot token>
CARDINAL_CONF=path/to/cardinal.ini
```

change the `OwnerId` value to your discord ID so that you own the bot instance

run `python src/cardinal_bot.py`

## Usage

Start by creating tournament by using slash command `/tournaments create`

One a tournament is created, some actions are available directly from UI (e.g. buttons)

For all others action search for slash commands in `/tournaments`
