# syntax=docker/dockerfile:1

FROM docker.io/library/alpine:3.23
ARG VERSION

USER root
RUN apk add --no-cache curl \ 
    && curl -sL https://dl.cloudsmith.io/public/isc/stork/rsa.6914F776A579B428.key >/etc/apk/keys/stork@isc-6914F776A579B428.rsa.pub \
    && printf -- 'https://dl.cloudsmith.io/public/isc/stork/alpine/v3.23/main\n' >>/etc/apk/repositories \
    && apk add --no-cache \
        tzdata \
        isc-stork-server=~"${VERSION}" \
        isc-stork-server-hook-ldap \
    && mkdir -p /var/lib/stork-server \
    && chown -R stork-server:stork-server /var/lib/stork-server

USER stork-server:stork-server
WORKDIR /var/lib/stork-server
ENV TZ=Europe/Oslo

EXPOSE 8080
ENTRYPOINT []
CMD ["stork-server"]
