#!/usr/bin/env python3

import io
import os

from wand.image import Image
from wand.drawing import Drawing

from cache import CoverArtLoader


class CoverArtMosaic:

    def __init__(self, cache_dir, num_tiles, tile_size):
        self.cache_dir = cache_dir
        self.num_tiles = num_tiles
        self.tile_size = tile_size


    def get_tile_position(self, tile):
        """ Calculate the position of a given tile, return (x, y) """

        return (int(tile % self.num_tiles * self.tile_size), int(tile // self.num_tiles * self.tile_size))


    def create(self):

        composite = Image(height=self.image_size, width=self.image_size, background="#000000")
        for x1, y1, x2, y2 in tiles:
            i += 1
            while True:
                try:
                    mbid = mbids.pop(0)
                except IndexError:
                    cover_art = self.load_or_create_missing_cover_art_tile()

                cover_art, err = self.fetch(mbid)
                if cover_art is None:
                    print(f"Could not fetch cover art for {mbid}: {err}")
                    if self.skip_missing:
                        print("Skip nmissing and try again")
                        continue

                    cover_art = self.load_or_create_missing_cover_art_tile()
                break

            # Check to see if we have a string with a filename or loaded/prepped image (for missing images)
            if isinstance(cover_art, str):
                cover = Image(filename=cover_art)
                cover.resize(x2 - x1, y2 - y1)
            else:
                cover = cover_art

            composite.composite(left=x1, top=y1, image=cover)

        obj = io.BytesIO()
        composite.format = 'jpeg'
        composite.save(file=obj)
        obj.seek(0, 0)

        return obj


if __name__ == '__main__':
    cal = CoverArtLoader("cache")
    release_data = cal.fetch_all()
    release_colors = cal.fetch_release_colors(release_data)
    cal.create_subset_table(release_colors)

    mos = CoverArtMosaic("cache", 5, 25)
