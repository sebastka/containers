# syntax=docker/dockerfile:1

FROM dunglas/frankenphp:1.12.2-php8.5.5-alpine
ARG VERSION

ARG USER=www-data
RUN setcap -r /usr/local/bin/frankenphp \
    && chown -R ${USER}:${USER} /config/caddy /data/caddy
USER ${USER}
