import discord
from discord.ext import commands


def setup(bot):  # this is called by Pycord to set up the cog
    bot.add_cog(Admin(bot))  # add the cog to the bot


class Admin(commands.Cog):
    admin = discord.SlashCommandGroup('admin', 'administrate bot')

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    async def ac_cogs(self, ctx: discord.AutocompleteContext):
        return list(map(lambda x: x.lower(), self.bot.cogs.keys()))

    @admin.command(name='exit', description='shutdown the application')
    @commands.is_owner()
    async def exit(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"I'm retiring now. See you soon {ctx.guild}' folks!")
        await self.bot.close()

    @admin.command(name='ping', description="Sends the bot latency.")
    async def ping(self, ctx: discord.ApplicationContext):
        latency_ms = int(self.bot.latency * 1000)
        await ctx.respond(f"Pong! Latency is {latency_ms}ms")

    @admin.command(name='reload', description='reload a bot cog')
    @commands.is_owner()
    async def reload_module(self, ctx: discord.ApplicationContext, name: discord.Option(str, autocomplete=ac_cogs)):
        try:
            self.bot.reload_extension(f'cogs.{name}')
            await ctx.respond(f'{name} cog successfully reloaded')
        except (discord.errors.ExtensionNotLoaded, discord.errors.ExtensionNotFound, discord.errors.NoEntryPointError,
                discord.errors.ExtensionFailed, discord.ext.commands.errors.NotOwner) as er:
            await ctx.respond(f'{name} cog not reloaded because:\r\n{er}')

    @reload_module.error
    async def reload_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f'Cannot reload: {error}')
