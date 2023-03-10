from tournapy.core.ruleset import RulesetEnum
from tournapy.tournament import Tournament

tourney = Tournament()
tourney.setup("Bishop", "test tournament", 2)

tourney.add_phase(0, RulesetEnum.SIMPLE_ELIMINATION.get_ruleset("playoff", 16, 3))

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
tourney.add_player("WizardsMonkeys", 1350)
tourney.add_to_team("NexWiz", "nexto", "WizardsMonkeys")

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

# tourney.init()
qualif = tourney.get_current_phase()
teams_names = tourney.df_teams()['name']
for team_name in teams_names:
    # next_phase.add_team(t.get_team(team_name))
    qualif.add_team(tourney.teams_dict[team_name])
bracket = qualif.init_bracket()
print('============== BRACKET ====================')
print(tourney.get_current_phase().get_bracket())
print('')
print(tourney.get_current_phase().get_standings())

phase = tourney.get_current_phase()
phase.start()

m = phase.next_match('Lexav')
phase.report_match_result(m, (5, 3), (4, 6), (2, 1))
print('============== STANDINGS ====================')
print(tourney.get_current_phase().get_standings())
print('')
print('============== BRACKET ====================')
print(tourney.get_current_phase().get_bracket())
print('')

m = phase.next_match('fuka')
phase.report_match_result(m, (1, 2), (3, 2), (4, 1))

m = phase.next_match('NiWi')
phase.report_match_result(m, (0, 8), (6, 1), (5, 6))
print('')

m = phase.next_match('NexWiz')
phase.report_match_result(m, (8, 2), (4, 9), (4, 10))
print('')

# END OF FIRST ROUND

print('============== BRACKET ====================')
print(tourney.get_current_phase().get_bracket())
print('')

print('============== STANDINGS ====================')
print(tourney.get_current_phase().get_standings())
print('')

m = phase.next_match('Lexav')
print(m)
phase.report_match_result(m, (2, 9), (0, 5))
print('')

m = phase.next_match('kafai')
phase.report_match_result(m, (8, 4), (2, 8), (7, 1))
print('')

m = phase.next_match('kafai')
phase.report_match_result(m, (8, 1), (5, 9), (4, 9))
print('')

print('============== STANDINGS ====================')
print(tourney.get_current_phase().get_standings())
print('')
print('============== BRACKET ====================')
print(tourney.get_current_phase().get_bracket())
print('')

print('============== MATCH HISTORY ====================')
print(tourney.get_current_phase().get_history())
print('')
