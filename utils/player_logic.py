_ACTION_PLACE = "PLACE"

def move_to_action(move):
    if type(move) == str:
        return move,
    return _ACTION_PLACE, int(move[0]), int(move[1])

def action_to_move(action):
    if len(action) == 1:
        return "STEAL"
    return action[1], action[2]

def parse(action):
    if len(action) == 1:
        return action[0], None
    else:
        return action[0], (action[1], action[2])
