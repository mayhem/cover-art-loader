#!/usr/bin/env python3

import io
import sys
from PIL import Image, ImageDraw
import requests

from compose import CoverArtMosaic
from base import create_rectangular_base_image, create_circular_base_image


def fetch_cover_art(release_mbid):

    r = requests.get(f"http://coverartarchive.org/release/{release_mbid}/front")
    if r.status_code != 200:
        print("Cannot fetch cover art: '%s'" % r.text)
        return None

    return Image.open(io.BytesIO(r.content))


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: create-cover-art-mosaic.py <release mbid> <base image size> <tile size> <output image png> <year>")
        sys.exit(-1)

    release_mbid = sys.argv[1]
    base_image_size = int(sys.argv[2])
    tile_size = int(sys.argv[3])
    output_file = sys.argv[4]
    year = sys.argv[5]
    cache_dir = "cache-%s" % year

    base_image = fetch_cover_art(release_mbid)
    if base_image is None:
        print("Failed to load base cover art")
        sys.exit(-1)

    base_image = base_image.resize((base_image_size, base_image_size))
    base_image = base_image.convert("RGBA")

    mos = CoverArtMosaic(cache_dir, base_image, tile_size, year)
    mosaic, _ = mos.create(dry_run=True)
    mosaic.save(output_file)

    sys.exit(-1)
