_NEIGHBOUR_OFFSETS = (
    (0, 1),
    (0, -1),
    (1, 0),
    (-1, 0),
    (1, -1),
    (-1, 1)
)
_OPPONENT = {"red": "blue", "blue": "red", None: None}
_WIN_VALUE = 1e9


def edge_branch_advantage(tracking_board, player):
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


def longest_edge_branch(tracking_board, player, from_start):
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
        for neighbour in _get_neighbours(coord, tracking_board, player, seen):
            q.append(neighbour)
    return longest


def branch_advantage(tracking_board, player):
    us = branching_score(tracking_board, player)
    them = branching_score(tracking_board, _OPPONENT[player])
    if us == _WIN_VALUE:
        return _WIN_VALUE
    elif them == _WIN_VALUE:
        return -_WIN_VALUE
    return us - them


def branching_score(tracking_board, player):
    seen = set()
    height_seen = [False]*tracking_board.n
    score = 0
    if player == "red":
        height = lambda move: move[0]
    else:
        height = lambda move: move[1]
    for tile in tracking_board.tiles[player]:
        if tile in seen and (not height_seen[height(tile)]):
            continue
        seen.add(tile)
        q = [tile]
        max_height = min_height = height(tile) 
        while q:
            coord = q.pop(-1)
            height_seen[height(coord)] = True
            max_height = max(max_height, height(coord))
            min_height = min(min_height, height(coord))
            for neighbour in _get_neighbours(coord, tracking_board, player, seen):
                q.append(neighbour)
        if max_height - min_height == tracking_board.n - 1:
            return _WIN_VALUE
        score += (max_height - min_height + 0.75)**1.5
    return score

def _get_neighbours(coord, tracking_board, player, seen):
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


def branch_capture(tracking_board, player):
    branch_adv = branch_advantage(tracking_board, player)
    if branch_adv == _WIN_VALUE:
        return _WIN_VALUE
    if branch_adv == -_WIN_VALUE:
        return -_WIN_VALUE
    capture_advantage = (
        tracking_board.tiles_captured 
        if player == tracking_board.player else 
        -tracking_board.tiles_captured
    )
    return (
        2 * tracking_board.n * capture_advantage 
        + branch_adv 
        + axis_advantage(tracking_board, player) / 30
    )

def edge_branch_capture(tracking_board, player):
    branch_adv = edge_branch_advantage(tracking_board, player)
    if branch_adv == _WIN_VALUE:
        return _WIN_VALUE
    if branch_adv == -_WIN_VALUE:
        return -_WIN_VALUE
    capture_advantage = (tracking_board.tiles_captured if player == tracking_board.player
                         else - tracking_board.tiles_captured)
    return (
        capture_advantage +
        branch_adv
    )



def centre_advantage(tracking_board, player):
    n = tracking_board.n
    if n % 2 == 0:
        # four pieces in the centre
        centre_tiles = [
            (n // 2, n // 2),
            (n // 2, n // 2 - 1),
            (n // 2 - 1, n // 2),
            (n // 2 - 1, n // 2 - 1)
        ]
    else:
        centre = n // 2, n // 2
        centre_tiles = [centre]
        for x, y in _NEIGHBOUR_OFFSETS:
            centre_tiles.append((centre[0] + x, centre[1] + y))
    centre_player = 0
    centre_opp = 0
    for tile in centre_tiles:
        centre_player += (1 if tracking_board[tile] == player else 0)
        centre_opp += (1 if tracking_board[tile] == _OPPONENT[player] else 0)
    return centre_player - centre_opp


def axis_advantage(tracking_board, player):
    score = 0
    ideal = tracking_board.n - 1
    for our_tile in tracking_board.tiles[player]:
        score -= abs(sum(our_tile) - ideal)
    for their_tile in tracking_board.tiles[_OPPONENT[player]]:
        score += abs(sum(their_tile) - ideal)
    return score


def new_heuristic(tracking_board, player):
    return branch_capture(tracking_board, player) + centre_advantage(tracking_board, player)
