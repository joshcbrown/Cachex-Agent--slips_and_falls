from utils.tracking_board import TrackingBoard
from utils.helper_functions import move_to_action

_ACTION_PLACE = "PLACE"
_ACTION_STEAL = "STEAL"
_ACTION_TYPES = {(_ACTION_STEAL,), (_ACTION_PLACE, int, int)}


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
        while True:
            next_move_input = input("put yo shit in:\n")
            penis = next_move_input.split()
            if len(penis) == 1:
                next_move = next_move_input
            elif len(penis) == 2:
                next_move = penis
            else:
                print("invalid format 1")
                continue
            next_action = move_to_action(next_move)
            atype, *aargs = next_action
            action_type = (atype, *(type(arg) for arg in aargs))
            if action_type in _ACTION_TYPES:
                break
            print("invalid format 2")
        # print(self.tracking_board.possible_moves)
        return next_action

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
