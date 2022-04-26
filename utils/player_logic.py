from referee import board

def get_possible_moves(board):
    # TODO: numpy way
    moves = [
        ("PLACE", r, q)
        for r in range(board.n) 
        for q in range(board.n)
        if not board.is_occupied((r, q))
    ]
    if len(moves) == board.n ** 2 - 1:
        moves.append(("STEAL",))
    return moves

def evaluate(board):
    return 0

def parse(action):
    if len(action) == 1:
        return action[0], None
    else:
        return action[0], (action[1], action[2])
