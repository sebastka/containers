#!/bin/sh
set -eux

export VERSION="$(date +'%F')"
export DOCKER_REPO='sebastka/jq'
export RUN_AS='nobody'

docker image build \
    --progress=plain \
    --build-arg VERSION="${VERSION}" \
    --tag "${DOCKER_REPO}:${VERSION}" \
    --tag "${DOCKER_REPO}:latest" \
    .

docker run --rm -it --user=$RUN_AS --entrypoint='' "${DOCKER_REPO}:latest" /bin/sh -l
