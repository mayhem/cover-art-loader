#!/usr/bin/env python3

from colorsys import hsv_to_rgb

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


create_rectangular_base_image("base.png", width=200, height=148, max_sv=.7)
