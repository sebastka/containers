# syntax=docker/dockerfile:1@sha256:87999aa3d42bdc6bea60565083ee17e86d1f3339802f543c0d03998580f9cb89

FROM docker.io/library/alpine:3.23.4@sha256:5b10f432ef3da1b8d4c7eb6c487f2f5a8f096bc91145e68878dd4a5019afde11
ARG VERSION
ARG USER=nobody

RUN printf -- 'alias ll="ls -alh"\n' >>/etc/profile && \
    apk add --no-cache jq
USER ${USER}
