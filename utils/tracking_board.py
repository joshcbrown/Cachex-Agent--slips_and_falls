import random
import numpy as np
from math import inf
from referee.board import Board
from utils.helper_functions import parse, action_to_move, move_to_action
from utils.heuristics import longest_edge_branch, centre_advantage
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
_ACTION_PLACE = "PLACE"
_OPPONENT = {"red": "blue", "blue": "red", None: None}
_WIN_VALUE = 1e10

depth_dict = {
    (3, False) : 9,
    (3, True) : 9,
    (4, False) : 4,
    (4, True) : 5,
    (5, False) : 3,
    (5, True) : 4,
    (6, False) : 3,
    (6, True) : 4
}


class TrackingBoard(Board):
    def __init__(self, player, evaluate, n):
        super().__init__(n)
        seed1 = int(timer()*1e9) % (2**32)
        np.random.seed(seed1)
        seed2 = int(timer()*1e9) % (2**32)
        random.seed(seed2)
        # np.random.seed(0)
        # random.seed(0)
        self.evaluations = 0
        self.total_evals = 0
        self.total_time = 0
        self.player = player
        self.evaluate = evaluate
        self.n = n
        #self.nm_depth = self.get_nm_depth()
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
        self.init_zobrist()

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
        if len(last_captures) != 0:
            for captured_coord in last_captures:
                self.possible_moves.add(captured_coord)
                self.tiles_captured += (1 if player == self.player else -1)
                self.tiles[_OPPONENT[player]].remove(captured_coord)
                self.update_zobrist(_OPPONENT[player], captured_coord)
        self.incr_state()
        if len(self.move_history) == 0:
            if self.centre is not None:
                self.possible_moves.add(self.centre)
        return last_captures

    def unplace(self, coord, player, last_captures):
        self.decr_state()
        self[coord] = None
        self.tiles[player].remove(coord)
        self.possible_moves.add(coord)
        self.update_zobrist(player, coord)
        if len(last_captures) != 0:
            for captured_coord in last_captures:
                self[captured_coord] = _OPPONENT[player]
                self.tiles[_OPPONENT[player]].add(captured_coord)
                self.possible_moves.remove(captured_coord)
                self.tiles_captured -= (1 if player == self.player else -1)
                self.update_zobrist(_OPPONENT[player], captured_coord)
        elif len(self.move_history) == 0:
            if self.centre is not None:
                self.possible_moves.remove(self.centre)

    def get_nm_depth(self, trans=False):
        perc_time = (self.total_time + timer() - self.move_start) / self.n**2
        key = (self.n, trans)
        if key in depth_dict:
            base = depth_dict[key]

            if perc_time > 0.98:
                return 0, .98
            elif perc_time > 0.85:
                return base - 2, .85
            elif perc_time > 0.70:
                return base - 1, .70
        else:
            base = 3 if trans else 2
            if perc_time > 0.97:
                print("OUT OF TIME")
                return 0, .97
            elif perc_time > 0.75:
                return base - 1, .70
        
        return base, None

    def get_greedy_move(self):
        if len(self.move_history) == 0:
            return self.get_first_move()
        if len(self.move_history) == 1:
            if self.time_to_steal():
                return _ACTION_STEAL
        moves = list(self.possible_moves)
        np.random.shuffle(moves)
        return max(
            moves,
            key=lambda move: self.evaluate_after_move(move)
        )

    def time_to_steal(self):
        if self.n == 3:
            last_tile = self.move_history[0][0]
            if sorted(last_tile) in [[0, 2], [0, 1]]:
                return True
            else:
                return False
        if self.n == 4:
            return False
        return True

    def get_first_move(self):
        return self.n - 1, 0


    def get_negamax_move(self, prune=False, trans=False, near=None):
        self.move_start = timer()

        if len(self.move_history) == 0:
            return self.get_first_move()
        if len(self.move_history) == 1:
            if self.time_to_steal():
                return _ACTION_STEAL

        if trans:
            return self.get_trans_move(near)

        self.evaluations = 0
        best_move_val = -inf
        # manage moves
        if near:
            all_moves = self.possible_moves
            self.possible_moves = self.get_occupied_neighbours(max_depth=near)
        moves = list(self.possible_moves)
        np.random.shuffle(moves)
        start_time = timer()
        for move in moves:
            self.nm_depth, perc = self.get_nm_depth()
            if self.nm_depth <= 0:
                best_move = self.get_greedy_move()
                if perc: print(perc)
                break
            value = self.evaluate_negamax(move, prune)
            if value > best_move_val:
                best_move = move
                best_move_val = value
            if best_move_val >= _WIN_VALUE:
                if perc: print(perc)
                break
        if perc: print(perc)
        if near:
            self.possible_moves = all_moves

        self.total_evals += self.evaluations
        # print(f"Evals: {self.evaluations}")
        # print(f"Time: {self.total_time + (timer() - start_time)}\n")
        return best_move

    def evaluate_negamax(self, move, prune):
        self.update(self.player, move_to_action(move))
        if prune:
            neg_value = self.alpha_beta(
                self.nm_depth, _OPPONENT[self.player], -_WIN_VALUE, _WIN_VALUE
            )
        else:
            neg_value = self.negamax(
                self.nm_depth, _OPPONENT[self.player]
            )
        self.undo_last_move()
        return -neg_value

    def evaluate_after_move(self, move):
        self.update(self.player, move_to_action(move))
        value = self.evaluate(self.player)
        self.undo_last_move()
        return value

    def negamax(self, depth: int, player):
        if depth == 0 or self.game_over():
            self.evaluations += 1
            return self.evaluate(player)
        best_value = -inf
        for move in self.possible_moves:
            self.update(player, move_to_action(move))
            node_value = -self.negamax(
                depth - 1, _OPPONENT[player]
            )
            if node_value > best_value:
                best_value = node_value
            self.undo_last_move()
        return best_value

    def alpha_beta(self, depth: int, player, alpha: float, beta: float):
        if depth == 0 or self.game_over():
            self.evaluations += 1
            return self.evaluate(player)
        heap = [(-self.num_neighbors(move), move) for move in self.possible_moves]
        heapq.heapify(heap)
        while heap:
            move = heapq.heappop(heap)[1]
            self.update(player, move_to_action(move))
            node_value = -self.alpha_beta(
                depth - 1, _OPPONENT[player], -beta, -alpha
            )
            self.undo_last_move()
            if node_value > alpha:
                alpha = node_value
            if alpha >= beta:
                break
        return alpha


    def get_trans_move(self, near=None):
        
        self.nm_depth, perc = self.get_nm_depth(trans=True)
        if perc: print(perc)
        if self.nm_depth <= 0:
            return self.get_greedy_move()
        self.evaluations = 0
        
        # manage moves
        if near and self.n > 3:
            all_moves = self.possible_moves
            self.possible_moves = self.get_occupied_neighbours(max_depth=near)
            
        self.transtbl = dict()
        best_move = self.ab_trans(
            self.nm_depth, self.player, -_WIN_VALUE, _WIN_VALUE
        )

        if near and self.n > 3:
            self.possible_moves = all_moves
        # print(f"Evals: {self.evaluations}")
        # print(f"Time: {self.total_time + (timer() - start_time)}\n")
        return best_move


    def ab_trans(self, depth: int, player, alpha: float, beta: float):
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
            return self.evaluate(player)
        
        value = -inf
        best_move = None
        heap = [(-self.num_neighbors(move), move) for move in self.possible_moves]
        heapq.heapify(heap)
        while heap:
            if depth == self.nm_depth and timer() - self.move_start > 10:
                return self.get_greedy_move()
            move = heapq.heappop(heap)[1]
            self.update(player, move_to_action(move))
            node_value = -self.ab_trans(
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

        return alpha if depth < self.nm_depth else best_move


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
        return neighbors + random.uniform(0, 0.5)

    def has_neighbour(self, move):
        for dx, dy in _NEIGHBOUR_OFFSETS:
            x = move[0] + dx
            y = move[1] + dy
            if (0 <= x < self.n and 0 <= y < self.n and self[(x, y)]):
                return 1
        return 0

    def get_occupied_neighbours(self, max_depth):
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
        self.state_counter[self.zobrist] += 1
    
    def update_zobrist(self, player, tile):
        self.zobrist ^= self.z_table[tile[0]][tile[1]][0 if player == "red" else 1] 

    def state_count(self):
        return self.state_counter[self.zobrist]

    def incr_state(self):
        self.state_counter[self.zobrist] += 1
    
    def decr_state(self):
        self.state_counter[self.zobrist] -= 1
