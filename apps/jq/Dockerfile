# syntax=docker/dockerfile:1@sha256:87999aa3d42bdc6bea60565083ee17e86d1f3339802f543c0d03998580f9cb89

FROM docker.io/library/alpine:3.24.1@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b
ARG VERSION
ARG USER=nobody

RUN printf -- 'alias ll="ls -alh"\n' >>/etc/profile && \
    apk add --no-cache jq
USER ${USER}
