import discord
from discord.ext import commands


def setup(bot):  # this is called by Pycord to set up the cog
    bot.add_cog(Greetings(bot))  # add the cog to the bot


class Greetings(commands.Cog):
    greetings = discord.SlashCommandGroup("greetings", "Greet people")

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @greetings.command(name='hello', description='Be polite, come say hi :)')
    async def hello(self, ctx: discord.ApplicationContext):
        # user: discord.User = ctx.Author
        await ctx.respond(f'Hey! Happy to see you there {ctx.user.mention}')

    @greetings.command(name='bye', description='let me know you leave for now')
    async def bye(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"Good Bye, {ctx.user.mention}! I hope I'll see you again soon")
