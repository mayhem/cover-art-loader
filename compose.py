#!/usr/bin/env python3

from collections import defaultdict
import io
import os
from random import randint
import sys
import json

from PIL import Image, ImageDraw
from tqdm import tqdm

from cache import CoverArtLoader


class CoverArtMosaic:

    COLOR_THRESHOLD = 20
    QUERY_LIMIT = 1000

    def __init__(self, cache_dir, base_image, tile_size, year):
        self.cache_dir = cache_dir
        self.tile_size = tile_size
        self.base_image = base_image
        self.year = year

        self.image_size_x = tile_size * self.base_image.width
        self.image_size_y = tile_size * self.base_image.height

    def create(self, dry_run=False):

        used = defaultdict(int)

        print("Create image size %d * %d with tile size %d." % (self.image_size_x, self.image_size_y, self.tile_size))
        cal = CoverArtLoader("cache-2023", self.year)
        composite = Image.new(mode="RGBA", size=(self.image_size_x, self.image_size_y), color=(0, 0, 0, 0))
        data = []

        if dry_run:
            draw = ImageDraw.Draw(composite)

        with tqdm(total=self.base_image.height * self.base_image.width) as pbar:
            for y in range(self.base_image.height):
                for x in range(self.base_image.width):

                    color = self.base_image.getpixel((x, y))
                    if color[3] == 0:
                        pbar.update(1)
                        continue

                    if not dry_run:
                        threshold = self.COLOR_THRESHOLD
                        for tries in range(5):
                            releases = cal.lookup(threshold, self.QUERY_LIMIT, color[0], color[1], color[2])
                            if len(releases) == 0:
                                threshold *= 2
                                continue
                            else:
                                break

                        if len(releases) == 0:
                            continue

                        # Pick a random release
                        release = releases[randint(0, len(releases) - 1)]
                        used[release["release_mbid"]] += 1

                        data.append({
                            "x1": x * self.tile_size,
                            "y1": y * self.tile_size,
                            "x2": (x + 1) * self.tile_size,
                            "y2": (y + 1) * self.tile_size,
                            "name": "%s by %s" % (release["release_name"], release["artist_credit_name"]),
                            "release_mbid": release["release_mbid"]
                        })

                        path = cal.cache_path(release["release_mbid"])
                        cover = Image.open(path)
                        tile = cover.resize((self.tile_size, self.tile_size))

                    else:
                        tile = Image.new(mode="RGBA",
                                         size=(self.tile_size, self.tile_size),
                                         color=(color[0], color[1], color[2], 255))

                    composite.paste(tile, (self.tile_size * x, self.tile_size * y))

                    pbar.update(1)

            return composite, data
