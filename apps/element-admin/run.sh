#!/bin/sh
set -eux

export RUN_AS='nobody'
export VERSION="$(date +'%Y.%-m.%-d')"

docker buildx bake
docker run --rm -it --user=$RUN_AS --entrypoint='' "element-admin:${VERSION}" /bin/sh -l
