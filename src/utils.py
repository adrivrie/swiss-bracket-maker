
from collections import defaultdict
import time
import win32clipboard
from classes import *
import math
import random
from itertools import combinations
import numpy as np
import networkx as nx

from settings import SettingsDialog

def get_clipboard_data() -> str:
    win32clipboard.OpenClipboard()
    data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    return data

def generate_matchups(players: list[Player], rounds: list[Round], settings: SettingsDialog) -> list[Matchup]:
    """
    Generate matchups by maximum weight matching, applying a penalty
    to up and down pairing, and disallowing repeat matchups completely.

    Randomness seeded with the sorted names of players and round number
    to attempt to make it reproducible and non-manipulable.

    TODO: try a faster approach first and use this as fallback
    """
    start = time.time()



    print("Calculating necessary stats")
    player_info_list = calculate_players_stats(players, rounds)
    player_info_list_in_round = [player for player in player_info_list if not player.player.dropped]

    # setting seed for both random and np.random as
    # networkx uses both random and numpy.random interchangably
    seed = "".join([player.player.name for player in player_info_list_in_round])
    seed += str(len(rounds))
    random.seed(seed)
    np.random.seed(random.randint(0, 2**32-1))

    # get scores incorporating randomly assigning delayed games' winners
    player_info_effective_scores = get_scores_for_round_generation(player_info_list_in_round, rounds, settings)


    random.shuffle(player_info_list_in_round)

    integer_scores = assign_integer_scores(player_info_effective_scores)

    # create the matchup graph
    player_graph = nx.Graph()
    # first gather all matchups that already happened, because those can't happen again
    already_played = set()
    for round in rounds:
        for matchup in round.matchups:
            already_played.add((matchup.player1, matchup.player2))
            already_played.add((matchup.player2, matchup.player1))

    for playerinfo1, playerinfo2 in combinations(player_info_list_in_round, 2):
        # add their edge and assign a weight based on their score difference
        difference = abs(integer_scores[playerinfo1] - integer_scores[playerinfo2])
        # make sure that these players have not played before
        if (playerinfo1.player.name, playerinfo2.player.name) in already_played:
            difference += 10
        # weight by double cubed score difference, and a small penalty term if
        # it's a repeat mispairing
        weight = 2 * difference**3
        if weight:
            weight += playerinfo1.mispairings + playerinfo2.mispairings
        player_graph.add_edge(playerinfo1, playerinfo2, weight=weight)

    # ensure that there's an even number of players by adding a BYE
    if len(player_info_list_in_round) % 2:
        for player_info in player_info_list_in_round:
            # also check if this player hasn't had a bye before
            if (None, player_info.player.name) in already_played:
                weight = (10 + integer_scores[player_info])**3
            else:
                weight = integer_scores[player_info]**3
            player_graph.add_edge(player_info, "BYE", weight=weight)

    # find a minimum weight maximum cardinality matching
    print("Finding optimal matching")
    matching = nx.min_weight_matching(player_graph)

    # sort by score because that's nice
    def _get_match_score_for_sorting(match: tuple[PlayerInfo|str]):
        if "BYE" in match:
            return (0, "", "")
        else:
            score = match[0].score + match[1].score + 0.5 * (match[0].active_delays + match[1].active_delays)
            return (-score, match[0].player.name, match[1].player.name)

    # first score, then alphabetical
    matching = sorted(matching, key=_get_match_score_for_sorting)

    matchups: list[Matchup] = []
    for matchup in matching:
        if "BYE" in matchup:
            bye_player = matchup[1] if matchup[0] == "BYE" else matchup[0]
            matchups.append(Matchup(bye_player.player.name, None, "BYE"))
            continue
        matchups.append(Matchup(matchup[0].player.name, matchup[1].player.name))
    print(f"Matchup generation took {time.time() - start} seconds")
    return matchups

def get_scores_for_round_generation(player_info_list: list[PlayerInfo], rounds: list[Round], settings: SettingsDialog) -> dict[PlayerInfo, float]:
    """
    Calculates the score or each player to be used in round generation.
    Specifically, effective score is the sum of scores over all games for each player
    plus each delayed game gives one point to one player at random.

    This has the effect of intentionally delayed games not being beneficial
    usually, though this cannot be prevented entirely.
    """

    delay_points = defaultdict(int)
    for round in rounds:
        for match in round.matchups:
            if match.winner == "Delayed":
                # If we allow random point assignment and flip a coin invert the points
                if settings.random_assignment_checkbox and random.random() > 0.5:
                    delay_points[match.player1] += settings.p2_ext_point
                    delay_points[match.player2] += settings.p1_ext_point
                else:
                    delay_points[match.player1] += settings.p1_ext_point
                    delay_points[match.player2] += settings.p2_ext_point

    effective_scores = {}
    for player_info in player_info_list:
        effective_scores[player_info] = player_info.score + delay_points[player_info.player.name]
    return effective_scores


def assign_integer_scores(player_info_effective_scores: dict[PlayerInfo, float]) -> dict[PlayerInfo, int]:
    """
    Assigns ordinal integer scores to the players,
    as float scores are supported by the scoring system
    but not (properly) by the graph algorithms.
    """

    player_info_integers = {}
    integer_score = 0
    score = 0
    for player_info, player_score in sorted(player_info_effective_scores.items(), key=lambda x: x[1]):
        if not math.isclose(player_score, score):
            integer_score += 1
        score = player_score
        player_info_integers[player_info] = integer_score
    return player_info_integers


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
    for round in rounds:
        for matchup in round.matchups:
            # if not a bye matchup
            if matchup.player2:
                was_mispairing = player_info_dict[matchup.player2].score != player_info_dict[matchup.player1].score
                if was_mispairing:
                    player_info_dict[matchup.player1].mispairings += 1
                    player_info_dict[matchup.player2].mispairings += 1

                player_info_dict[matchup.player2].score += matchup.score_player2
                player_info_dict[matchup.player2].n_played += 1
                player_info_dict[matchup.player2].n_wins += matchup.winner == matchup.player2
                player_info_dict[matchup.player2].active_delays += matchup.winner == "Delayed"

            player_info_dict[matchup.player1].score += matchup.score_player1
            player_info_dict[matchup.player1].n_played += 1
            player_info_dict[matchup.player1].n_wins += matchup.winner == matchup.player1
            player_info_dict[matchup.player1].active_delays += matchup.winner == "Delayed"

    # resistance
    for round in rounds:
        for matchup in round.matchups:
            if not matchup.player2: # BYE
                continue
            p1 = matchup.player1
            p2 = matchup.player2
            # add opponent's score to resistance
            player_info_dict[p1].resistance += player_info_dict[p2].score
            player_info_dict[p2].resistance += player_info_dict[p1].score


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
