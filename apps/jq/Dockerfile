# syntax=docker/dockerfile:1

FROM alpine:3.23.4
ARG VERSION
ARG USER=nobody

RUN printf -- 'alias ll="ls -alh"\n' >>/etc/profile && \
    apk add --no-cache jq
USER ${USER}
