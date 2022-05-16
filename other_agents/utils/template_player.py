from greedy.greedy_tracker import GreedyTracker
from negamaxs.nm_tracker import NegamaxTracker
from transtbl.transtbl_tracker import TranstblTracker
from utils.helper_functions import move_to_action
from random import randint, seed
from functools import partial
from time import perf_counter as timer
from utils.heuristics import longest_edge_branch

_ACTION_PLACE = "PLACE"


class TemplatePlayer:
    def __init__(self, player, n, ptype: str, pname: str):
        self.player = player
        self.n = n
        self.ptype = ptype
        self.pname = pname
        if ptype == "greedy":
            seed(1)
            self.tracking_board = GreedyTracker(player, self.evaluate, n)
            self.get_move = self.tracking_board.get_greedy_move
        elif ptype == "negamax":
            self.tracking_board = NegamaxTracker(player, self.evaluate, n)
            self.get_move = partial(
                self.tracking_board.get_negamax_move
            )
        elif ptype == "ab":
            self.tracking_board = NegamaxTracker(player, self.evaluate, n)
            self.get_move = partial(
                self.tracking_board.get_negamax_move, prune=True
            )
        elif ptype == "within2":
            self.tracking_board = NegamaxTracker(player, self.evaluate, n)
            self.get_move = partial(
                self.tracking_board.get_negamax_move, prune=True, within2=True
            )
        elif ptype == "transtbl":
            self.tracking_board = TranstblTracker(player, self.evaluate, n)
            self.get_move = self.tracking_board.get_transtbl_move
        else:
            print(f"invalid player type: {ptype}")
            exit()

    # default to random eval, overriden in subclasses
    def evaluate(self, player):
        return randint(0, int(1e6))

    def action(self):
        """
        Called at the beginning of your turn. Based on the current state
        of the game, select an action to play.
        """
        time = timer()
        choice = self.get_move()
        self.tracking_board.total_time += timer() - time
        # if self.ptype != "greedy":
        #     print(f"{self.ptype} evals: {self.tracking_board.evaluations}")
        #     print(f"{self.ptype} timer: {self.tracking_board.total_time}\n")
        #     if self.ptype == "transtbl":
        #         print(self.tracking_board.state_count())
        return move_to_action(choice)

    def turn(self, player, action):
        """
        Called at the end of each player's turn to inform this player of 
        their chosen action. Update your internal representation of the 
        game state based on this. The parameter action is the chosen 
        action itself. 
        
        Note: At the end of your player's turn, the action parameter is
        the same as what your player returned from the action method
        above. However, the referee has validated it at this point.
        """
        self.tracking_board.update(player, action)
        
        for pl in ["red", "blue"]:
            if longest_edge_branch(self.tracking_board, pl) == self.n:
                if self.player == pl:
                    print(f"{self.ptype} {self.pname} WIN!")
                else:
                    print(f"{self.ptype} {self.pname} LOSS")
                print(
                    f"N: {self.n} ; " +
                    f"TIME: {round(self.tracking_board.total_time, 1)} ; " +
                    f"PROP: {round(self.tracking_board.total_time/(self.n**2), 2)} ; " +
                    f"LEN: {len(self.tracking_board.move_history)}"
                )
                if self.ptype != "greedy":
                    print(f"EVALS: {self.tracking_board.total_evals}")
                if self.player == "blue":
                    print()
