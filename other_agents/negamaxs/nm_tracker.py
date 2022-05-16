import random
import numpy as np
from math import inf
from referee.board import Board
from utils.helper_functions import action_to_move, move_to_action
from utils.heuristics import longest_edge_branch
from time import perf_counter as timer
import heapq
from queue import Queue

_NEIGHBOUR_OFFSETS = (
    (0, 1),
    (0, -1),
    (1, 0),
    (-1, 0),
    (1, -1),
    (-1, 1)
)
_ACTION_STEAL = "STEAL"
_OPPONENT = {"red": "blue", "blue": "red", None: None}
_WIN_VALUE = 1e7


class NegamaxTracker(Board):
    def __init__(self, player, evaluate, n):
        super().__init__(n)
        # np.random.seed(int(timer()*1e9) % (2**32))
        # random.seed(int(timer()*1e9) % (2**32))
        np.random.seed(0)
        random.seed(0)
        self.evaluations = 0
        self.total_evals = 0
        self.total_time = 0
        self.nm_depth = 3 if n > 3 else 1000
        self.player = player
        self.evaluate = evaluate
        self.n = n
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
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
        self.tiles_captured += (1 if player == self.player else -1)
        tile = self.tiles[_OPPONENT[player]].pop()
        self.tiles[player].add((tile[1], tile[0]))

    def unswap(self, player):
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
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
            if self.centre is not None:
                self.possible_moves.add(self.centre)
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
            if self.centre is not None:
                self.possible_moves.remove(self.centre)

    def get_greedy_move(self):
        moves = list(self.possible_moves)
        np.random.shuffle(moves)
        return max(
            moves,
            key=lambda move: self.evaluate_after_move(move)
        )

    def evaluate_after_move(self, move):
        self.update(self.player, move_to_action(move))
        value = self.evaluate(self.player)
        self.undo_last_move()
        return value


    def evaluation_wrapper(self, player):
        self.evaluations += 1
        eval = self.evaluate(player) 
        if eval == _WIN_VALUE:
            return eval - len(self.move_history)
        if eval == -_WIN_VALUE:
            return eval + len(self.move_history)
        return eval

    def time_to_steal(self):
        return True

    def get_first_move(self):
        return 0, 0

    def get_negamax_move(self, prune=False, within2=False):
        self.move_start = timer()

        if len(self.move_history) == 0:
            return self.get_first_move()
        if len(self.move_history) == 1:
            if self.time_to_steal():
                return _ACTION_STEAL

        # manage moves
        if within2:
            all_moves = self.possible_moves
            self.possible_moves = self.get_occupied_neighbours()

        self.evaluations = 0
        best_move_val = -inf        
        for move in self.possible_moves:
            value = self.evaluate_negamax(move, prune)
            if value > best_move_val:
                best_move = move
                best_move_val = value
        if within2:
            self.possible_moves = all_moves

        self.total_evals += self.evaluations
        return best_move

    def evaluate_negamax(self, move, prune):
        self.update(self.player, move_to_action(move))
        if prune:
            neg_value = self.alpha_beta(
                self.nm_depth, _OPPONENT[self.player], -inf, inf
            )
        else:
            neg_value = self.negamax(
                self.nm_depth, _OPPONENT[self.player]
            )
        self.undo_last_move()
        return -neg_value

    def negamax(self, depth: int, player):
        if depth == 0 or self.game_over():
            return self.evaluation_wrapper(player)
        best_value = -inf
        for move in self.possible_moves:
            self.update(player, move_to_action(move))
            node_value = -self.negamax(
                depth - 1, _OPPONENT[player]
            )
            self.undo_last_move()
            best_value = max(best_value, node_value)
        return best_value

    def alpha_beta(self, depth: int, player, alpha: float, beta: float):
        if depth == 0 or self.game_over():
            return self.evaluation_wrapper(player)
        heap = [(-self.num_neighbors(move), move) for move in self.possible_moves]
        heapq.heapify(heap)
        while heap:
            move = heapq.heappop(heap)[1]
            self.update(player, move_to_action(move))
            node_value = -self.alpha_beta(
                depth - 1, _OPPONENT[player], -beta, -alpha
            )
            self.undo_last_move()
            alpha = max(alpha, node_value)
            if alpha >= beta:
                break
        return alpha

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

    def get_occupied_neighbours(self, max_depth=2):
        q = Queue(maxsize = self.n**2)
        seen = set()
        neighbours = set()
        # start with currently occupied squares as depth 0
        for tile in self.tiles[self.player]:
            q.put((tile, 0))
            seen.add(tile)
        for tile in self.tiles[_OPPONENT[self.player]]:
            q.put((tile, 0))
            seen.add(tile)
        # then do BFS up to depth = max_depth
        while not q.empty():
            (x, y), depth = q.get()
            for dx, dy in _NEIGHBOUR_OFFSETS:
                nbr = x+dx, y+dy
                if (
                    depth < max_depth and 
                    nbr not in seen and
                    0 <= nbr[0] < self.n and 0 <= nbr[1] < self.n and 
                    not self[nbr]
                    ):
                        seen.add(nbr)
                        neighbours.add(nbr)
                        if depth + 1 < max_depth:
                            q.put((nbr, depth + 1))
        return neighbours
