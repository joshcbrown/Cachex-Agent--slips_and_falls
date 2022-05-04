from utils.template_player import TemplatePlayer

class Player(TemplatePlayer):
    def __init__(self, player, n):
        super().__init__(player, n)

    def evaluate(self):
        return self.tracking_board.tiles_captured
