
import time
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
    start = time.time()
    print("Calculating necessary stats")
    player_info_list = calculate_players_stats(players, rounds)

    player_info_list_in_round = [player for player in player_info_list if not player.player.dropped]

    # networkx uses both random and numpy.random interchangably
    random.seed("".join([player.player.name for player in player_info_list_in_round]))
    np.random.seed(random.randint(0, 2**32-1))

    random.shuffle(player_info_list_in_round)

    integer_scores = assign_integer_scores(player_info_list_in_round)

    # create the matchup graph
    player_graph = nx.Graph()
    # first gather all matchups that already happened, because those can't happen again
    already_played = set()
    for round in rounds:
        for matchup in round.matchups:
            already_played.add((matchup.player1, matchup.player2))
            already_played.add((matchup.player2, matchup.player1))

    for playerinfo1, playerinfo2 in combinations(player_info_list_in_round, 2):
        # make sure that these players have not played before
        if (playerinfo1.player.name, playerinfo2.player.name) in already_played:
            continue
        # then add their edge and assign a weight based on their score difference
        difference = abs(integer_scores[playerinfo1] - integer_scores[playerinfo2])
        player_graph.add_edge(playerinfo1, playerinfo2, weight=difference**3)

    # ensure that there's an even number of players by adding a BYE
    if len(player_info_list_in_round) % 2:
        for player_info in player_info_list_in_round:
            # also check if this player hasn't had a bye before
            if (None, player_info.player.name) not in already_played:
                player_graph.add_edge(player_info, "BYE", weight=integer_scores[player_info]**3)

    # find a minimum weight maximum cardinality matching
    print("Finding optimal matching")
    matching = nx.min_weight_matching(player_graph)

    # TODO: Check if bracket is appropriate size and use fallback otherwise
    # Should only be a problem if number of rounds approaches number of players
    # but I have not been able to prove a lower bound (I think it might be half)

    matchups: list[Matchup] = []
    for matchup in matching:
        if "BYE" in matchup:
            bye_player = matchup[1] if matchup[0] == "BYE" else matchup[0]
            matchups.append(Matchup(bye_player.player.name, None, "BYE"))
            continue
        matchups.append(Matchup(matchup[0].player.name, matchup[1].player.name))
    print(f"Matchup generation took {time.time() - start} seconds")
    return matchups

def assign_integer_scores(player_info_list: list[PlayerInfo]) -> dict[PlayerInfo, int]:
    """
    Assigns ordinal integer scores to the players,
    as float scores are supported by the scoring system
    but not (properly) by the graph algorithms.
    """

    player_info_integers = {}
    # we count to-be-played games as half a point
    player_info_list = sorted(player_info_list, key=lambda x: x.score + 0.5 * x.active_delays)
    score = player_info_list[0].score + 0.5 * player_info_list[0].active_delays
    integer_score = 0
    for player_info in player_info_list:
        if not math.isclose(player_info.score + 0.5 * player_info.active_delays, score):
            integer_score += 1
        score = player_info.score + 0.5 * player_info.active_delays
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

def create_bracket(participants: list[PlayerInfo]) -> list[Matchup]:
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
        p1 = participants[match[0]-1].player.name if match[0] is not None else "BYE"
        p2 = participants[match[1]-1].player.name if match[1] is not None else "BYE"
        new_match = Matchup(p1, p2)
        matches.append(new_match)

    print(matches)

    return matches


def change_into_bye(seed, participants_count):
    return seed if seed <= participants_count else None


def calculate_players_stats(players: list[Player], rounds: list[Round], as_dict: bool = False) -> list[PlayerInfo]:
    player_info_dict: dict[str, PlayerInfo] = {}
    for player in players:
        player_info_dict[player.name] = PlayerInfo(player)

    # Scores
    for r in rounds:
        for matchup in r.matchups:
            player_info_dict[matchup.player1].score += matchup.score_player1
            player_info_dict[matchup.player1].n_played += 1
            player_info_dict[matchup.player1].n_wins += matchup.winner == matchup.player1
            player_info_dict[matchup.player1].active_delays += matchup.winner == "Delayed"

            if matchup.player2:
                player_info_dict[matchup.player2].score += matchup.score_player2
                player_info_dict[matchup.player2].n_played += 1
                player_info_dict[matchup.player2].n_wins += matchup.winner == matchup.player2
                player_info_dict[matchup.player2].active_delays += matchup.winner == "Delayed"

    # Win% and resistance
    for r in rounds:
        pass

    if as_dict:
        return player_info_dict
    return list(player_info_dict.values())




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
