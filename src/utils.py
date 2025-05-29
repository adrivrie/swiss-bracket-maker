
import win32clipboard
from classes import *
from copy import deepcopy
import numpy as np

def get_clipboard_data() -> str:
    win32clipboard.OpenClipboard()
    data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    return data

def generate_matchups(players: list[Player]) -> list[Matchup]:
    from random import shuffle

    players_copy = []
    for p in players:
        if not p.dropped:
            players_copy.append(deepcopy(p))

    shuffle(players_copy)
    for player in players_copy:
        if player.dropped:
            players_copy.remove(player)
    matchups = []
    while len(players_copy) >=2:
        p1, p2 = np.random.choice(players_copy, size=2, replace=False)
        players_copy.remove(p1)
        players_copy.remove(p2)

        new_matchup = Matchup(get_player_by_name(players, p1.name), get_player_by_name(players, p2.name))
        matchups.append(new_matchup)

    if len(players_copy) == 1:
        # bye matchup
        lucky_player = players_copy[0]
        lucky_player = get_player_by_name(players, lucky_player.name)
        new_matchup = Matchup(lucky_player, None, "BYE")
        matchups.append(new_matchup)
    
    return matchups


def get_player_by_name(players: list[Player], name: str) -> Player:
    for player in players:
        if player.name == name:
            return player


def get_matchup_by_player(matchups: list[Matchup], player: Player) -> Matchup:
    for matchup in matchups:
        # cannot check on player object because of deepcopy when making matchups
        if matchup.player1 == player or matchup.player2 == player:
            return matchup
