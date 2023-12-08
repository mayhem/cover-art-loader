#!/usr/bin/env python3

from colorsys import hsv_to_rgb

def create_base_image():

    width = 10
    height = 10

    bitmap = [ [ 0 for x in range(width) ] for y in range(height) ]
    for x in range(width):
        for y in range(height):
            if y < height / 2:
                v = 1.0 - (y / height * 2.0)
                s = 0
            else:
                v = 0
                s = ((y / height) - .5) * 2.0

            h = x / float(width)
            print(h,s,v)

            rgb = hsv_to_rgb(h,s,v)
            bitmap[y][x] = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

    with open("test.ppm", "w") as f:
        f.write("P3\n")
        f.write(f"{width} {height}\n")
        f.write("255\n")
        for y in range(height):
            for x in range(width):
                f.write("%d %d %d " % (bitmap[y][x][0], bitmap[y][x][1], bitmap[y][x][2]))
            f.write("\n")

create_base_image()
