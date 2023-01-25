import tournament as t
import team as team
import player as player

tourney = t.Tournament()
tourney.setup("Bishop", "test tournament", 2)

tourney.add_player("Bishop", 1250)
tourney.add_player("WizardsMonkeys", 1350)
tourney.add_player("Zylbyrom", 1200)
tourney.add_player("Nikoalbara", 1150)
# print(tourney.df_players)

tourney.add_team("NiWi", "Nikoalbara", "WizardsMonkeys")
tourney.add_team("ZyBi", "Zylbyrom", "Bishop")

print('')
print('============== TEAMS ====================')
print(tourney.df_teams)
print('')
print('============== PLAYERS ====================')
print(tourney.df_players)
print('')
