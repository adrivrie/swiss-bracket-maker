
import win32clipboard
from classes import *
from copy import deepcopy
import numpy as np
import math

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

def create_bracket(participants) -> list[Matchup]:
    participants_count = len(participants)
    rounds = math.ceil(math.log(participants_count, 2))
    bracket_size = 2 ** rounds
    required_byes = bracket_size - participants_count

    print(f"Number of participants: {participants_count}")
    print(f"Number of rounds: {rounds}")
    print(f"Bracket size: {bracket_size}")
    print(f"Required number of byes: {required_byes}")

    if participants_count < 2:
        return []

    match_seeds = [[1, 2]]

    for round_num in range(1, rounds):
        round_match_seeds = []
        sum_seeds = 2 ** (round_num + 1) + 1

        for match in match_seeds:
            home = change_into_bye(match[0], participants_count)
            away = change_into_bye(sum_seeds - match[0], participants_count)
            round_match_seeds.append([home, away])

            home = change_into_bye(sum_seeds - match[1], participants_count)
            away = change_into_bye(match[1], participants_count)
            round_match_seeds.append([home, away])

        match_seeds = round_match_seeds

    matches = []
    for match in match_seeds:
        p1 = participants[match[0]-1] if match[0] is not None else Player("BYE")
        p2 = participants[match[1]-1] if match[1] is not None else Player("BYE")
        new_match = Matchup(p1, p2)
        matches.append(new_match)

    print(matches)

    return matches


def change_into_bye(seed, participants_count):
    return seed if seed <= participants_count else None


def build_full_bracket_from_first_round(first_round: list[Matchup]) -> list[list[Matchup]]:
    bracket = [first_round]
    total_players = len(first_round) * 2
    total_rounds = int(math.log2(total_players))

    # Build future rounds with empty matches
    for r in range(1, total_rounds):
        matches_in_round = len(bracket[r - 1]) // 2
        next_round = [Matchup(Player(""), Player("")) for _ in range(matches_in_round)]
        bracket.append(next_round)

    return bracket
