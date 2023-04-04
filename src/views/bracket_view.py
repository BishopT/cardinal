import re

import discord
from discord.ext import pages

from tournapy.core.ruleset import Ruleset


class BracketView:

    def __init__(self, ruleset: Ruleset):
        self.ruleset = ruleset

    def get_page_items(self, i: int):
        matches = []
        for m in self.ruleset.bracket.values():
            if re.match(f'{i}-', m.id):
                embed = discord.Embed(
                    title=f'{m.id} match',
                    description=f'Match: {m.blue_team} vs {m.red_team}',
                    # Pycord provides a class with default colors you can choose from
                    color=discord.Colour.blue(),
                )
                matches.append(embed)
        return {f'Round {i}', matches}

    def get_page_group(self):
        page_buttons = [
            pages.PaginatorButton("first", label="<<-", style=discord.ButtonStyle.green),
            pages.PaginatorButton("prev", label="<-", style=discord.ButtonStyle.green),
            pages.PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True),
            pages.PaginatorButton("next", label="->", style=discord.ButtonStyle.green),
            pages.PaginatorButton("last", label="->>", style=discord.ButtonStyle.green),
        ]
        print(f'toto')
        for i in range(self.ruleset.bracket_depth):
            print(f'round={i}')
            self.get_page_items(i)
        return pages.PageGroup(
            pages=[
                "Round 1",
                "Round 2",
                "Final!",
            ],
            label=f"{self.ruleset.name}",
            description=f"Pages for {self.ruleset.name} bracket",
            custom_buttons=page_buttons,
            use_default_buttons=False

        )
