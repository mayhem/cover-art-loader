#!/usr/bin/env python3

from PIL import Image

img = Image.effect_mandelbrot((1000,1000), (-1,-1, 1, 1), 100)
img.save("mandelbrot.jpg")
