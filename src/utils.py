
import win32clipboard
from classes import *
from copy import deepcopy
import math
import random
from itertools import combinations
import numpy as np
import networkx as nx

def get_clipboard_data() -> str:
    win32clipboard.OpenClipboard()
    data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    return data

def generate_matchups(players: list[Player]) -> list[Matchup]:
    """
    Generate matchups by maximum weight matching, applying a penalty
    to up and down pairing, and disallowing repeat matchups completely.

    Randomness seeded with the sorted names of players to attempt to
    make it reproducible and non-manipulable.

    TODO: try a faster approach first and use this as fallback
    """

    players_in_round = [player for player in players if not player.dropped]

    #networkx uses both random and numpy.random interchangably
    random.seed("".join([player.clean_name for player in players_in_round]))
    np.random.seed(random.randint(0, 2**32-1))

    random.shuffle(players_in_round)

    integer_scores = assign_integer_scores(players_in_round)

    # create the matchup graph
    player_graph = nx.Graph()
    for player1, player2 in combinations(players_in_round, 2):
        difference = abs(integer_scores[player1] - integer_scores[player2])
        player_graph.add_edge(player1, player2, weight=difference**3)

    # ensure that there's an even number of players by adding a BYE
    if len(players_in_round) % 2:
        for player in players_in_round:
            player_graph.add_edge(player, "BYE", weight=integer_scores[player]**3)

    # find a minimum weight maximum cardinality matching
    matching = nx.min_weight_matching(player_graph)

    matchups: list[Matchup] = []
    for matchup in matching:
        if "BYE" in matchup:
            bye_player = matchup[1] if matchup[0] == "BYE" else matchup[0]
            matchups.append(Matchup(bye_player, None, "BYE"))
            continue
        matchups.append(Matchup(*matchup))

    # put the highest scores first because that's intuitive
    matchups.sort(reverse=True, key=lambda x: (x.player1.score, x.player1.name))
    return matchups

def assign_integer_scores(players: list[Player]) -> dict[int, Player]:
    """
    Assigns ordinal integer scores to the players,
    as float scores are supported by the scoring system
    but not (properly) by the graph algorithms.
    """

    player_integers = {}
    players = sorted(players, key=lambda x: x.score)
    score = players[0].score
    integer_score = 0
    for player in players:
        if not math.isclose(player.score, score):
            integer_score += 1
        score = player.score
        player_integers[player] = integer_score
    return player_integers

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


# TODO: Future work. Create full interactive bracket page
# def build_full_bracket_from_first_round(first_round: list[Matchup]) -> list[list[Matchup]]:
#     bracket = [first_round]
#     total_players = len(first_round) * 2
#     total_rounds = int(math.log2(total_players))

#     # Build future rounds with empty matches
#     for r in range(1, total_rounds):
#         matches_in_round = len(bracket[r - 1]) // 2
#         next_round = [Matchup(Player(""), Player("")) for _ in range(matches_in_round)]
#         bracket.append(next_round)

#     return bracket
