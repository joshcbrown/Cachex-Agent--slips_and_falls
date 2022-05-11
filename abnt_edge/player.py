from utils.heuristics import branch_capture, edge_branch_advantage, edge_branch_capture
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
        super().__init__(player, n, "abntedge")

    def evaluate(self, player):
        return edge_branch_capture(self.tracking_board, player)
