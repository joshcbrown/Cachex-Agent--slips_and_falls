import numpy as np
from referee.board import Board
from utils.helper_functions import parse, action_to_move, move_to_action
from utils.heuristics import longest_branch

_ACTION_STEAL = "STEAL"
_ACTION_PLACE = "PLACE"
_OPPONENT = {"red": "blue", "blue": "red", None: None}
_WIN_VALUE = 1e7


class TrackingBoard(Board):
    def __init__(self, player, evaluate, n):
        super().__init__(n)
        np.random.seed(0)
        self.evaluations = 0
        self.player = player
        self.evaluate = evaluate
        self.n = n
        self.nm_depth = 2
        self.move_history = []
        self.possible_moves = {(p, r) for p in range(n) for r in range(n)}
        self.tiles_captured = 0
        self.start_squares = {
            "red": [(0, i) for i in range(n)],
            "blue": [(i, 0) for i in range(n)]
        }
        self.end_squares = {
            "red": [(n - 1, i) for i in range(n)],
            "blue": [(i, n - 1) for i in range(n)]
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
            self._swap(player)
            last_captures = None
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

    def unswap(self, player):
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
        self.possible_moves.add(_ACTION_STEAL)
        self.tiles_captured -= (1 if player == self.player else -1)

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

    def get_greedy_move(self):
        moves = list(self.possible_moves)
        # np.random.shuffle(moves)
        return max(
            moves,
            key=lambda move: self.evaluate_after_move(move)
        )

    def get_negamax_move(self, prune=False):
        self.evaluations = 0
        moves = list(self.possible_moves)
        # np.random.shuffle(moves)
        best_move = best_move_val = best_children = None
        for move in moves:
            # print(f"{self.player} first move: {move}")
            value, children = self.evaluate_negamax(move, prune)
            if best_move is None or value > best_move_val:
                best_move = move
                best_move_val = value
                best_children = children
            if best_move_val == _WIN_VALUE:
                break
        print(best_move)
        print(best_move_val)
        print(best_children)
        print(self.evaluations)
        return best_move

    def evaluate_negamax(self, move, prune):
        self.update(self.player, move_to_action(move))
        if prune:
            neg_value, sequence = self.alpha_beta(self.nm_depth, _OPPONENT[self.player], -_WIN_VALUE, _WIN_VALUE)
        else:
            neg_value, sequence = self.negamax(self.nm_depth, _OPPONENT[self.player])
        sequence.append(f"{self.player}:{move}")
        sequence.reverse()
        self.undo_last_move()
        return -neg_value, sequence

    def evaluate_after_move(self, move):
        self.update(self.player, move_to_action(move))
        value = self.evaluate(self.player)
        self.undo_last_move()
        return value

    def negamax(self, depth: int, player):
        # TODO: investigate negamax not finding steal as best move for opposition
        if depth == 0 or self.game_over():
            self.evaluations += 1
            # print(f"{depth=}, {self._data}, {self.evaluate(player)}")
            return self.evaluate(player), []
        best_value = None
        children = []
        for move in self.possible_moves:
            if move == _ACTION_STEAL:
                original = self.possible_moves
                self.possible_moves = self.possible_moves.copy()
            self.update(player, move_to_action(move))
            # print(f"{player=}, {move=}, {self._data}\n")
            neg_node_value, potential_children = self.negamax(depth - 1, _OPPONENT[player])
            node_value = -neg_node_value
            if best_value is None or node_value > best_value:
                best_value = node_value
                children = potential_children
                children.append(f"{player}:{move}")
            self.undo_last_move()
            if move == _ACTION_STEAL:
                assert original == self.possible_moves
                self.possible_moves = original
        return best_value, children

    def alpha_beta(self, depth: int, player, alpha: float, beta: float):
        # TODO: investigate negamax not finding steal as best move for opposition
        if depth == 0 or self.game_over():
            # print(f"{depth=}, {self._data}, {self.evaluate(player)}")
            self.evaluations += 1
            return self.evaluate(player), []
        children = []
        for move in self.possible_moves:
            if move == _ACTION_STEAL:
                original = self.possible_moves
                self.possible_moves = self.possible_moves.copy()
            self.update(player, move_to_action(move))
            # print(f"{player=}, {move=}, {self._data}\n")
            neg_node_value, potential_children = self.alpha_beta(depth - 1, _OPPONENT[player], -beta, -alpha)
            node_value = -neg_node_value
            if node_value > alpha:
                alpha = node_value
                children = potential_children
                children.append(f"{player}:{move}")
            self.undo_last_move()
            if move == _ACTION_STEAL:
                assert original == self.possible_moves
                self.possible_moves = original
            if alpha >= beta:
                break
        return alpha, children

    def game_over(self):
        if longest_branch(self, self.player, from_start=True) == self.n:
            return self.player
        elif longest_branch(self, _OPPONENT[self.player], from_start=True) == self.n:
            return _OPPONENT[self.player]
        # TODO: worry about draws
        return None

    # TODO: investigate following sequence of moves against alpha beta as red, board size 4 red, nm depth 2: red (1, 2),
    #  blue: (1, 0), red: (3, 1), blue: (1, 1), red: (2, 2) (it thinks this is a win, very strange) blue: (0, 2),
    #  red: (0, 1), blue: (0, 2), red: (1, 3) (misses win here but also thinks it wins with a non-winning move)
