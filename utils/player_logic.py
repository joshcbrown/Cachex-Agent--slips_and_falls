def evaluate(tracking_board):
    return 0

def parse(action):
    if len(action) == 1:
        return action[0], None
    else:
        return action[0], (action[1], action[2])
