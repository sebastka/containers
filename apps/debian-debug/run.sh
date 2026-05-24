#!/bin/sh
set -eux

export VERSION="$(date +'%F')"
export DOCKER_REPO='debian-debug'
export RUN_AS='debian'

docker buildx bake
docker run --rm -it --user=$RUN_AS --entrypoint='' "${DOCKER_REPO}:${VERSION}" /bin/bash -l
