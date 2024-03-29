#!/usr/bin/env python3

import io
import os
import sys
from time import sleep
from uuid import UUID
import concurrent.futures

import psycopg2
from psycopg2.extras import execute_values
import psycopg2.errors
import requests
from wand.image import Image
from tqdm import tqdm

import config

def get_predominant_color_helper(obj, release_mbid):
    return obj.get_predominant_color(release_mbid)


class CoverArtLoader:

    def __init__(self, cache_dir, year):
        self.cache_dir = cache_dir
        self.year = year


    def cache_path(self, release_mbid):
        """ Given a release_mbid, create the file system path to where the cover art should be saved and 
            ensure that the directory for it exists. """

        path = os.path.join(self.cache_dir, release_mbid[0], release_mbid[0:1], release_mbid[0:2])
        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        return os.path.join(path, release_mbid + ".jpg")


    def _download_file(self, url):
        """ Download a file given a URL and return that file as file-like object. """

        sleep_duration = 2
        while True:
            headers = {'User-Agent': 'ListenBrainz Cover Art Compositor ( rob@metabrainz.org )'}
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                total = 0
                obj = io.BytesIO()
                for chunk in r:
                    total += len(chunk)
                    obj.write(chunk)
                obj.seek(0, 0)
                return obj, ""

            if r.status_code in [403, 404]:
                return None, f"Could not load resource: {r.status_code}."

            if r.status_code == 429:
                print("Exceeded rate limit. sleeping %d seconds." % sleep_duration)
                sleep(sleep_duration)
                sleep_duration *= 2
                if sleep_duration > 100:
                    return None, "Timeout loading image, due to 429"

                continue

            if r.status_code == 503:
                print("Service not available. sleeping %d seconds." % sleep_duration)
                sleep(sleep_duration)
                sleep_duration *= 2
                if sleep_duration > 100:
                    return None, "Timeout loading image, 503"
                continue

            return None, "Unhandled status code: %d" % r.status_code

    def _download_cover_art(self, release_mbid, caa_id, cover_art_file):
        """ The cover art for the given release mbid does not exist, so download it,
            save a local copy of it. """

        url = f"https://archive.org/download/mbid-{release_mbid}/mbid-{release_mbid}-{caa_id}_thumb250.jpg"
        image, err = self._download_file(url)
        if image is None:
            return err

        with open(cover_art_file, 'wb') as f:
            f.write(image.read())

        return None

    def fetch(self, release_mbid, caa_id):
        """ Fetch the cover art for the given release_mbid and return a path to where the image
            is located on the local fs. This function will check the local cache for the image and
            if it does not exist, it will be fetched from the archive and chached locally. """

        print("%s %d" % (release_mbid, caa_id), end="")
        sys.stdout.flush()
        cover_art_file = self.cache_path(release_mbid)
        if not os.path.exists(cover_art_file):
            err = self._download_cover_art(release_mbid, caa_id, cover_art_file)
            if err is not None:
                print(" download failed")
                return None, err
            else:
                print(" ok")
        else:
            print(" exists")

        return cover_art_file, ""


    def fetch_all(self):

        releases = []
        query = """WITH releases_year AS (
                   SELECT rl.gid AS release_mbid
                        , rl.release_group AS release_group_id
                        , caa.id AS caa_id
                     FROM release rl
                     JOIN release_country rc
                       ON rc.release = rl.id
                     JOIN cover_art_archive.cover_art caa
                       ON caa.release = rl.id
                     JOIN cover_art_archive.cover_art_type cat
                       ON cat.id = caa.id
                    WHERE type_id = 1
                      AND rc.date_year = %d
               UNION
                   SELECT rl.gid AS release_mbid
                        , rl.release_group AS release_group_id
                        , caa.id AS caa_id
                     FROM release rl
                     JOIN release_unknown_country ruc
                       ON ruc.release = rl.id
                     JOIN cover_art_archive.cover_art caa
                       ON caa.release = rl.id
                     JOIN cover_art_archive.cover_art_type cat
                       ON cat.id = caa.id
                    WHERE type_id = 1
                      AND ruc.date_year = %d
         ), distinct_releases_year AS (
                   SELECT DISTINCT ry.release_mbid
                        , ry.release_group_id
                        , ry.caa_id
                        , row_number() over (partition by ry.release_mbid,
                                                          ry.release_group_id
                                       order by ry.release_mbid,
                                                ry.release_group_id) AS rnum
                     FROM releases_year ry
                 GROUP BY ry.release_mbid
                        , ry.release_group_id
                        , ry.caa_id
          )
                   SELECT release_mbid
                        , caa_id   
                     FROM distinct_releases_year dry
                 GROUP BY dry.release_mbid
                        , dry.release_group_id
                        , dry.caa_id
                        , dry.rnum
                   HAVING dry.rnum = 1""" % (self.year, self.year)

        with psycopg2.connect(config.MBID_MAPPING_DATABASE_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                curs.execute(query)
                for row in curs:
                    releases.append((row["release_mbid"], row["caa_id"]))

        print("%d releases" % len(releases))

        return releases

    def get_predominant_color(self, release_mbid):
        path = self.cache_path(release_mbid)
        if not os.path.exists(path):
            return None

        image = Image(filename=path)
        image.resize(1, 1)
        return (int(255 * image[0][0].red), int(255 * image[0][0].green), int(255 * image[0][0].blue))

    def to_color16(self, color):
        return ((color[0] >> 3) << 11) | ((color[1] >> 2) << 5) | (color[2] >> 3)

    def from_color16(self, color):
        return ((color >> 11 << 3), (((color >> 5) & 63) << 2), ((color & 31) << 3))


    def calculate_colors(self):

        release_colors = {}
        print("fetch release list from db")
        releases = self.fetch_all()
        print("calculate colors")
        calculated = 0
        with tqdm(total=len(releases)) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
                futures = {executor.submit(get_predominant_color_helper, self, release[0]) :
                           release
                           for release in releases}
                for future in concurrent.futures.as_completed(futures):
                    release = futures[future]
                    try:
                        color = future.result()
                        if color is not None:
                            release_colors[release] = color
                            calculated += 1
                    except Exception as exc:
                        print('%s generated an exception: %s' % (release_mbid, exc))
                    pbar.update(1)

        print("Calculated colors for %s releases" % calculated)

        print("save color to db")
        with psycopg2.connect(config.MBID_MAPPING_DATABASE_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                try:
                    curs.execute("DROP TABLE mapping.release_colors_yim_subset")
                    conn.commit()
                except psycopg2.errors.UndefinedTable:
                    conn.rollback()

                curs.execute("""CREATE TABLE mapping.release_colors_yim_subset (
                                            caa_id         BIGINT NOT NULL,
                                            release_mbid   UUID NOT NULL,
                                            red            INTEGER NOT NULL,
                                            green          INTEGER NOT NULL,
                                            blue           INTEGER NOT NULL,
                                            color16        INTEGER NOT NULL,
                                            color          CUBE)""")
                conn.commit();

                values = []
                for release in release_colors:
                    color = release_colors[release]
                    col16 = self.to_color16(color)
                    values.append((release[1], release[0], color[0], color[1], color[2], col16, "(%d,%d,%d)" % (color[0], color[1], color[2])))
                execute_values(curs, """INSERT INTO mapping.release_colors_yim_subset 
                                         (caa_id, release_mbid, red, green, blue, color16, color) VALUES %s""", values)
                conn.commit()

                print("create index")
                curs.execute("""CREATE INDEX release_colors_yim_subset_ndx_color
                                          ON mapping.release_colors_yim_subset(color)""")


    def create_subset_table(self, release_caa_ids):

        release_colors = []
        release_mbids = [ r[0] for r in release_caa_ids ]
        query = """SELECT caa_id 
                        , release_mbid
                        , red
                        , green
                        , blue
                        , color
                     INTO mapping.release_colors_yim_subset
                     FROM release_color
                    WHERE release_mbid in %s"""
        with psycopg2.connect(config.MBID_MAPPING_DATABASE_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                try:
                    curs.execute("DROP TABLE mapping.release_colors_yim_subset")
                except psycopg2.errors.UndefinedTable:
                    conn.rollback()

                curs.execute(query, (tuple(release_mbids),))

    def lookup(self, threshold, limit, red, green, blue):

        releases = []
        query = f""" WITH release_colors AS ( 
                    SELECT release_mbid AS mbid
                         , color <-> '{red}, {green}, {blue}' AS score
                         , color
                      FROM mapping.release_colors_yim_subset
                     WHERE color <-> '{red}, {green}, {blue}'::CUBE < {threshold}
                  ORDER BY color <-> '{red}, {green}, {blue}'
                     LIMIT {limit}
                )    
                    SELECT r.gid AS release_mbid
                         , r.name AS release_name  
                         , ac.name AS artist_credit_name
                         , score
                      FROM release_colors rc
                      JOIN release r
                        ON r.gid = rc.mbid
                      JOIN artist_credit ac
                        ON r.artist_credit = ac.id
                  ORDER BY color <-> '{red}, {green}, {blue}'"""

        with psycopg2.connect(config.MBID_MAPPING_DATABASE_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                curs.execute(query)
                for row in curs:
                    releases.append(dict(row))

        return releases

    def get_color_histogram(self):

        query = """SELECT color16
                        , COUNT(*)
                     FROM mapping.release_colors_yim_subset
                 GROUP BY color16
                 ORDER BY color16"""

        colors = []
        with psycopg2.connect(config.MBID_MAPPING_DATABASE_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                curs.execute(query)
                for row in curs:
                    colors.append(row)
        return colors

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: cache.py <cache_dir> <year>")
        sys.exit(-1)

    cal = CoverArtLoader(sys.argv[1], int(sys.argv[2]))
    for release_mbid, caa_id in cal.fetch_all():
        cal.fetch(release_mbid, caa_id)
#    cal.calculate_colors()
