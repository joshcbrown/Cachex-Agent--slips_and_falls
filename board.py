from hexagons import draw_hexagon
from math import sqrt

NEIGHBOUR_OFFSETS = (
    (0, 1),
    (0, -1),
    (1, 0),
    (-1, 0),
    (1, -1),
    (-1, 1)
)

class Board():
    def __init__(self, n, board_dict = {}, prev_board = None) -> None:
        self.n = n
        self.board_dict = board_dict
        self.prev_board = prev_board
    
    def draw(self, hexagon_size, start_row, window):
        start_row = start_row.copy()
        hexagons = []
        for i in range(self.n):
            row = []
            curr_hexagon = start_row.copy()
            for j in range(self.n):
                if (i, j) in self.board_dict:
                    col = self.board_dict[(i, j)]
                    if col == "b":
                        colour = (0, 0, 255)
                    elif col == "r":
                        colour = (255, 0, 0)
                    row.append(draw_hexagon(window, curr_hexagon[0], curr_hexagon[1], hexagon_size, colour))

                else:
                    row.append(draw_hexagon(window, curr_hexagon[0], curr_hexagon[1], hexagon_size, (0, 0, 0)))
                curr_hexagon[0] += sqrt(3) * hexagon_size + hexagon_size / 5
            hexagons.append(row)
            start_row[0] += sqrt(3) * hexagon_size * .5 + hexagon_size / 5
            start_row[1] -= hexagon_size * 1.5 + hexagon_size / 5
        return hexagons

    def attempt_move(self, y, x, col):
        if (y, x) in self.board_dict:
            return None
        new_board_dict = self.board_dict.copy()
        new_board_dict[(y, x)] = col
        new_board = Board(self.n, new_board_dict, self)
        return new_board
    
    def undo_move(self):
        assert self.prev_board is not None
        return self.prev_board
    
    def win(self, col):
        return win(self, col)

def win(board, col):
    not_visited = {(y, x) for (y, x), tile_col in board.board_dict.items() if tile_col == col}
    # define win condition as: red making vertical line, blue making horizontal line

    if col == "b":
        side1_func = lambda _, x: x == 0
        side2_func = lambda _, x: x == board.n - 1
    elif col == "r":
        side1_func = lambda y, _: y == 0
        side2_func = lambda y, _: y == board.n - 1

    # perform dfs
    while len(not_visited) != 0:
        first_tile = not_visited.pop()
        stack = [first_tile]
        touched_side1 = False
        touched_side2 = False
        while len(stack) != 0:
            y, x = stack.pop()
            touched_side1 = touched_side1 or side1_func(y, x)
            touched_side2 = touched_side2 or side2_func(y, x)
            if touched_side1 and touched_side2:
                return True
            for offset_y, offset_x in NEIGHBOUR_OFFSETS:
                new_y = offset_y + y
                new_x = offset_x + x
                if (0 <= new_x and new_x < board.n and
                    0 <= new_y and new_y < board.n and
                    (new_y, new_x) in not_visited):
                    stack.append([new_y, new_x])
                    not_visited.remove((new_y, new_x))
    return False                   
                    