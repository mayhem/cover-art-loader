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

    def __init__(self, cache_dir, pattern_file, tile_size, year):
        self.cache_dir = cache_dir
        self.tile_size = tile_size
        self.pattern_file = pattern_file
        self.year = year

        self.pattern_image = Image.open(pattern_file)
        self.image_size_x = tile_size * self.pattern_image.width
        self.image_size_y = tile_size * self.pattern_image.height

    def create(self, output_file):

        used = defaultdict(int)

        print("Create image size %d * %d with tile size %d." %
              (self.image_size_x, self.image_size_y, self.tile_size))
        cal = CoverArtLoader("cache-2023", self.year)
        composite = Image.new(mode="RGBA", size=(self.image_size_x, self.image_size_y), color=(0,0,0,0))
        data = []

        with tqdm(total=self.pattern_image.height * self.pattern_image.width) as pbar:
            for y in range(self.pattern_image.height):
                for x in range(self.pattern_image.width):

                    color = self.pattern_image.getpixel((x,y))
                    if color[3] == 0:
                        pbar.update(1)
                        continue

                    releases = cal.lookup(self.COLOR_THRESHOLD, self.QUERY_LIMIT, color[0], color[1], color[2])
                    if len(releases) == 0:
                        continue

                    # Pick a random release
                    release = releases[randint(0, len(releases)-1)]
                    used[release["release_mbid"]] += 1

                    data.append({
                        "x1":
                        x * self.tile_size,
                        "y1":
                        y * self.tile_size,
                        "x2": (x + 1) * self.tile_size,
                        "y2": (y + 1) * self.tile_size,
                        "name":
                        "%s by %s" % (release["release_name"],
                                      release["artist_credit_name"]),
                        "release_mbid":
                        release["release_mbid"]
                    })

                    path = cal.cache_path(release["release_mbid"])

                    cover = Image.open(path)
                    resized = cover.resize((self.tile_size, self.tile_size))

                    composite.paste(resized, (self.tile_size * x, self.tile_size * y))

                    pbar.update(1)

            composite.save(output_file, "PNG")

            with open(output_file + ".json", "w") as f:
                f.write(json.dumps(data))


if __name__ == '__main__':
    #    cal = CoverArtLoader("cache")
    #    release_data = cal.fetch_all()
    #    cal.create_subset_table(release_data)

    if len(sys.argv) < 4:
        print(
            "Usage: compose.py <tile size> <base image PNG> <output image JPG> <year>"
        )
        sys.exit(-1)

    mos = CoverArtMosaic("cache", sys.argv[2], int(sys.argv[1]),
                         int(sys.argv[4]))
    mos.create(sys.argv[3])
    sys.exit(0)
