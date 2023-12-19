#!/usr/bin/env python3
import json
import sys
from PIL import Image, ImageDraw

from compose import CoverArtMosaic
from base import create_rectangular_base_image, create_circular_base_image


def create_base_images(radius, tile_size):
    border = radius // 10 

    black = create_circular_base_image(radius, max_sv=.9, more_black=True)
    white = create_circular_base_image(radius, max_sv=.9, more_black=False)

    width = (radius * 4) + (border * 3)
    height = (radius * 2) + (border * 2)

    base = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    base.paste(black, (border, border))
    base.paste(white, ((radius * 2) + (border * 2), border))

    mask = Image.new('RGBA', (width * tile_size, height * tile_size), (255, 255, 255, 0))
    mask_draw = ImageDraw.Draw(mask)
    tborder = border * tile_size
    tradius = (radius * tile_size)

    bbox_left = (tborder,
                 tborder,
                 tborder + tradius + tradius,
                 tborder + tradius + tradius)
    bbox_right = (tborder * 2 + (tradius * 2),
                  tborder,
                  tborder * 2 + (tradius * 4),
                  tborder + tradius + tradius)

    bbox_left = (bbox_left[0] + tile_size, bbox_left[1] + tile_size, bbox_left[2] - tile_size, bbox_left[3] - tile_size)
    bbox_right = (bbox_right[0] + tile_size, bbox_right[1] + tile_size, bbox_right[2] - tile_size, bbox_right[3] - tile_size)

    mask_draw.ellipse(bbox_left, fill=(0, 0, 0))
    mask_draw.ellipse(bbox_right, fill=(0, 0, 0))

    mask.save("mask.png")

    return base, mask, bbox_left, bbox_right

def add_logos(mosaic):

    lb = Image.open("logos/ListenBrainz_logo.png")

    lb_width = mosaic.size[0] // 6
    lb_height = lb_width * lb.size[1] // lb.size[0]

    lb = lb.resize((lb_width, lb_height))
   
    x = (mosaic.size[0] // 2) - (lb.size[0] // 2)
    y = lb.size[1]
    mosaic.paste(lb, (x, y))
 

    ia = Image.open("logos/internet-archive-logo.png")

    ia_width = mosaic.size[0] // 5
    ia_height = ia_width * ia.size[1] // ia.size[0]

    ia = ia.resize((ia_width, ia_height))
   
    x = (mosaic.size[0] // 2) - (ia.size[0] // 2)
    y = mosaic.size[1] - int(ia.size[1] * 2.5)
    mosaic.paste(ia, (x, y))

    return mosaic


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: compose.py <tile size> <radius> <output image JPG> <year>")
        sys.exit(-1)

    tile_size = int(sys.argv[1])
    radius = int(sys.argv[2])
    output_file = sys.argv[3]
    year = int(sys.argv[4])
    cache_dir = f"cache-{year}"

    base_image, base_mask, bbox_left, bbox_right = create_base_images(radius, tile_size)
    mos = CoverArtMosaic(cache_dir, base_image, tile_size, year)
    mosaic, json_data = mos.create(dry_run=False)
    mosaic.save("pre-mask.png")

    with open(output_file + ".json", "w") as f:
        f.write(json.dumps(json_data))

    transparent = Image.new(size=mosaic.size, color=(0, 0, 0, 0), mode="RGBA")
    mosaic = Image.composite(mosaic, transparent, base_mask)
    mosaic = add_logos(mosaic)

    draw = ImageDraw.Draw(mosaic)
    draw.rectangle(bbox_left, outline=(0,0,0,255), width=1)
    draw.rectangle(bbox_right, outline=(0,0,0,255), width=1)

    mosaic.save(output_file)
