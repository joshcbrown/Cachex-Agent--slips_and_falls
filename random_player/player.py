from referee.board import Board
from utils.tracking_board import TrackingBoard
#from utils.player_logic import evaluate
from numpy import random

_ACTION_PLACE = "PLACE"

class Player:
    def __init__(self, player, n):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "red" if your player will
        play as Red, or the string "blue" if your player will play
        as Blue.
        """
        # random.seed(0)
        self.player = player
        self.n = n
        self.tracking_board = TrackingBoard(player, n)

    def action(self):
        """
        Called at the beginning of your turn. Based on the current state
        of the game, select an action to play.
        """
        idx = random.choice(len(self.tracking_board.possible_moves))
        choice = list(self.tracking_board.possible_moves)[idx]
        if isinstance(choice, str):
            return choice,
        else:
            return _ACTION_PLACE, int(choice[0]), int(choice[1])
    
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
        self.tracking_board.undo_last_move()
        self.tracking_board.update(player, action)
