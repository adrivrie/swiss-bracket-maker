import re

class Player():
    def __init__(self, name: str):
        self.name = name
        self.clean_name = re.sub(r'[^a-zA-Z0-9]', '', name) #''.join(filter(str.isalnum, name))
        self.score = 0
        self.resistance = 0
        self.matches = ""
        self.dropped = False


    def __str__(self):
        return f"{self.name}: {self.score}"


class Matchup():
    def __init__(self, player1: Player, player2: Player, notes: str = ""):
        self.player1 = player1
        self.player2 = player2
        self.winner = None
        self.score_player1 = 0.
        self.score_player2 = 0.
        self.notes = notes

        
    def __str__(self):
        return f"{self.player1.name} vs {self.player2.name}"


class Round():
    def __init__(self, matchups: list[Matchup]):
        self.matchups = matchups
        self.locked = False

