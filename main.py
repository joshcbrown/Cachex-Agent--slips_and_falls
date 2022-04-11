import pygame
from math import sqrt
from argparse import ArgumentParser
from board import Board

def run_game(board, hexagon_size, start_row):
    clock = pygame.time.Clock()
    col = "r"
    run = True
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                found = False
                for i, row in enumerate(hexagons):
                    for j, hexagon in enumerate(row):
                        if hexagon.collidepoint(pos):
                            print(f"{i=}, {j=}")
                            if not board.make_move(i, j, col):
                                break
                            if col == "r":
                                col = "b"
                            else:
                                col = "r"
                            found = True
                            break
                    if found:
                        break
        

        window.fill((255, 255, 255))
        hexagons = board.draw(hexagon_size, start_row, window)
        pygame.display.update()

def main():
    parser = ArgumentParser()
    parser.add_argument('-n', '--n', type=int, default=5)
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="display the chosen path on the board with info")
    args = parser.parse_args()

    
    # size is the length from centre to any point and the side length
    hexagon_size = 20 * (WIDTH - 100) / (args.n * (20 * sqrt(3) + 19) - 19)
    start_row = [100, HEIGHT - 200]
    board = Board(args.n)
    run_game(board, hexagon_size, start_row)

    pygame.quit()


if __name__ == '__main__':
    WIDTH, HEIGHT = 1000, 1000
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cachex")

    main()