_ACTION_PLACE = "PLACE"
_NEIGHBOUR_OFFSETS = (
    (0, 1),
    (0, -1),
    (1, 0),
    (-1, 0),
    (1, -1),
    (-1, 1)
)

def move_to_action(move):
    if type(move) == str:
        return move,
    return _ACTION_PLACE, int(move[0]), int(move[1])

def action_to_move(action):
    if len(action) == 1:
        return "STEAL"
    return action[1], action[2]

def get_neighbours(coord, tracking_board, player, seen):
    neighbours = []
    for x, y in _NEIGHBOUR_OFFSETS:
        new_x = coord[0] + x
        new_y = coord[1] + y
        new_coord = (new_x, new_y)
        if (0 <= new_x < tracking_board.n and 0 <= new_y < tracking_board.n and
                new_coord not in seen and tracking_board[new_coord] == player):
            neighbours.append(new_coord)
            seen.add(new_coord)
    return neighbours
