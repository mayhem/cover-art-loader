#!/usr/bin/env python3

from colorsys import hsv_to_rgb
from math import sin, cos, radians

from PIL import Image


def make_image(width, height, bitmap, mode="RGB"):

    b_array = bytearray()
    for y in range(height):
        for x in range(width):
            b_array += bytes(bitmap[y][x])

    return Image.frombytes(mode, (width, height), b_array)


def create_rectangular_base_image(width, height, max_sv):

    bitmap = [[(0, 0, 0) for x in range(width)] for y in range(height)]
    for x in range(width):
        for y in range(height):
            if y < height / 2:
                s = ((y / height) * 2.0) * max_sv
                v = max_sv
            else:
                s = max_sv
                v = (max_sv * 2) - ((y / height * 2.0) * max_sv)

            h = x / float(width)
            rgb = hsv_to_rgb(h, s, v)
            bitmap[y][x] = (int(rgb[0] * 255), int(rgb[1] * 255),
                            int(rgb[2] * 255))

    return make_image(width, height, bitmap)


def create_circular_base_image(radius, max_sv, more_black=True):

    dia = radius * 2
    bitmap = [[(0, 0, 0, 0) for x in range(dia)] for y in range(dia)]

    scale = 20
    for r in range(radius):
        for t in range(360 * scale):
            if more_black:
                if r < radius / 2:
                    s = ((r / radius) * 2.0) * max_sv
                    v = max_sv
                else:
                    s = max_sv
                    v = (max_sv * 2) - ((r / radius * 2.0) * max_sv)
            else:
                if r < radius / 2:
                    v = ((r / radius) * 2.0) * max_sv
                    s = max_sv
                else:
                    v = max_sv
                    s = (max_sv * 2) - ((r / radius * 2.0) * max_sv)

            x = int((cos(radians(t / scale)) * r) + radius)
            y = int((sin(radians(t / scale)) * r) + radius)

            rgb = hsv_to_rgb(t / (360 * scale), s, v)
            bitmap[y][x] = (int(rgb[0] * 255), int(rgb[1] * 255),
                            int(rgb[2] * 255), 255)

    return make_image(dia, dia, bitmap, "RGBA")


black = create_circular_base_image(200, max_sv=.9, more_black=True)
white = create_circular_base_image(200, max_sv=.9, more_black=False)

width = (200 * 4) + (50 * 3)
height = (200 * 2) + (50 * 2)

base = Image.new('RGBA', (width, height), (0, 0, 0, 0))
base.paste(black, (50, 50))
base.paste(white, (500, 50))
base.save("base-image.png")
