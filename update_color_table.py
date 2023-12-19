#!/usr/bin/env python3
import sys
from cache import CoverArtLoader

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: cache.py <cache_dir> <year>")
        sys.exit(-1)

    cal = CoverArtLoader(sys.argv[1], int(sys.argv[2]))
    cal.calculate_colors()
