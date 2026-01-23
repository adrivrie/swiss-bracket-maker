
import win32clipboard
from classes import *
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

def generate_matchups(players: list[Player], rounds: list[Round]) -> list[Matchup]:
    """
    Generate matchups by maximum weight matching, applying a penalty
    to up and down pairing, and disallowing repeat matchups completely.

    Randomness seeded with the sorted names of players to attempt to
    make it reproducible and non-manipulable.

    TODO: try a faster approach first and use this as fallback
    """

    player_info_list = calculate_players_stats(players, rounds)

    player_info_list_in_round = [player for player in player_info_list if not player.player.dropped]

    # networkx uses both random and numpy.random interchangably
    random.seed("".join([player.player.name for player in player_info_list_in_round]))
    np.random.seed(random.randint(0, 2**32-1))

    random.shuffle(player_info_list_in_round)

    integer_scores = assign_integer_scores(player_info_list_in_round)

    # create the matchup graph
    player_graph = nx.Graph()
    for player1, player2 in combinations(player_info_list_in_round, 2):
        # first make sure that these players have not played before
        # TODO: use rounds instead of player matches
        # for p1_mu in player1.matches:
        #     if player2 in [p1_mu.player1, p1_mu.player2]:
        #         break
        # then add their edge and assign a weight based on their score difference
        # else:
        difference = abs(integer_scores[player1] - integer_scores[player2])
        player_graph.add_edge(player1, player2, weight=difference**3)

    # ensure that there's an even number of players by adding a BYE
    if len(player_info_list_in_round) % 2:
        for player_info in player_info_list_in_round:
            # also check if this player hasn't had a bye before
            # TODO: check
            # if None not in [mu.player2 for mu in player.matches]:
            player_graph.add_edge(player_info, "BYE", weight=integer_scores[player_info]**3)

    # find a minimum weight maximum cardinality matching
    matching = nx.min_weight_matching(player_graph)

    matchups: list[Matchup] = []
    for matchup in matching:
        if "BYE" in matchup:
            bye_player = matchup[1] if matchup[0] == "BYE" else matchup[0]
            matchups.append(Matchup(bye_player.player.name, None, "BYE"))
            continue
        matchups.append(Matchup(matchup[0].player.name, matchup[1].player.name))

    # put the highest scores first because that's intuitive
    # matchups.sort(reverse=True, key=lambda x: (x.player1.score, x.player1.name))
    return matchups

def assign_integer_scores(player_info_list: list[PlayerInfo]) -> dict[PlayerInfo, int]:
    """
    Assigns ordinal integer scores to the players,
    as float scores are supported by the scoring system
    but not (properly) by the graph algorithms.
    """

    player_info_integers = {}
    player_info_list = sorted(player_info_list, key=lambda x: x.score)
    score = player_info_list[0].score
    integer_score = 0
    for player_info in player_info_list:
        if not math.isclose(player_info.score, score):
            integer_score += 1
        score = player_info.score
        player_info_integers[player_info] = integer_score
    return player_info_integers

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

def calculate_players_stats(players: list[Player], rounds: list[Round]) -> list[PlayerInfo]:
    player_info_dict: dict[str, PlayerInfo] = {}
    for player in players:
        player_info_dict[player.name] = PlayerInfo(player)

    # Scores
    for r in rounds:
        for matchup in r.matchups:
            player_info_dict[matchup.player1].score += matchup.score_player1
            player_info_dict[matchup.player1].n_played += 1
            player_info_dict[matchup.player1].n_wins += matchup.winner == matchup.player1
            
            if matchup.player2:
                player_info_dict[matchup.player2].score += matchup.score_player2
                player_info_dict[matchup.player2].n_played += 1
                player_info_dict[matchup.player2].n_wins += matchup.winner == matchup.player2

    # Win% and resistance
    for r in rounds:
        pass

    return list(player_info_dict.values())

    


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
