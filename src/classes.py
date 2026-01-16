import re

class Player():
    def __init__(self, name: str, dropped = False):
        self.name = name
        self.clean_name = re.sub(r'[^a-zA-Z0-9]', '', name) #''.join(filter(str.isalnum, name))
        self.dropped = dropped
        self.score = 0.0
        self.resistance = 0.0
        self.n_played = 0
        self.n_wins = 0

    def __str__(self):
        return f"{self.name}: {self.score}"

    def __repr__(self):
        return f"{self.name}"

    def to_dict(self):
        return {
            "name": self.name,
            "clean_name": self.clean_name,
            "score": self.score,
            "resistance": self.resistance,
            "dropped": self.dropped,
            "winpercentage": self.winpercentage,
            # Export only matchup IDs or opponent names to avoid circular references
            "matches": [f"{m.player1.name} vs {m.player2.name if m.player2 else 'BYE'}" for m in self.matches]
        }


class Matchup():
    def __init__(self, player1: str, player2: str, notes: str = ""):
        self.player1 = player1
        self.player2 = player2
        self.winner = ""
        self.score_player1 = 0.
        self.score_player2 = 0.
        self.notes = notes

    def __str__(self):
        return f"{self.player1} vs {self.player2 if self.player2 else "BYE"}"

    def __repr__(self):
        return f"{self.player1} vs {self.player2 if self.player2 else "BYE"}"

    def to_dict(self):
        return {
            "player1": self.player1,
            "player2": self.player2 if self.player2 else None,
            "winner": self.winner if self.winner else None,
            "score_player1": self.score_player1,
            "score_player2": self.score_player2,
            "notes": self.notes
        }


class Round():
    def __init__(self, matchups: list[Matchup]):
        self.matchups = matchups

    def __str__(self):
        return f"List of {len(self.matchups)}."

    def __repr__(self):
        return f"List of {len(self.matchups)}."

    def to_dict(self):
        return {
            "matchups": [m.to_dict() for m in self.matchups]
        }
