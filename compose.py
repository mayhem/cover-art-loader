#!/usr/bin/env python3

from collections import defaultdict
import io
import os
from random import randint
import sys
import json

from PIL import Image
from tqdm import tqdm

from cache import CoverArtLoader


class CoverArtMosaic:

    COLOR_THRESHOLD = 100
    QUERY_LIMIT = 10

    def __init__(self, cache_dir, base_image, tile_size, year):
        self.cache_dir = cache_dir
        self.tile_size = tile_size
        self.base_image = base_image
        self.year = year

        self.image_size_x = tile_size * self.base_image.width
        self.image_size_y = tile_size * self.base_image.height

    def create(self):

        used = defaultdict(int)

        print("Create image size %d * %d with tile size %d." %
              (self.image_size_x, self.image_size_y, self.tile_size))
        cal = CoverArtLoader("cache-2023", self.year)
        composite = Image.new(mode="RGBA", size=(self.image_size_x, self.image_size_y), color=(0,0,0,0))
        data = []

        with tqdm(total=self.base_image.height * self.base_image.width) as pbar:
            for y in range(self.base_image.height):
                for x in range(self.base_image.width):

                    color = self.base_image.getpixel((x,y))
                    if color[3] == 0:
                        pbar.update(1)
                        continue

#                    releases = cal.lookup(self.COLOR_THRESHOLD, self.QUERY_LIMIT, color[0], color[1], color[2])
#                    if len(releases) == 0:
#                        continue
#
#                    # Pick a random release
#                    release = releases[randint(0, len(releases)-1)]
#                    used[release["release_mbid"]] += 1
#
#                    data.append({
#                        "x1":
#                        x * self.tile_size,
#                        "y1":
#                        y * self.tile_size,
#                        "x2": (x + 1) * self.tile_size,
#                        "y2": (y + 1) * self.tile_size,
#                        "name":
#                        "%s by %s" % (release["release_name"],
#                                      release["artist_credit_name"]),
#                        "release_mbid":
#                        release["release_mbid"]
#                    })
#
#                    path = cal.cache_path(release["release_mbid"])
                    path= "0016dcfe-2372-44a8-8076-995a657f961d.jpg"
                    cover = Image.open(path)
                    resized = cover.resize((self.tile_size, self.tile_size))

                    composite.paste(resized, (self.tile_size * x, self.tile_size * y))

                    pbar.update(1)

            return composite, data

            with open(output_file + ".json", "w") as f:
                f.write(json.dumps(data))
