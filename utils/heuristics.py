NEIGHBOUR_OFFSETS = (
    (0, 1),
    (0, -1),
    (1, 0),
    (-1, 0),
    (1, -1),
    (-1, 1)
)

def longest_branch(tracking_board, player, from_start):
    edge_squares = tracking_board.start_squares if from_start else tracking_board.end_squares
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

def _get_neighbours(coord, tracking_board, player, seen):
        neighbours = []
        for x, y in NEIGHBOUR_OFFSETS:
            new_x = coord[0] + x
            new_y = coord[1] + y
            new_coord = (new_x, new_y)
            # check that the new point is not outside the board and the tile
            # isn't occupied by an obstacle
            if (0 <= new_x < tracking_board.n and 
                0 <= new_y < tracking_board.n and 
                new_coord not in seen and tracking_board[new_coord] == player):
                neighbours.append(new_coord)
                seen.add(new_coord)
        return neighbours

            
