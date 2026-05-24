#!/bin/sh
set -eux

export VERSION="$(date +'%F')"
export DOCKER_REPO='jq'
export RUN_AS='nobody'

docker buildx bake
docker run --rm -it --user=$RUN_AS --entrypoint='' "${DOCKER_REPO}:${VERSION}" /bin/sh -l
