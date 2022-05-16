from utils.template_player import TemplatePlayer
from utils.heuristics import branch_eval

class Player(TemplatePlayer):
    def __init__(self, player, n):
        super().__init__(player, n, "greedy", "branch")
    
    def evaluate(self, player):
        return branch_eval(self.tracking_board, player)
