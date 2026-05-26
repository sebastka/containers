# syntax=docker/dockerfile:1@sha256:87999aa3d42bdc6bea60565083ee17e86d1f3339802f543c0d03998580f9cb89

FROM docker.io/library/alpine:3.23.4@sha256:5b10f432ef3da1b8d4c7eb6c487f2f5a8f096bc91145e68878dd4a5019afde11
ARG VERSION

USER root
RUN apk add --no-cache curl \ 
    && curl -sL https://dl.cloudsmith.io/public/isc/stork/rsa.6914F776A579B428.key >/etc/apk/keys/stork@isc-6914F776A579B428.rsa.pub \
    && printf -- 'https://dl.cloudsmith.io/public/isc/stork/alpine/v3.23/main\n' >>/etc/apk/repositories \
    && apk add --no-cache \
        tzdata \
        isc-stork-server=~"${VERSION}" \
        isc-stork-server-hook-ldap=~"${VERSION}" \
    && mkdir -p /var/lib/stork-server \
    && chown -R stork-server:stork-server /var/lib/stork-server

USER stork-server:stork-server
WORKDIR /var/lib/stork-server
ENV TZ=Europe/Oslo

EXPOSE 8080
ENTRYPOINT []
CMD ["stork-server"]
