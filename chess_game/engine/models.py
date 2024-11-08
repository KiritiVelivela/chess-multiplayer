import chess
from django.db import models
from django.contrib.auth.models import User

class Game(models.Model):
    player_white = models.ForeignKey(User, related_name='white_player', on_delete=models.CASCADE)
    player_black = models.ForeignKey(User, related_name='black_player', on_delete=models.CASCADE)
    current_fen = models.CharField(max_length=100, default=chess.Board().fen())  # Store the FEN string for the current state
    game_over = models.BooleanField(default=False)  # Track if the game is finished
    winner = models.ForeignKey(User, related_name='games_won', null=True, blank=True, on_delete=models.SET_NULL)
    resignation = models.BooleanField(default=False)
    journal_entry = models.TextField(null=True, blank=True)  # Allow null and blank for optional entries

    # Add a method for move count
    @property
    def move_count(self):
        # FEN structure: parts = [piece placement, active color, castling, en passant, half-move clock, full-move number]
        fen_parts = self.current_fen.split()
        if len(fen_parts) >= 6:
            # Return the full-move number directly from the FEN (it's the last element in the FEN string)
            return int(fen_parts[5])  # Full-move number from FEN
        return 0

    def __str__(self):
        return f"Game {self.id} - {self.player_white.username} vs {self.player_black.username}"


class Move(models.Model):
    game = models.ForeignKey(Game, related_name='moves', on_delete=models.CASCADE)
    uci_move = models.CharField(max_length=10)  # Store the move in UCI format
    move_number = models.IntegerField()

    def __str__(self):
        return f"Move {self.move_number}: {self.uci_move}"


class Challenge(models.Model):
    challenger = models.ForeignKey(User, related_name='challenges_made', on_delete=models.CASCADE)
    challenged = models.ForeignKey(User, related_name='challenges_received', on_delete=models.CASCADE)
    accepted = models.BooleanField(null=True)  # `None` means pending, `True` means accepted, `False` means rejected
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.challenger.username} challenged {self.challenged.username}"