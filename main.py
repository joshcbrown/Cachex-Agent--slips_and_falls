import pygame
from math import cos, sin, pi, sqrt
from argparse import ArgumentParser
import json

def draw_hexagon(surface, centre_x, centre_y, side_length, colour):
    points = []
    for i in range(6):
        angle = pi/3 * i - pi/6
        points.append([centre_x + side_length * cos(angle),
                       centre_y + side_length * sin(angle)])
    hexagon = pygame.draw.polygon(surface, colour, points)
    return hexagon

def draw_row(number, side_length, start):
    width = sqrt(3) * side_length
    current_centre = start.copy()
    hexagons = []
    for i in range(number):
        hexagons.append(draw_hexagon(window, current_centre[0], current_centre[1], side_length))
        current_centre[0] += width
    return hexagons

def draw_board_dict(n, board_dict):
    start_row = [200, 350]
    hexagons = []
    hexagon_size = 20
    for i in range(n):
        row = []
        curr_hexagon = start_row.copy()
        for j in range(n):
            if (i, j) in board_dict:
                col = board_dict[(i, j)]
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

def main():
    parser = ArgumentParser()
    parser.add_argument('input', help='path to input json file')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="display the chosen path on the board with info")
    args = parser.parse_args()

    with open(args.input) as file:
        data = json.load(file)
    
    # load data into variables
    n = data['n']
    board_dict = {(y, x): c for c, y, x in data['board']}

    clock = pygame.time.Clock()
    run = True
    hexagon_size = 20
    hexagons = []
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                for i, row in enumerate(hexagons):
                    for j, hexagon in enumerate(row):
                        if hexagon.collidepoint(pos):
                            print(f"{i=}, {j=}")
                            board_dict[(i, j)] = "r"
        
        window.fill((255, 255, 255))
        hexagons = draw_board_dict(n, board_dict)
        # row_start = [200, 350]
        # for i in range(3):
        #     row = draw_row(10, 20, row_start)
        #     assert type(row) == list
        #     if len(hexagons) != 3:
        #         hexagons.append(row)
        #     else:
        #         hexagons[i] = row
        #     row_start[0] += sqrt(3) * hexagon_size * .5
        #     row_start[1] -= hexagon_size * 2 * 3/4
            
        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    WIDTH, HEIGHT = 700, 700
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cachex")

    main()