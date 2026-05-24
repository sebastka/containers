#!/bin/sh
set -eux

export VERSION="$(date +'%Y.%-m.%-d')"
export DOCKER_REPO='element-admin'
export RUN_AS='nobody'

docker buildx bake
docker run --rm -it --user=$RUN_AS --entrypoint='' "${DOCKER_REPO}:${VERSION}" /bin/sh -l
