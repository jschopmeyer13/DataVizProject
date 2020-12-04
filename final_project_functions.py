import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from collections import Counter



## NOTES

# within playDescription (name) means defense of pass while [name] means rushing quarterback
OFFENSE = ['QB', 'RB', 'WR', 'TE', 'FB']

'''
def group_by_keyword(keyword, games, plays):
	names = []
	df_int = plays[plays.playDescription.str.contains(keyword)][['playDescription','possessionTeam', 'gameId']]
	df_merge = pd.merge(df_int, games[['gameId', 'homeTeamAbbr', 'visitorTeamAbbr']], how='inner', on='gameId')
	for row in df_merge.itertuples():
		home = getattr(row, "homeTeamAbbr")
	    away = getattr(row, "visitorTeamAbbr")
	    descript = getattr(row, "playDescription")
	    possession = getattr(row, 'possessionTeam')

	    defense = home if away == possession else away
	    start = descript.index(keyword) + len(keyword)
	    # start = descript.index("{}".format(keyword)) + len("{}".format(keyword))
	#         end  = descript.index(" at ")
	    end = start+20
	    name = descript[start:end]
	    if "(" in name:
	        name= name[0:name.index("(")-1]
	    elif "[" in name:
	        name= name[0:name.index("[")-1]     

	#     name = name[0: min(name.index("("), name.index("["))]
	    names.append((name, defense))
	return names
'''

def fix_height(row):
	output = 0.0
	if "-" in row:
		vals = row.split("-")
		output = 12*int(vals[0]) + int(vals[1])
	else:
		output = int(row)
	return output



def clean_description(row, keyword):
	"""
	Parses out just the name based on keyword
	*only has been tested with INTERCEPT by
	"""
	start = row.index(keyword) + len(keyword)
	word = row[start:]
	word = word[:word.index(" ")]
	return word

def shorten(name):
	"""
	Shortens full name to use to compare and group
	"""
	first_last = name.split(" ")
	short = first_last[0][0] + "."
	short+="".join(first_last[1:])
	return short

def get_team(row):
	poss = getattr(row, 'possessionTeam')
	home = getattr(row, "homeTeamAbbr")
	away = getattr(row, "visitorTeamAbbr")
	# print(row)
	return away if poss==home else home


def organize_by(keyword,event_word, plays, games, week, players, week_number):
	"""
	Gets only players related to the chose keyword
	"""

	if keyword==None:
		df_plays = plays[['playDescription','possessionTeam', 'gameId','playId']]
	else:
		plays = plays[plays.passResult == "IN"] # ! Getting only passes ruled interceptions
		df_plays = plays[plays.playDescription.str.contains(keyword)][['playDescription','possessionTeam', 'gameId','playId']]

	
	df_merge_games = pd.merge(df_plays, games[['gameId', 'homeTeamAbbr', 'visitorTeamAbbr','week']], how='inner', on='gameId')

	print(df_merge_games.shape)

	df_merge_week = pd.merge(df_merge_games, week[['gameId', 'playId','nflId', 'displayName', 'event', 'x','y', 'frameId', 'week', 'position']], on=['gameId', 'playId', 'week'])
	# getting only defensive players
	df_defense = df_merge_week[~df_merge_week.position.isin(OFFENSE)]
	# only look at frames with interception
	df_defense = df_defense[df_defense.event == event_word]

	df_defense['shorten_name'] = df_defense.displayName.apply(lambda row: shorten(row))


	if keyword:
		df_defense['playDescription'] = df_defense['playDescription'].apply(lambda row: clean_description(row, keyword))

	df_defense['team'] = df_defense[['possessionTeam', 'homeTeamAbbr', 'visitorTeamAbbr']].apply(lambda row: get_team(row), axis=1)
	
	if keyword == None:
		return df_defense
	else:
		return df_defense[df_defense.playDescription == df_defense.shorten_name]
	 

def get_defender(row):
	descript = getattr(row, "playDescription")
	name = getattr(row, "shorten_name")

	words = descript[descript.index('incomplete'):]
	output = []
	if "(" in words:
		words = words[words.index("(")+1:words.index(")")]

	if ',' in words:
		words= words.split(', ')
	else:
		words = [words]

	if name in words:
		return True
	else:
		return np.nan

def defense_on_throw(keyword,event_word, plays, games, week, players, week_number):
	"""
	Looking for who pass is incomplete to. Then looking for the closest defender to the offensive player and in comparison to the ball.
	"""

	# gets all confirmed incomplete passes
	plays = plays[plays.passResult == "I"]
	if keyword==None:
		df_plays = plays[['playDescription','possessionTeam', 'gameId','playId']]
	else:
		df_plays = plays[plays.playDescription.str.contains(keyword)][['playDescription','possessionTeam', 'gameId','playId']]
	
	df_merge_games = pd.merge(df_plays, games[['gameId', 'homeTeamAbbr', 'visitorTeamAbbr','week']], how='inner', on='gameId')

	df_merge_week = pd.merge(df_merge_games, week[['gameId', 'playId','nflId', 'displayName', 'event', 'x','y', 'frameId', 'week', 'position']], on=['gameId', 'playId', 'week'])
	# getting only defensive players
	df_defense = df_merge_week[~df_merge_week.position.isin(['QB'])]
	# only look at frames with interception
	df_defense = df_defense[df_defense.event == event_word]
	df_defense['team'] = df_defense[['possessionTeam', 'homeTeamAbbr', 'visitorTeamAbbr']].apply(lambda row: get_team(row), axis=1)

	df_defense['shorten_name'] = df_defense.displayName.apply(lambda row: shorten(row))
	df_defense['defenders'] = df_defense[['playDescription', 'shorten_name']].apply(lambda row: get_defender(row), axis=1)

	return df_defense.dropna()


def coverage_stats(df_match, col1='personnelO', col2='personnelD', comp='epa'):
	# coverage_cols = ['gameId', 'playId', 'playDescription',
	# 	'offenseFormation', 'personnelO', 'defendersInTheBox',
	# 	'numberOfPassRushers', 'personnelD', 'typeDropback',
	# 	'passResult', 'offensePlayResult', 'playResult', 'epa']
	# df_match = plays[coverage_cols]

	comp_columns = [col1, col2, comp]

	df_fair = df_match[df_match.playResult == df_match.offensePlayResult]

	df_epa_avg = df_fair[comp_columns].groupby(by=[col1,col2], as_index=False).mean()
	comp_avg = comp+"_avg"
	df_epa_avg = df_epa_avg.rename(columns={comp: comp_avg})

	df_epa_count = df_fair[comp_columns].groupby(by=[col1, col2], as_index=False).count()
	comp_count = comp+"_count"
	
	df_epa_count = df_epa_count.rename(columns={comp:comp_count})

	df_epa_merge = pd.merge(df_epa_avg, df_epa_count, how='inner', on=[col1, col2])
	df_epa_merge = df_epa_merge[~df_epa_merge[col1].str.contains("LS")]
	df_epa_merge = df_epa_merge[df_epa_merge[comp_count] > 20] # getting only signficant comparisons

	df2 = df_epa_merge.reset_index()
	df_top_min = df2.loc[df2[[col1, comp_avg]].groupby(col1).idxmin()[comp_avg]]
	return df_top_min.loc[:,~df_top_min.columns.isin([comp_count,'index'])].sort_values(comp_avg)



# Graphing 

def get_value(idx, column, players):
	# print(column)
	return players[players.nflId == idx][column].tolist()[0]


def get_xy(data, column, players):
	# print(column)
	x_vals = []
	y_vals = []
	for k, v in dict(data.nflId.value_counts()).items():
		x_vals.append(get_value(k, column, players))
		y_vals.append(v)
	return x_vals, y_vals

def get_college(data, column, players):
	# print(column)
	x_vals = []
	d = {}
	y_vals = []
	for k, v in dict(data.nflId.value_counts()).items():
		temp = get_value(k, column, players)
		if temp in d:
			d[temp] +=v
		else:
			d[temp] = v
	return sorted(d.items(), key=lambda pair: pair[1], reverse=False)





##----------DEPRECATED--------------


def clean_keyword(names):
	name_team = []
	all_info = []

	for i in names:
		name = i[0]
		if " at " in name:
			loc = name.index(" at ")

			name = name[:loc]
		name_team.append((name, i[1]))

	return name_team


def count_sort(values, dt = False):
	if not dt:
		return sorted(dict(Counter(values)).items(), key=lambda pair:pair[1], reverse=True)
	else:
		return {k:v for k, v in sorted(dict(Counter(values)).items(), key=lambda pair:pair[1], reverse=True)}

def get_columns(plays, games, week, player):
	print(plays.columns)
	print(games.columns)
	print(week.columns)
	print(player.columns)