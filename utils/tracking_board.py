from referee.board import Board
from utils.helper_functions import parse, action_to_move, move_to_action
from utils.heuristics import longest_branch
_ACTION_STEAL = "STEAL"
_ACTION_PLACE = "PLACE"
_OPPONENT = {"red": "blue", "blue": "red", None: None}

class TrackingBoard(Board):
    def __init__(self, player, n):
        super().__init__(n)
        self.player = player
        self.n = n
        self.move_history = []
        self.possible_moves = {(p, r) for p in range(n) for r in range(n)}
        self.tiles_captured = 0
        self.start_squares = {
            "red": [(0, i) for i in range(n)],
            "blue": [(i, 0) for i in range(n)]
        }
        self.end_squares = {
            "red": [(n-1, i) for i in range(n)], 
            "blue": [(i, n-1) for i in range(n)]
        }
        if n % 2 == 1:
            self.centre = (n // 2, n // 2)
            self.possible_moves.remove(self.centre)
        else:
            self.centre = None

    def update(self, player, action):
        move = action_to_move(action)
        # print(f"before: {self.possible_moves}")
        if move == _ACTION_STEAL:
            last_captures = self._swap(player)
        else:
            last_captures = self._place(player, move)
        # print(f"after: {self.possible_moves}")
        self.move_history.append((move, player, last_captures))

    def undo_last_move(self):
        move, player, last_captures = self.move_history.pop(-1)
        if move == _ACTION_STEAL:
            self.unswap(player)
        else:
            self.unplace(move, player, last_captures)
    
    def _swap(self, player):
        self.possible_moves.remove(_ACTION_STEAL)
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
        self.tiles_captured += (1 if player == self.player else -1)

    def _place(self, player, move):
        self.possible_moves.remove(move)
        last_captures = self.place(player, move)
        if len(last_captures) != 0:
            for captured_coord in last_captures:
                self.possible_moves.add(captured_coord)
                self.tiles_captured += (1 if player == self.player else -1)
        if len(self.move_history) == 0:
            self.possible_moves.add(_ACTION_STEAL)
            if self.centre is not None:
                self.possible_moves.add(self.centre)
        elif len(self.move_history) == 1:
            self.possible_moves.remove(_ACTION_STEAL)
        return last_captures

    def unswap(self, player):
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
        self.possible_moves.add(_ACTION_STEAL)
        self.tiles_captured -= (1 if player == self.player else -1)

    def unplace(self, coord, player, last_captures):
        self[coord] = None
        self.possible_moves.add(coord)
        if len(last_captures) != 0:
            for captured_coord in last_captures:
                self[captured_coord] = _OPPONENT[player]
                self.possible_moves.remove(captured_coord)
                self.tiles_captured -= (1 if player == self.player else -1)
        elif len(self.move_history) == 0:
            self.possible_moves.remove(_ACTION_STEAL)
            if self.centre is not None:
                self.possible_moves.remove(self.centre)
        elif len(self.move_history) == 1:
            self.possible_moves.add(_ACTION_STEAL)

    def get_greedy_move(self, evaluate):
        return max(
            list(self.possible_moves),
            key=lambda move: self.evaluate_after_move(move, evaluate)
        )

    def evaluate_after_move(self, move, evaluate):
        self.update(self.player, move_to_action(move))
        value = evaluate()
        self.undo_last_move()
        return value
