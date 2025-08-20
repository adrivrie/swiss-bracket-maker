import re

class Player():
    def __init__(self, name: str):
        self.name = name
        self.clean_name = re.sub(r'[^a-zA-Z0-9]', '', name) #''.join(filter(str.isalnum, name))
        self.score = 0.0
        self.resistance = 0.0
        self.matches: list[Matchup] = []
        self.dropped = False
        self.winpercentage = 0.0

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
    def __init__(self, player1: Player, player2: Player, notes: str = ""):
        self.player1 = player1
        self.player2 = player2
        self.winner = None
        self.score_player1 = 0.
        self.score_player2 = 0.
        self.notes = notes

    def __str__(self):
        return f"{self.player1.name} vs {self.player2.name if self.player2 else "BYE"}"

    def __repr__(self):
        return f"{self.player1.name} vs {self.player2.name if self.player2 else "BYE"}"

    def to_dict(self):
        return {
            "player1": self.player1.name,
            "player2": self.player2.name if self.player2 else None,
            "winner": self.winner.name if self.winner else None,
            "score_player1": self.score_player1,
            "score_player2": self.score_player2,
            "notes": self.notes
        }


class Round():
    def __init__(self, matchups: list[Matchup], locked: bool = False):
        self.matchups = matchups
        self.locked = locked

    def __str__(self):
        return f"List of {len(self.matchups)}. Locked: {self.locked}"

    def __repr__(self):
        return f"List of {len(self.matchups)}. Locked: {self.locked}"

    def to_dict(self):
        return {
            "locked": self.locked,
            "matchups": [m.to_dict() for m in self.matchups]
        }
