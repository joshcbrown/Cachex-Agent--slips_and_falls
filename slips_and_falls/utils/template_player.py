from slips_and_falls.final_tracker import FinalTracker
from slips_and_falls.utils.helper_functions import move_to_action
from slips_and_falls.utils.heuristics import longest_edge_branch
from random import randint, seed
from functools import partial
from time import perf_counter as timer

_ACTION_PLACE = "PLACE"


class TemplatePlayer:
    def __init__(self, player, n, ptype: str, pname: str):
        self.tracking_board = FinalTracker(player, self.evaluate, n)
        self.get_move = self.tracking_board.get_transtbl_move
        self.ptype = ptype
        self.pname = pname

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
