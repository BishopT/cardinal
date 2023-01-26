import tournament as t
import ruleset
import team as team
import player as player

import simple_elimination as se

import json
import json_patch

tourney = t.Tournament()
tourney.setup("Bishop", "test tournament", 2)

tourney.add_phase(se.SimpleElimination(16))

tourney.add_player("Bishop", 1250)
tourney.add_player("Zylbyrom", 1200)
tourney.add_to_team("ZyBi", "Zylbyrom", "Bishop")

tourney.add_player("Nikoalbara", 1150)
tourney.add_player("WizardsMonkeys", 1350)
tourney.add_to_team("NiWi", "Nikoalbara", "WizardsMonkeys")

tourney.add_player("D-nar", 1250)
tourney.add_player("killer", 1350)
tourney.add_to_team("D-Kil", "D-nar", "killer")

tourney.add_player("xav", 1200)
tourney.add_player("lefou", 1150)
tourney.add_to_team("Lexav", "xav", "lefou")

tourney.add_player("centice", 1250)
tourney.add_player("ragnarok", 1350)
tourney.add_to_team("Race", "centice", "ragnarok")

tourney.add_player("nexto", 1250)
tourney.add_player("necto", 1350)
tourney.add_to_team("NexNec", "nexto", "necto")

tourney.add_player("kaydop", 1200)
tourney.add_player("fairy", 1150)
tourney.add_to_team("kafai", "kaydop", "fairy")

tourney.add_player("furious", 1200)
tourney.add_player("karma", 1150)
tourney.add_to_team("fuka", "furious", "karma")

# print(tourney.df_players)

print('')
print('============== TEAMS ====================')
print(tourney.df_teams())
print('')
print('============== PLAYERS ====================')
print(tourney.df_players())
print('')

tourney.init()
bracket = tourney.get_phase(1).init_bracket(1)
print(json.dumps(bracket, indent=4))
print(tourney.get_phase(1).get_standings())
