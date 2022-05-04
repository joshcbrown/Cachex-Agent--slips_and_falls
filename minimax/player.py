from utils.template_player import TemplatePlayer
from utils.heuristics import best_heuristic
_ACTION_PLACE = "PLACE"


class Player(TemplatePlayer):
    def __init__(self, player, n):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "red" if your player will
        play as Red, or the string "blue" if your player will play
        as Blue.
        """
        super().__init__(player, n)

    def evaluate(self):
        return best_heuristic(self.tracking_board, self.player)