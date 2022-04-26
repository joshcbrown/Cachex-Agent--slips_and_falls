from referee.board import Board
from utils.player_logic import parse

_ACTION_STEAL = "STEAL"
_ACTION_PLACE = "PLACE"

_OPPONENT = { "red": "blue", "blue": "red", None: None }

class TrackingBoard(Board):
    def __init__(self, player, n):
        super().__init__(n)
        self.player = player
        self.move_history = []
    
    def update(self, player, action):
        atype, coord = parse(action)
        if atype == _ACTION_STEAL:
            self.swap()
            last_captures = None
        elif atype == _ACTION_PLACE:
            last_captures = self.place(player, coord)
        self.move_history.append((atype, coord, player, last_captures))

    def undo_last_move(self):
        atype, coord, player, last_captures = self.move_history.pop(-1)
        if atype == _ACTION_STEAL:
            self.swap()
        elif atype == _ACTION_PLACE:
            self.unplace(coord, player, last_captures)

    def unplace(self, coord, player, last_captures):
        self[coord] = None
        if len(last_captures) != 0:
            for coord in last_captures:
                self[coord] = _OPPONENT[player]
