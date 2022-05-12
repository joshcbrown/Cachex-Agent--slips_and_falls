from utils.tracking_board import TrackingBoard
from utils.helper_functions import move_to_action
from random import randint
from functools import partial
from time import perf_counter as timer
from utils.heuristics import branch_advantage, longest_edge_branch

_ACTION_PLACE = "PLACE"


class TemplatePlayer:
    def __init__(self, player, n, ptype: str):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "red" if your player will
        play as Red, or the string "blue" if your player will play
        as Blue.
        """
        self.player = player
        self.n = n
        self.ptype = ptype
        self.tracking_board = TrackingBoard(player, self.evaluate, n)
        if ptype == "greedy":
            self.get_move = self.tracking_board.get_greedy_move
        elif ptype == "negamax":
            self.get_move = partial(self.tracking_board.get_negamax_move)
        elif ptype == "ab":
            self.get_move = partial(
                self.tracking_board.get_negamax_move, prune=True
            )
        elif ptype == "abn":
            self.get_move = partial(
                self.tracking_board.get_negamax_move, prune=True, near=2
            )
        elif ptype[:4] == "abnt":
            self.get_move = partial(
                self.tracking_board.get_negamax_move, 
                prune=True, near=2, trans=True
            )
        else:
            print(f"invalid player type: {ptype}")
            exit()

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
        # if self.ptype[0:4] == "abnt":
        #     print(f"{self.ptype} evals: {self.tracking_board.evaluations}")
        #     print(f"{self.ptype} timer: {self.tracking_board.total_time}\n")
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
        
        # ensure undo+redo has no effect
        old_z = self.tracking_board.zobrist
        self.tracking_board.undo_last_move()
        self.tracking_board.update(player, action)
        assert self.tracking_board.zobrist == old_z
        
        for pl in ["red", "blue"]:
            if longest_edge_branch(self.tracking_board, pl) == self.n:
                if self.player == pl:
                    print(f"{self.ptype} WIN!")
                else:
                    print(f"{self.ptype} LOSS")
                print(f"N: {self.n} ; TIME: {round(self.tracking_board.total_time, 1)} ; PROP: {round(self.tracking_board.total_time/(self.n**2), 2)}")
                if self.player == "blue":
                    print()
