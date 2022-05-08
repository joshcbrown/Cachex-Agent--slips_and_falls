from utils.heuristics import best_heuristic, new_heuristic
from utils.template_player import TemplatePlayer


class Player(TemplatePlayer):
    def __init__(self, player, n):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "red" if your player will
        play as Red, or the string "blue" if your player will play
        as Blue.
        """
        super().__init__(player, n, "ab")

    def evaluate(self, player):
        return new_heuristic(self.tracking_board, player)
