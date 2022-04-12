import pygame
from math import sqrt
from argparse import ArgumentParser
from board import Board

def run_game(board, hexagon_size, start_row, surface):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('helvetica', 20)
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
                            new_board = board.make_move(i, j, col)
                            if not new_board:
                                break
                            board = new_board
                            col = switch_colours(col)
                            found = True
                            break
                    if found:
                        break
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_u and board.prev_board is not None:
                    board = board.undo_move()
                    col = switch_colours(col)
        
        surface.fill((255, 255, 255))
        hexagons = board.draw(hexagon_size, start_row, surface)
        if board.win("b"):
            text_surface = font.render("gamestate: blue wins!", False, (0, 0, 255))
        elif board.win("r"):
            text_surface = font.render("gamestate: red wins!", False, (255, 0, 0))
        else:
            text_surface = font.render(f"gamestate: {col} to play", False, (0, 0, 0))
        surface.blit(text_surface, (50, 50))

        pygame.display.update()

def switch_colours(col):
    return "r" if col == "b" else "b"

def main():
    parser = ArgumentParser()
    parser.add_argument('-n', '--n', type=int, default=5)
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="display the chosen path on the board with info")
    args = parser.parse_args()

    # initialise pygame stuff
    WIDTH, HEIGHT = 1000, 1000
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cachex")
    pygame.font.init()
    
    # size is the length from centre to any point and the side length
    hexagon_size = 1600 / (sqrt(3) * (3 * args.n - 1))
    start_row = [100, HEIGHT - 100]
    board = Board(args.n)

    run_game(board, hexagon_size, start_row, window)

    pygame.quit()


if __name__ == '__main__':
    main()
