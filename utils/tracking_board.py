from referee.board import Board
from utils.player_logic import parse

_ACTION_STEAL = "STEAL"
_ACTION_PLACE = "PLACE"

_OPPONENT = {"red": "blue", "blue": "red", None: None}


class TrackingBoard(Board):
    def __init__(self, player, n):
        super().__init__(n)
        self.player = player
        self.move_history = []
        self.possible_moves = {(p, r) for p in range(n) for r in range(n)}
        if n % 2 == 1:
            self.centre = (n // 2, n // 2)
            self.possible_moves.remove(self.centre)
        else:
            self.centre = None

    def update(self, player, action):
        atype, coord = parse(action)
        if atype == _ACTION_STEAL:
            self.possible_moves.remove(_ACTION_STEAL)
            self.swap()
            last_captures = None
            self.possible_moves = {(r, p) for p, r in self.possible_moves}
        elif atype == _ACTION_PLACE:
            self.possible_moves.remove(coord)
            last_captures = self.place(player, coord)
            if len(last_captures) != 0:
                for captured_coord in last_captures:
                    self.possible_moves.add(captured_coord)
            if len(self.move_history) == 0:
                self.possible_moves.add(_ACTION_STEAL)
                if self.centre is not None:
                    self.possible_moves.add(self.centre)
            elif len(self.move_history) == 1:
                self.possible_moves.remove(_ACTION_STEAL)
        self.move_history.append((atype, coord, player, last_captures))

    def undo_last_move(self):
        atype, coord, player, last_captures = self.move_history.pop(-1)
        if atype == _ACTION_STEAL:
            self.unswap()
        elif atype == _ACTION_PLACE:
            self.unplace(coord, player, last_captures)

    def unswap(self):
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
        self.possible_moves.add(_ACTION_STEAL)

    def unplace(self, coord, player, last_captures):
        self[coord] = None
        self.possible_moves.add(coord)
        if len(last_captures) != 0:
            for captured_coord in last_captures:
                self[captured_coord] = _OPPONENT[player]
                self.possible_moves.remove(captured_coord)
        elif len(self.move_history) == 0:
            self.possible_moves.remove(_ACTION_STEAL)
            if self.centre is not None:
                self.possible_moves.remove(self.centre)
        elif len(self.move_history) == 1:
            self.possible_moves.add(_ACTION_STEAL)
