#!/usr/bin/env python3

import io
import os

from wand.image import Image
from wand.drawing import Drawing

from cache import CoverArtLoader


class CoverArtMosaic:

    def __init__(self, cache_dir, pattern_file, tile_size):
        self.cache_dir = cache_dir
        self.tile_size = tile_size
        self.pattern_file = pattern_file

        self.pattern_image = Image(filename=pattern_file)
        self.image_size_x = tile_size * self.pattern_image.width 
        self.image_size_y = tile_size * self.pattern_image.height 
        print("pattern image: %d x %d" % (self.pattern_image.width, self.pattern_image.height))


    def create(self, output_file):

        used = {}

        cal = CoverArtLoader("cache")
        composite = Image(height=self.image_size_y, width=self.image_size_x, background="#000000")
        index = 0
        for y in range(self.pattern_image.height):
            for x in range(self.pattern_image.width):
                color = self.pattern_image[y][x]

                picked = None
                releases = cal.lookup(int(255 * color.red), int(255 * color.green), int(255 * color.blue))
                for release in releases:
                    if release["release_mbid"] in used:
                        continue
                    picked = release

                if picked is None:
                    picked = releases[0]
                    print("Ran out of options!")

                used[picked["release_mbid"]] = 1

                print(f"{x} {y} ({color.red}, {color.green}, {color.blue}) {picked['release_mbid']}")
                path = cal._cache_path(picked["release_mbid"])

                cover = Image(filename=path)
                cover.resize(self.tile_size, self.tile_size)

                composite.composite(left=self.tile_size * x, top=self.tile_size * y, image=cover)

                index += 1

        composite.save(filename=output_file)



if __name__ == '__main__':
#    TODO: actually analyze these images!
    cal = CoverArtLoader("cache")
#    release_data = cal.fetch_all()
#    cal.create_subset_table(release_data)

    mos = CoverArtMosaic("cache", "rainbow.png", 100)
    mos.create("test.jpg")
