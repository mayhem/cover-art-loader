#!/usr/bin/env python3

from colorsys import hsv_to_rgb
from math import sin, cos, radians

from PIL import Image
import numpy as np

def save_image(png_file, width, height, bitmap, mode="RGB"):

    b_array = bytearray()
    for y in range(height):
        for x in range(width):
            b_array += bytes(bitmap[y][x])

    img = Image.frombytes(mode, (width, height), b_array)
    img.save(png_file)


def create_rectangular_base_image(png_file, width, height, max_sv):

    bitmap = [ [ (0, 0, 0) for x in range(width) ] for y in range(height) ]
    for x in range(width):
        for y in range(height):
            if y < height / 2:
                s = ((y / height) * 2.0) * max_sv
                v = max_sv
            else:
                s = max_sv
                v = (max_sv * 2) - ((y / height * 2.0) * max_sv)

            h = x / float(width)
            rgb = hsv_to_rgb(h,s,v)
            bitmap[y][x] = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

    save_image(png_file, width, height, bitmap)


def create_circular_base_image(png_file, radius, max_sv, more_black=True):

    dia = radius * 2
    bitmap = [ [ (0, 0, 0, 0) for x in range(dia) ] for y in range(dia) ]

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

            x = int((cos(radians(t/scale)) * r) + radius)
            y = int((sin(radians(t/scale)) * r) + radius)

            rgb = hsv_to_rgb(t / (360 * scale), s, v)
            bitmap[y][x] = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 255)

    save_image(png_file, dia, dia, bitmap, "RGBA")

#create_rectangular_base_image("base.png", width=200, height=148, max_sv=.7)
create_circular_base_image("base-circular-black.png", 200, max_sv=.8, more_black=True)
create_circular_base_image("base-circular-white.png", 200, max_sv=.8, more_black=False)
