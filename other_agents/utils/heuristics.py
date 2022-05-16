from utils.helper_functions import get_neighbours

_NEIGHBOUR_OFFSETS = (
    (0, 1),
    (0, -1),
    (1, 0),
    (-1, 0),
    (1, -1),
    (-1, 1)
)
_OPPONENT = {"red": "blue", "blue": "red", None: None}
_WIN_VALUE = 1e7
_EVEN_CENTRE_TILES = lambda n: [
    (n // 2, n // 2),
    (n // 2, n // 2 - 1),
    (n // 2 - 1, n // 2),
    (n // 2 - 1, n // 2 - 1)
]


def captures(tracking_board, player):
    return (
        tracking_board.tiles_captured 
        if player == tracking_board.player else 
        -tracking_board.tiles_captured
    )

def longest_edge_branch(tracking_board, player, from_start=True):
    if from_start:
        edge_squares = tracking_board.start_squares[player]
    else:
        edge_squares = tracking_board.end_squares[player]
    q = [coord for coord in edge_squares if tracking_board[coord] == player]
    seen = set(q)
    longest = 0
    while q:
        coord = q.pop(-1)
        length = (coord[0] if player == "red" else coord[1]) + 1
        if not from_start:
            length = tracking_board.n - length + 1
        longest = max(longest, length)
        for neighbour in get_neighbours(coord, tracking_board, player, seen):
            q.append(neighbour)
    return longest

def longest_branch(tracking_board, player):
    seen = set()
    score = 0
    if player == "red":
        height = lambda move: move[0]
    else:
        height = lambda move: move[1]
    for tile in tracking_board.tiles[player]:
        if tile in seen:
            continue
        seen.add(tile)
        q = [tile]
        max_height = min_height = height(tile) 
        while q:
            coord = q.pop(-1)
            max_height = max(max_height, height(coord))
            min_height = min(min_height, height(coord))
            for neighbour in get_neighbours(coord, tracking_board, player, seen):
                q.append(neighbour)
        if max_height - min_height == tracking_board.n - 1:
            return _WIN_VALUE
        score = max(score, max_height - min_height + 1)
    return score

def branch_eval(tracking_board, player):
    us = longest_branch(tracking_board, player)
    them = longest_branch(tracking_board, _OPPONENT[player])
    if us == _WIN_VALUE:
        return _WIN_VALUE
    elif them  == -_WIN_VALUE:
        return -_WIN_VALUE
    return us - them

def edge_branch_eval(tracking_board, player):
    us = longest_edge_branch(tracking_board, player, from_start=True)
    them = longest_edge_branch(tracking_board, _OPPONENT[player], from_start=True)
    if us == tracking_board.n:
        return _WIN_VALUE
    elif them == tracking_board.n:
        return -_WIN_VALUE
    return (
        us -
        them +
        longest_edge_branch(tracking_board, player, from_start=False) -
        longest_edge_branch(tracking_board, _OPPONENT[player], from_start=False)
    )

def edge_branch_capture_eval(tracking_board, player):
    edge_branch = edge_branch_eval(tracking_board, player)
    if edge_branch == _WIN_VALUE:
        return _WIN_VALUE
    if edge_branch == -_WIN_VALUE:
        return -_WIN_VALUE
    return( 
        edge_branch +
        captures(tracking_board, player)
    )

def branch_capture_eval(tracking_board, player):
    branch = branch_eval(tracking_board, player)
    if branch == _WIN_VALUE:
        return _WIN_VALUE
    if branch == -_WIN_VALUE:
        return -_WIN_VALUE
    return (
        branch + 
        captures(tracking_board, player)
    )

def branch_capture_axis_eval(tracking_board, player):
    branch = branch_eval(tracking_board, player)
    if branch == _WIN_VALUE:
        return _WIN_VALUE
    if branch == -_WIN_VALUE:
        return -_WIN_VALUE
    return (
        branch + 
        captures(tracking_board, player) +
        axis_advantage(tracking_board, player) / 100
    )

def edge_branch_capture_axis_eval(tracking_board, player):
    branch_adv = edge_branch_eval(tracking_board, player)
    if branch_adv == _WIN_VALUE:
        return _WIN_VALUE
    if branch_adv == -_WIN_VALUE:
        return -_WIN_VALUE
    return (
        branch_adv +
        captures(tracking_board, player) +
        axis_advantage(tracking_board, player) / 100
    )

def edge_branch_capture_edges_eval(tracking_board, player):
    edge_branch = edge_branch_eval(tracking_board, player)
    if edge_branch == _WIN_VALUE:
        return _WIN_VALUE
    if edge_branch == -_WIN_VALUE:
        return -_WIN_VALUE
    return (
        edge_branch +
        captures(tracking_board, player) * 2 +
        edges_advantage(tracking_board, player) / 10
    )

def centre_advantage(tracking_board, player):
    n = tracking_board.n
    if n % 2 == 0:
        # four pieces in the centre
        centre = _EVEN_CENTRE_TILES(n)
    else:
        centre = n // 2, n // 2
        centre_tiles = [centre]
        for x, y in _NEIGHBOUR_OFFSETS:
            centre_tiles.append((centre[0] + x, centre[1] + y))
    centre_adv = 0
    for tile in centre_tiles:
        centre_adv += (tracking_board[tile] == player)
        centre_adv -= (tracking_board[tile] == _OPPONENT[player])
    return centre_adv

def axis_advantage(tracking_board, player):
    score = 0
    ideal = tracking_board.n - 1
    for our_tile in tracking_board.tiles[player]:
        score += (-2 < sum(our_tile) - ideal < 2)
    for their_tile in tracking_board.tiles[_OPPONENT[player]]:
        score -= (-2 < sum(their_tile) - ideal < 2)
    return score

def edges_advantage(tracking_board, player):
    score = 0
    for tile in tracking_board.tiles[player]:
        num += (
            tile[0] == 0 or 
            tile[0] == tracking_board.n - 1 or
            tile[1] == 0 or 
            tile[1] == tracking_board.n - 1
        )
    for tile in tracking_board.tiles[_OPPONENT[player]]:
        score -= (
            tile[0] == 0 or 
            tile[0] == tracking_board.n - 1 or
            tile[1] == 0 or 
            tile[1] == tracking_board.n - 1
        )
    return score
