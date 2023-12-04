#!/usr/bin/env python3

from collections import defaultdict
import io
import os
import sys
import json

from wand.image import Image

from cache import CoverArtLoader


class CoverArtMosaic:

    COLOR_THRESHOLD = 100
    QUERY_LIMIT = 20

    def __init__(self, cache_dir, pattern_file, tile_size):
        self.cache_dir = cache_dir
        self.tile_size = tile_size
        self.pattern_file = pattern_file

        self.pattern_image = Image(filename=pattern_file)
        self.image_size_x = tile_size * self.pattern_image.width 
        self.image_size_y = tile_size * self.pattern_image.height 


    def create(self, output_file):

        used = defaultdict(int)

        cal = CoverArtLoader("cache")
        composite = Image(height=self.image_size_y, width=self.image_size_x, background="#000000")
        data = []
        for y in range(self.pattern_image.height):
            for x in range(self.pattern_image.width):
                color = self.pattern_image[y][x]
                color = (int(255 * color.red), int(255 * color.green), int(255 * color.blue))

                lowest_use_count = None
                lowest_use_index = None
                releases = cal.lookup(self.COLOR_THRESHOLD, self.QUERY_LIMIT, color[0], color[1], color[2])
                if len(releases) == 0:
                    continue

                for i, release in enumerate(releases):
                    release_mbid = release["release_mbid"]
                    if i == 0:
                        lowest_use_count = used[release_mbid]
                        lowest_use_index = i
                    if used[release_mbid] < lowest_use_count:
                        lowest_use_count = used[release_mbid]
                        lowest_use_index = i

                if lowest_use_index is None:
                    continue

                release = releases[lowest_use_index]
                used[release["release_mbid"]] += 1

                print("(%3d %3d) (%3d %3d %3d)-(%3d %3d %3d) %s %d %d" % (x, y, color[0], color[1], color[2],
                                                                          release["red"], release["green"], release["blue"],
                                                                          release["release_mbid"],
                                                                          used[release["release_mbid"]],
                                                                          releases[lowest_use_index]["score"]))
                data.append({"x1": x * self.tile_size,
                             "y1": y * self.tile_size,
                             "x2": (x+1) * self.tile_size,
                             "y2": (y+1) * self.tile_size,
                             "name": "%s by %s" % (release["release_name"], release["artist_credit_name"]),
                             "release_mbid": release["release_mbid"]})

                path = cal.cache_path(release["release_mbid"])

                cover = Image(filename=path)
                cover.resize(self.tile_size, self.tile_size)

                composite.composite(left=self.tile_size * x, top=self.tile_size * y, image=cover)

        max_dupes = 0
        for mbid in used:
            max_dupes = max(max_dupes, used[mbid])
        print("max re-use count: %d" % max_dupes)

        composite.save(filename=output_file)

        with open(output_file + ".json", "w") as f:
            f.write(json.dumps(data))


if __name__ == '__main__':
    cal = CoverArtLoader("cache")
#    release_data = cal.fetch_all()
#    cal.create_subset_table(release_data)

    if len(sys.argv) < 3:
        print("Usage: compose.py <tile size> <base image PNG> <output image JPG>")
        sys.exit(-1)

    mos = CoverArtMosaic("cache", sys.argv[2], int(sys.argv[1]))
    mos.create(sys.argv[3])
    sys.exit(0)
