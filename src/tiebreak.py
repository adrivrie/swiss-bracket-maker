from collections import defaultdict

from classes import PlayerInfo, Round


def calculate_tiebreak(
    rounds: list[Round], player_info_dict: dict[str, PlayerInfo], method: int
) -> defaultdict[str, float]:
    if method == 1:
        print("Calculating tiebreak with the Buchholz system")
        return buchholz(rounds, player_info_dict)
    elif method == 2:
        print("Calculating tiebreak as resistance")
        return resistance(rounds, player_info_dict, False)
    elif method == 3:
        print("Calculating tiebreak as resistance with opponent's resistance")
        return resistance(rounds, player_info_dict, True)
    elif method == 4:
        print("Calculating tiebreak as resistance with opponent's resistance")
        return sonneborn_berger(rounds, player_info_dict)
    print("Resistance method not recognized, using Buchholz")
    return buchholz(rounds, player_info_dict)


def buchholz(rounds: list[Round], player_info_dict: dict[str, PlayerInfo]):
    """
    Sum of opponent's scores with outliers taken out.
    https://en.wikipedia.org/wiki/Tie-breaking_in_Swiss-system_tournaments#Median_/_Buchholz_/_Solkoff
    """
    opponents_scores = defaultdict(list)
    for round in rounds:
        for matchup in round.matchups:
            if not matchup.player2:  # BYE
                opponents_scores[matchup.player1].append(0)
                continue
            p1 = matchup.player1
            p2 = matchup.player2

            opponents_scores[p1].append(player_info_dict[p2].score)
            opponents_scores[p2].append(player_info_dict[p1].score)

    n_rounds = len(rounds)
    result = defaultdict(int)
    for player, scorelist in opponents_scores.items():
        if len(scorelist) < n_rounds:
            scorelist += [0] * (n_rounds - len(scorelist))
        scorelist.sort()
        if n_rounds < 3:
            result[player] = sum(scorelist)
        elif n_rounds < 9:
            result[player] = sum(scorelist[1:-1])
        else:
            result[player] = sum(scorelist[2:-2])
    return result

def sonneborn_berger(rounds: list[Round], player_info_dict: dict[str, PlayerInfo]):
    """
    Sum of opponent's scores multiplied by a player's scores against said opponent.
    https://en.wikipedia.org/wiki/Tie-breaking_in_Swiss-system_tournaments#Sonneborn%E2%80%93Berger_score
    """
    sb_scores = defaultdict(int)
    for round in rounds:
        for matchup in round.matchups:
            if not matchup.player2:  # BYE
                continue
            p1 = matchup.player1
            p2 = matchup.player2
            sb_scores[p1] += (player_info_dict[p2].score) * matchup.score_player1
            sb_scores[p2] += (player_info_dict[p1].score) * matchup.score_player2

    return sb_scores


def resistance(
    rounds: list[Round],
    player_info_dict: dict[str, PlayerInfo],
    include_opponents: False,
):
    """
    Opponents' winrates, optionally further tiebroken by their opponent's winrates.
    https://en.wikipedia.org/wiki/Tie-breaking_in_Swiss-system_tournaments#Opponents'_win_percentage
    """
    # first tier resistance first
    opp_win_rates = defaultdict(list)
    for round in rounds:
        for matchup in round.matchups:
            if not matchup.player2:  # BYE
                continue
            p1 = matchup.player1
            p2 = matchup.player2
            # add opponent's score to the list
            opp_win_rates[p1].append(
                max(0.25, player_info_dict[p2].n_wins / player_info_dict[p2].n_played)
            )
            opp_win_rates[p2].append(
                max(0.25, player_info_dict[p1].n_wins / player_info_dict[p1].n_played)
            )
    resistances = defaultdict(int)
    for player, opps in opp_win_rates.items():
        if not opps:
            resistances[player] = 0
        else:
            resistances[player] = 100 * sum(opps) / len(opps)

    if not include_opponents:
        return resistances

    # now to add opponents' resistances. Somewhat dirty as just
    # 1/100th of the value instead of a real hierarchy

    opp_resistances = defaultdict(list)
    for round in rounds:
        for matchup in round.matchups:
            if not matchup.player2:  # BYE
                continue
            p1 = matchup.player1
            p2 = matchup.player2
            # add opponent's score to the list
            opp_resistances[p1].append(max(0.25, resistances[p2]))
            opp_resistances[p2].append(max(0.25, resistances[p1]))
    for player, opps in opp_resistances.items():
        if opps:
            resistances[player] += sum(opps) / len(opps) / 100

    return resistances
