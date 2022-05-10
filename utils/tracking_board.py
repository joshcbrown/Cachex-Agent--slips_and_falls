import random
import numpy as np
from math import inf
from referee.board import Board
from utils.helper_functions import parse, action_to_move, move_to_action
from utils.heuristics import longest_edge_branch, centre_advantage
from time import perf_counter as timer
import heapq

_NEIGHBOUR_OFFSETS = (
    (0, 1),
    (0, -1),
    (1, 0),
    (-1, 0),
    (1, -1),
    (-1, 1)
)
_ACTION_STEAL = "STEAL"
_ACTION_PLACE = "PLACE"
_OPPONENT = {"red": "blue", "blue": "red", None: None}
_WIN_VALUE = 1e9


class TrackingBoard(Board):
    def __init__(self, player, evaluate, n):
        super().__init__(n)
        #np.random.seed(0)
        #random.seed(0)
        self.evaluations = 0
        self.total_time = 0
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
        self.tiles = {
            "red": set(),
            "blue": set()
        }
        if n % 2 == 1:
            self.centre = (n // 2, n // 2)
            self.possible_moves.remove(self.centre)
        else:
            self.centre = None

    def update(self, player, action):
        move = action_to_move(action)
        if move == _ACTION_STEAL:
            self._swap(player)
            last_captures = None
        else:
            last_captures = self._place(player, move)
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
        tile = self.tiles[_OPPONENT[player]].pop()
        self.tiles[player].add((tile[1], tile[0]))

    def unswap(self, player):
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
        self.possible_moves.add(_ACTION_STEAL)
        self.tiles_captured -= (1 if player == self.player else -1)
        tile = self.tiles[player].pop()
        self.tiles[_OPPONENT[player]].add((tile[1], tile[0]))

    def _place(self, player, move):
        self.possible_moves.remove(move)
        last_captures = self.place(player, move)
        self.tiles[player].add(move)
        if len(last_captures) != 0:
            for captured_coord in last_captures:
                self.possible_moves.add(captured_coord)
                self.tiles_captured += (1 if player == self.player else -1)
                self.tiles[_OPPONENT[player]].remove(captured_coord)
        if len(self.move_history) == 0:
            self.possible_moves.add(_ACTION_STEAL)
            if self.centre is not None:
                self.possible_moves.add(self.centre)
        elif len(self.move_history) == 1:
            self.possible_moves.remove(_ACTION_STEAL)
        return last_captures

    def unplace(self, coord, player, last_captures):
        self[coord] = None
        self.tiles[player].remove(coord)
        self.possible_moves.add(coord)
        if len(last_captures) != 0:
            for captured_coord in last_captures:
                self[captured_coord] = _OPPONENT[player]
                self.tiles[_OPPONENT[player]].add(captured_coord)
                self.possible_moves.remove(captured_coord)
                self.tiles_captured -= (1 if player == self.player else -1)
        elif len(self.move_history) == 0:
            self.possible_moves.remove(_ACTION_STEAL)
            if self.centre is not None:
                self.possible_moves.remove(self.centre)
        elif len(self.move_history) == 1:
            self.possible_moves.add(_ACTION_STEAL)

    def time_to_steal(self):
        return True 
        return self.centre is None

    def get_greedy_move(self):
        if len(self.move_history) == 0:
            return 0, self.n - 1
        if len(self.move_history) == 1:
            return _ACTION_STEAL if self.time_to_steal() else self.centre
        moves = list(self.possible_moves)
        np.random.shuffle(moves)
        return max(
            moves,
            key=lambda move: self.evaluate_after_move(move)
        )

    def get_negamax_move(self, prune=False):
        if len(self.move_history) == 0:
            return 0, self.n - 1
        if len(self.move_history) == 1:
            return _ACTION_STEAL if self.time_to_steal() else self.centre
        time_left = self.n**2 - self.total_time
        start_time = timer()
        self.evaluations = 0
        best_move = best_children = None
        best_move_val = -inf
        moves = list(self.possible_moves)
        np.random.shuffle(moves)
        for move in moves:
            # if there's only 1 seconds left give up on nm
            if time_left - (timer() - start_time) < 1:
                return self.get_greedy_move()
            value, children = self.evaluate_negamax(move, prune)
            if value > best_move_val:
                best_move = move
                best_move_val = value
                best_children = children
            if best_move_val == _WIN_VALUE:
                break
        if best_move_val != _WIN_VALUE:
            # print(f"Anticipated sequence: {best_children}")
            # print(f"Move val: {best_move_val}")
            # print(f"Evals: {self.evaluations}")
            # print(f"Time: {self.total_time + (timer() - start_time)}\n")
            pass
        else:
            print(f"TOTAL TIME: {self.total_time + (timer() - start_time)}\n")
        return best_move

    def evaluate_negamax(self, move, prune):
        self.update(self.player, move_to_action(move))
        if prune:
            neg_value, sequence = self.alpha_beta(
                self.nm_depth, _OPPONENT[self.player], -_WIN_VALUE, _WIN_VALUE
            )
        else:
            neg_value, sequence = self.negamax(
                self.nm_depth, _OPPONENT[self.player]
            )
        sequence.append(f"{self.player[0]}:{move}")
        sequence.reverse()
        self.undo_last_move()
        return -neg_value, sequence

    def evaluate_after_move(self, move):
        self.update(self.player, move_to_action(move))
        value = self.evaluate(self.player)
        self.undo_last_move()
        return value

    def negamax(self, depth: int, player):
        if depth == 0 or self.game_over():
            self.evaluations += 1
            return self.evaluate(player), []
        best_value = -inf
        children = []
        for move in self.possible_moves:
            self.update(player, move_to_action(move))
            neg_node_value, potential_children = self.negamax(
                depth - 1, _OPPONENT[player]
            )
            node_value = -neg_node_value
            if node_value > best_value:
                best_value = node_value
                children = potential_children
                children.append(f"{player[0]}:{move}")
            self.undo_last_move()
        return best_value, children

    def alpha_beta(self, depth: int, player, alpha: float, beta: float):
        if depth == 0 or self.game_over():
            self.evaluations += 1
            return self.evaluate(player), []
        children = []
        # heap = [(self.num_neighbors(move), move) for move in self.possible_moves]
        # heapq.heapify(heap)
        # while heap:
        #     move = heapq.heappop(heap)[1]
        for move in self.possible_moves:
            self.update(player, move_to_action(move))
            neg_node_value, potential_children = self.alpha_beta(
                depth - 1, _OPPONENT[player], -beta, -alpha
            )
            node_value = -neg_node_value
            self.undo_last_move()
            if node_value > alpha:
                alpha = node_value
                children = potential_children
                children.append(f"{player[0]}:{move}")
            if alpha >= beta:
                break
        return alpha, children

    def game_over(self):
        if longest_edge_branch(self, self.player, from_start=True) == self.n:
            return self.player
        elif longest_edge_branch(self, _OPPONENT[self.player], from_start=True) == self.n:
            return _OPPONENT[self.player]
        return None

    def num_neighbors(self, move):
        neighbors = 0
        for dx, dy in _NEIGHBOUR_OFFSETS:
            x = move[0] + dx
            y = move[1] + dy
            if (0 <= x < self.n and 0 <= y < self.n and self[(x, y)]):
                neighbors += 1
        return neighbors

    def has_neighbour(self, move):
        for dx, dy in _NEIGHBOUR_OFFSETS:
            x = move[0] + dx
            y = move[1] + dy
            if (0 <= x < self.n and 0 <= y < self.n and self[(x, y)]):
                return 1
        return 0
