# syntax=docker/dockerfile:1@sha256:ecfaec9ed6d810b56388c508f4121597bfbba70d41a6dfeee4d8cad5f295fc32

FROM docker.io/library/alpine:3.24.2@sha256:3cf95fe0816180395592b8373f3ec60663f076127617bbacb4eacf9667afe2e9
ARG VERSION
ARG USER=nobody

RUN printf -- 'alias ll="ls -alh"\n' >>/etc/profile && \
    apk add --no-cache jq
USER ${USER}
