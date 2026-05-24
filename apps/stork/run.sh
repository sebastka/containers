#!/bin/sh
set -eux

export VERSION='2.4.1'
export DOCKER_REPO='stork'
export RUN_AS='stork-server'

docker image build \
    --progress=plain \
    --build-arg VERSION="${VERSION}" \
    --tag "${DOCKER_REPO}:${VERSION}" \
    --tag "${DOCKER_REPO}:latest" \
    .

docker buildx bake
docker run --rm -it --user=$RUN_AS --entrypoint='' "${DOCKER_REPO}:${VERSION}" /bin/sh -l
