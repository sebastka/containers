# syntax=docker/dockerfile:1

ARG VERSION=latest
FROM docker.io/crowdsecurity/crowdsec:${VERSION}
RUN addgroup -g 1000 crowdsec && \
    adduser -u 1000 -G crowdsec -D crowdsec && \
    mkdir /etc/crowdsec
    chown -R crowdsec:crowdsec \
        /var/lib/crowdsec \
        /staging/etc/crowdsec \
        /staging/var/lib/crowdsec \
        /etc/crowdsec

USER 1000:1000
