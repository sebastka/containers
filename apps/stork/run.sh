#!/bin/sh
set -eux

export VERSION='2.4.0'
export DOCKER_REPO='sebastka/stork'
export RUN_AS='stork-server'
# export RUN_AS_TARGET='stork'

docker image build \
    --progress=plain \
    --build-arg VERSION="${VERSION}" \
    --tag "${DOCKER_REPO}:${VERSION}" \
    --tag "${DOCKER_REPO}:latest" \
    .

docker run --rm -it --user=$RUN_AS --entrypoint='' "${DOCKER_REPO}:latest" /bin/sh -l
