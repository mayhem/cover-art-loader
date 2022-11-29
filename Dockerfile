ARG PYTHON_BASE_IMAGE_VERSION=3.10-20220315
FROM metabrainz/python:$PYTHON_BASE_IMAGE_VERSION as listenbrainz-base

ARG PYTHON_BASE_IMAGE_VERSION

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                       build-essential \
                       imagemagick \
    && rm -rf /var/lib/apt/lists/*

# PostgreSQL client
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
ENV PG_MAJOR 12
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" $PG_MAJOR > /etc/apt/sources.list.d/pgdg.list
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-$PG_MAJOR \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /cache /code
WORKDIR /code
COPY . /code

RUN pip install -r requirements.txt

CMD /code/cache.py
