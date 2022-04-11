import pygame
from math import sqrt, sin, cos, pi

def draw_hexagon(surface, centre_x, centre_y, side_length, colour):
    points = []
    for i in range(6):
        angle = pi/3 * i - pi/6
        points.append([centre_x + side_length * cos(angle),
                       centre_y + side_length * sin(angle)])
    hexagon = pygame.draw.polygon(surface, colour, points)
    return hexagon

def draw_row(number, side_length, start, window):
    width = sqrt(3) * side_length
    current_centre = start.copy()
    hexagons = []
    for i in range(number):
        hexagons.append(draw_hexagon(window, current_centre[0], current_centre[1], side_length))
        current_centre[0] += width
    return hexagons