import random
import numpy as np
from math import inf
from referee.board import Board
from utils.helper_functions import parse, action_to_move, move_to_action
from utils.heuristics import longest_edge_branch, centre_advantage
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
_ACTION_PLACE = "PLACE"
_OPPONENT = {"red": "blue", "blue": "red", None: None}
_WIN_VALUE = 1e9


class TrackingBoard(Board):
    def __init__(self, player, evaluate, n):
        super().__init__(n)
        np.random.seed(0)
        random.seed(0)
        self.evaluations = 0
        self.total_time = 0
        self.player = player
        self.evaluate = evaluate
        self.n = n
        self.nm_depth = self.get_nm_depth(self.n)
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
        self.possible_moves.remove(_ACTION_STEAL)
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
        self.tiles_captured += (1 if player == self.player else -1)
        tile = self.tiles[_OPPONENT[player]].pop()
        self.tiles[player].add((tile[1], tile[0]))
        self.update_zobrist(_OPPONENT[player], tile)
        self.update_zobrist(player, (tile[1], tile[0]))

    def unswap(self, player):
        self.swap()
        self.possible_moves = {(r, p) for p, r in self.possible_moves}
        self.possible_moves.add(_ACTION_STEAL)
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
        self.update_zobrist(player, coord)
        if len(last_captures) != 0:
            for captured_coord in last_captures:
                self[captured_coord] = _OPPONENT[player]
                self.tiles[_OPPONENT[player]].add(captured_coord)
                self.possible_moves.remove(captured_coord)
                self.tiles_captured -= (1 if player == self.player else -1)
                self.update_zobrist(_OPPONENT[player], captured_coord)
        elif len(self.move_history) == 0:
            self.possible_moves.remove(_ACTION_STEAL)
            if self.centre is not None:
                self.possible_moves.remove(self.centre)
        elif len(self.move_history) == 1:
            self.possible_moves.add(_ACTION_STEAL)

    def time_to_steal(self):
        return True 

    def get_nm_depth(self, n):
        if n == 3:
            return 9
        if n == 4:
            return 4
        if n == 5:
            return 3
        else:
            return 2

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

    def get_negamax_move(self, prune=False, trans=False, near=None):
        if len(self.move_history) == 0:
            return 0, self.n - 1
        if len(self.move_history) == 1:
            return _ACTION_STEAL if self.time_to_steal() else self.centre

        time_left = self.n**2 - self.total_time
        if self.total_time > self.n**2 * 0.75:
           self.nm_depth = self.get_nm_depth(self.n) - 1
        start_time = timer()
        self.evaluations = 0
        
        best_move_val = -inf
        # manage moves
        if near:
            all_moves = self.possible_moves
            self.possible_moves = self.get_occupied_neighbours(max_depth=near)
        if trans:
            self.transtbl = dict()
        moves = list(self.possible_moves)
        np.random.shuffle(moves)
        for move in moves:
            # if there's only 1 seconds left give up on nm
            if time_left - (timer() - start_time) < 1:
                self.possible_moves = all_moves
                return self.get_greedy_move()
            value = self.evaluate_negamax(move, prune, trans)
            if value > best_move_val:
                best_move = move
                best_move_val = value
            if best_move_val == _WIN_VALUE:
                break
        if near:
            self.possible_moves = all_moves
        # print(f"Anticipated sequence: {best_children}")
        # print(f"Move val: {best_move_val}")
        # print(f"Evals: {self.evaluations}")
        # print(f"Time: {self.total_time + (timer() - start_time)}\n")
        return best_move

    def evaluate_negamax(self, move, prune, trans):
        self.update(self.player, move_to_action(move))
        if trans:
            neg_value = self.ab_trans(
                self.nm_depth, _OPPONENT[self.player], -_WIN_VALUE, _WIN_VALUE
            )
        elif prune:
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
        heap = [(0, move) for move in self.possible_moves]
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
        heap = [(-self.num_neighbors(move), move) for move in self.possible_moves]
        heapq.heapify(heap)
        while heap:
            move = heapq.heappop(heap)[1]
            self.update(player, move_to_action(move))
            node_value = -self.ab_trans(
                depth - 1, _OPPONENT[player], -beta, -alpha
            )
            value = max(value, node_value)
            alpha = max(alpha, node_value)
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
        for tile in self.tiles["red"]:
            self.update_zobrist("red", tile)
        for tile in self.tiles["blue"]:
            self.update_zobrist("blue", tile)
    
    def update_zobrist(self, player, tile):
        self.zobrist ^= self.z_table[tile[0]][tile[1]][0 if player == "red" else 1] 
