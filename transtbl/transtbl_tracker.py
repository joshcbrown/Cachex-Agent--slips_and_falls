import random
import numpy as np
from math import inf, ceil

from referee.board import Board
from utils.helper_functions import action_to_move, move_to_action
from utils.heuristics import longest_edge_branch
from time import perf_counter as timer
import heapq
from queue import Queue
from collections import defaultdict as dd

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

depth_dict = {
    3 : 10,
    4 : 5,
    5 : 4,
    6 : 4
}


class TranstblTracker(Board):
    def __init__(self, player, evaluate, n):
        super().__init__(n)
        self.evaluations = 0
        self.total_evals = 0
        self.total_time = 0
        self.player = player
        self.evaluate = evaluate
        self.n = n
        self.move_history = []
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
        self.init_zobrist()

    def update(self, player, action):
        move = action_to_move(action)
        if move == _ACTION_STEAL:
            self.turn_swap(player)
            last_captures = None
        else:
            last_captures = self.turn_place(player, move)
        self.move_history.append((move, player, last_captures))

    def turn_swap(self, player):
        self.swap()
        self.tiles_captured += (1 if player == self.player else -1)
        tile = self.tiles[_OPPONENT[player]].pop()
        self.tiles[player].add((tile[1], tile[0]))
        self.update_zobrist(_OPPONENT[player], tile)
        self.update_zobrist(player, (tile[1], tile[0]))
        self.incr_state()

    def turn_place(self, player, move):
        last_captures = self.place(player, move)
        self.update_zobrist(player, move)
        self.tiles[player].add(move)
        for captured_coord in last_captures:
            self.tiles_captured += (1 if player == self.player else -1)
            self.tiles[_OPPONENT[player]].remove(captured_coord)
            self.update_zobrist(_OPPONENT[player], captured_coord)
        self.incr_state()
        return last_captures

    def internal_update(self, player, action):
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
        self.update_zobrist(_OPPONENT[player], tile)
        self.update_zobrist(player, (tile[1], tile[0]))
        self.incr_state()

    def unswap(self, player):
        self.decr_state()
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
        self.tiles_captured -= (1 if player == self.player else -1)
        tile = self.tiles[player].pop()
        self.tiles[_OPPONENT[player]].add((tile[1], tile[0]))
        self.update_zobrist(player, tile)
        self.update_zobrist(_OPPONENT[player], (tile[1], tile[0]))

    def _place(self, player, move):
        self.possible_moves.remove(move)
        last_captures = self.place(player, move)
        self.update_zobrist(player, move)
        self.tiles[player].add(move)
        for captured_coord in last_captures:
            self.possible_moves.add(captured_coord)
            self.tiles_captured += (1 if player == self.player else -1)
            self.tiles[_OPPONENT[player]].remove(captured_coord)
            self.update_zobrist(_OPPONENT[player], captured_coord)
        self.incr_state()
        return last_captures

    def unplace(self, coord, player, last_captures):
        self.decr_state()
        self[coord] = None
        self.tiles[player].remove(coord)
        self.possible_moves.add(coord)
        self.update_zobrist(player, coord)
        for captured_coord in last_captures:
            self[captured_coord] = _OPPONENT[player]
            self.tiles[_OPPONENT[player]].add(captured_coord)
            self.possible_moves.remove(captured_coord)
            self.tiles_captured -= (1 if player == self.player else -1)
            self.update_zobrist(_OPPONENT[player], captured_coord)

    def get_greedy_move(self):
        moves = list(self.possible_moves)
        np.random.shuffle(moves)
        return max(
            moves,
            key=lambda move: self.evaluate_after_move(move)
        )

    def evaluate_after_move(self, move):
        self.internal_update(self.player, move_to_action(move))
        value = self.evaluate(self.player)
        self.undo_last_move()
        return value

    def evaluation_wrapper(self, player):
        self.evaluations += 1
        # slightly discourage a draw
        if self.state_count() >= 7:
            return 0
        eval = self.evaluate(player)
        if eval == _WIN_VALUE:
            return eval - len(self.move_history)
        if eval == -_WIN_VALUE:
            return eval + len(self.move_history)
        return eval

    def get_nm_depth(self):
        perc_time = (self.total_time + timer() - self.move_start) / self.n**2
        key = self.n
        if key in depth_dict:
            # smaller boards we can go a bit deeper
            base = depth_dict[key]
            if perc_time > 0.97:
                return 0, .97
            elif perc_time > 0.85:
                return base - 2, .85
            elif perc_time > 0.70:
                return base - 1, .70
        else:
            # larger boards stick to depth of 3
            base = 3
            if perc_time > 0.97:
                print("OUT OF TIME")
                return 0, .97
            elif perc_time > 0.75:
                return base - 1, .75
        return base, None

    def time_to_steal(self):
        if self.n == 3:
            last_tile = self.move_history[0][0]
            if last_tile in [(0, 2), (0, 1), (2, 0), (2, 1)]:
                return True
            else:
                return False
        if self.n == 4:
            return False
        return True

    def get_first_move(self):
        if self.n == 3:
            return 1, 0
        else:
            return self.n - 1, 0

    def get_transtbl_move(self):
        self.move_start = timer()

        if len(self.move_history) == 0:
            return self.get_first_move()
        if len(self.move_history) == 1:
            if self.time_to_steal():
                return _ACTION_STEAL

        self.nm_depth, perc = self.get_nm_depth()
        if perc: print(perc)
        if self.nm_depth <= 0:
            return self.get_greedy_move()
        self.evaluations = 0
        
        # manage moves
        if self.n == 3:
            self.possible_moves = self.get_occupied_neighbours(max_depth=4)
        else:
            self.possible_moves = self.get_occupied_neighbours()
            for corner in [(0, self.n-1), (self.n-1, 0)]:
                if not self[corner]:
                    self.possible_moves.add(corner)
        self.transtbl = dict()
        score, best_move = self.negamax_ab_tt(
            self.nm_depth, self.player, -inf, inf
        )

        self.total_evals += self.evaluations
        # print(f"{score = }")
        # print(self.state_count())
        # print(f"Evals: {self.evaluations}")
        # print(f"Time: {self.total_time + (timer() - start_time)}\n")
        return best_move


    def negamax_ab_tt(self, depth: int, player, alpha: float, beta: float):
        alpha_orig = alpha
        
        if self.zobrist in self.transtbl:
            tt_val, tt_depth, tt_flag = self.transtbl[self.zobrist]
            if tt_depth >= depth:    
                if tt_flag == "E":
                    return tt_val
                elif tt_flag == "L":
                    alpha = max(alpha, tt_val)
                elif tt_flag == "U":
                    beta = min(beta, tt_val)
                
                if alpha >= beta:
                    return tt_val

        if depth == 0 or self.game_over():
            self.evaluations += 1
            return self.evaluation_wrapper(player)
        
        value = -inf
        best_move = None
        heap = [(-self.num_neighbors(move), move) for move in self.possible_moves]
        heapq.heapify(heap)
        while heap:
            move = heapq.heappop(heap)[1]
            self.internal_update(player, move_to_action(move))
            node_value = -self.negamax_ab_tt(
                depth - 1, _OPPONENT[player], -beta, -alpha
            )
            value = max(value, node_value)
            if node_value > alpha or best_move is None:
                alpha = node_value
                best_move = move
            self.undo_last_move()
            if alpha >= beta:
                break

        if value <= alpha_orig:
            tt_flag = "U"
        elif value >= beta:
            tt_flag = "L"
        else:
            tt_flag = "E"
        self.transtbl[self.zobrist] = (value, depth, tt_flag)
        return alpha if depth < self.nm_depth else (alpha, best_move)


    def game_over(self):
        if longest_edge_branch(self, self.player, from_start=True) == self.n:
            return self.player
        elif longest_edge_branch(self, _OPPONENT[self.player], from_start=True) == self.n:
            return _OPPONENT[self.player]
        return self.state_count() >= 7

    def num_neighbors(self, move):
        neighbors = 0
        for dx, dy in _NEIGHBOUR_OFFSETS:
            x = move[0] + dx
            y = move[1] + dy
            if (0 <= x < self.n and 0 <= y < self.n and self[(x, y)]):
                neighbors += 1
        return neighbors

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
        # then do BFS up do depth = max_depth
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

    def init_zobrist(self):
        self.z_table = []
        for _ in range(self.n):
            row = []
            for _ in range(self.n):
                row.append([random.getrandbits(64), random.getrandbits(64)])
            self.z_table.append(row)
        self.zobrist = 0
        self.state_counter = dd(int)
        self.incr_state()
    
    def update_zobrist(self, player, tile):
        self.zobrist ^= self.z_table[tile[0]][tile[1]][0 if player == "red" else 1] 

    def state_count(self):
        return self.state_counter[self.zobrist]

    def incr_state(self):
        self.state_counter[self.zobrist] += 1
    
    def decr_state(self):
        self.state_counter[self.zobrist] -= 1
