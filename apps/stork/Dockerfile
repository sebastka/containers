# syntax=docker/dockerfile:1@sha256:ecfaec9ed6d810b56388c508f4121597bfbba70d41a6dfeee4d8cad5f295fc32

FROM docker.io/library/alpine:3.24.2@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6
ARG VERSION

USER root
RUN apk add --no-cache curl \ 
    && curl -sL https://dl.cloudsmith.io/public/isc/stork/rsa.6914F776A579B428.key >/etc/apk/keys/stork@isc-6914F776A579B428.rsa.pub \
    && printf -- 'https://dl.cloudsmith.io/public/isc/stork/alpine/v%s/main\n' "$(cut -d. -f1,2 /etc/alpine-release)" >>/etc/apk/repositories \
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
