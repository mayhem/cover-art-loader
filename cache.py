#!/usr/bin/env python3

import io
import os
import sys
from time import sleep
from uuid import UUID

import psycopg2
import psycopg2.extras
import psycopg2.errors
from psycopg2.extras import execute_values
import requests

import config


class CoverArtLoader:

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir


    def _cache_path(self, release_mbid):
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
                log("Exceeded rate limit. sleeping %d seconds." % sleep_duration)
                sleep(sleep_duration)
                sleep_duration *= 2
                if sleep_duration > 100:
                    return None, "Timeout loading image, due to 429"

                continue

            if r.status_code == 503:
                log("Service not available. sleeping %d seconds." % sleep_duration)
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
        cover_art_file = self._cache_path(release_mbid)
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
                      AND rc.date_year = 2022
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
                      AND ruc.date_year = 2022
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
                   HAVING dry.rnum = 1"""

        with psycopg2.connect(config.MBID_MAPPING_DATABASE_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                curs.execute(query)
                for row in curs:
                    releases.append((row["release_mbid"], row["caa_id"]))

        print("%d releases" % len(releases))

        return releases

    def fetch_release_colors(self, release_caa_ids):

        release_colors = []
        release_mbids = [ r[0] for r in release_caa_ids ]
        query = """SELECT caa_id 
                        , release_mbid
                        , red
                        , green
                        , blue
                        , color
                     FROM release_color
                    WHERE release_mbid in %s"""
        with psycopg2.connect(config.MBID_MAPPING_DATABASE_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                curs.execute(query, (tuple(release_mbids),))
                for row in curs:
                    release_colors.append((row["caa_id"],
                                           row["release_mbid"],
                                           row["red"],
                                           row["green"],
                                           row["blue"],
                                           row["color"]))

        return release_colors


    def create_subset_table(self, release_colors):

        query = """INSERT INTO mapping.release_colors_yim_subset (caa_id,
                                                                  release_mbid,
                                                                  red,
                                                                  green,
                                                                  blue,
                                                                  color) VALUES (%s)"""
        print(release_colors[0])
        with psycopg2.connect(config.MBID_MAPPING_DATABASE_URI) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
                try:
                    curs.execute("TRUNCATE mapping.release_colors_yim_subset")
                except psycopg2.errors.UndefinedTable:
                    conn.rollback()
                    curs.execute("""CREATE TABLE mapping.release_colors_yim_subset (
                                        caa_id                  BIGINT NOT NULL,
                                        release_mbid            TEXT NOT NULL,
                                        red                     SMALLINT NOT NULL,
                                        green                   SMALLINT NOT NULL,   
                                        blue                    SMALLINT NOT NULL,
                                        color                   CUBE
                                    )""")
                    conn.commit()

                execute_values(curs, query, release_colors)
                conn.commit()


if __name__ == '__main__':
    cal = CoverArtLoader("cache")
    for release_mbid, caa_id in cal.fetch_all():
        cal.fetch(release_mbid, caa_id)
