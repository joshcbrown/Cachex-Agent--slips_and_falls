from hexagons import draw_hexagon
from math import sqrt


class Board():
    def __init__(self, n, board_dict = {}) -> None:
        self.n = n
        self.board_dict = board_dict
    
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

    def make_move(self, y, x, col):
        self.prev_board_dict = self.board_dict.copy()
        if (y, x) in self.board_dict:
            return False
        self.board_dict[(y, x)] = col
        return True
    
    def undo_move(self):
        self.board_dict = self.prev_board_dict
    
