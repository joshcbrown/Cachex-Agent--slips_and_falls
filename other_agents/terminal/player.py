from other_agents.utils.helper_functions import move_to_action
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
        self.player = player
        self.n = n

    def action(self):
        """
        Called at the beginning of your turn. Based on the current state
        of the game, select an action to play.
        """
        while True:
            next_move_input = input("put your move in e.g. '1 3' or 'STEAL':\n")
            move_str = next_move_input.split()
            if len(move_str) == 1:
                next_move = next_move_input
            elif len(move_str) == 2:
                next_move = move_str
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
        pass
