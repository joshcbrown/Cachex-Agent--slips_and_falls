from utils.template_player import TemplatePlayer
from utils.heuristics import edge_branch_eval

class Player(TemplatePlayer):
    def __init__(self, player, n):
        super().__init__(player, n, "greedy", "edge_branch")
    
    def evaluate(self, player):
        return edge_branch_eval(self.tracking_board, player)
