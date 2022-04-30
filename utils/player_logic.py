def evaluate(tracking_board):
    return 0


def move_to_action(move):
    if type(move) == str:
        return move,
    return "PLACE", move[0], move[1]

def action_to_move(action):
    if len(action) == 1:
        return "STEAL"
    return action[1], action[2]

def parse(action):
    if len(action) == 1:
        return action[0], None
    else:
        return action[0], (action[1], action[2])
