#!/bin/sh
set -eux

export RUN_AS='nobody'
export VERSION="$(grep -m1 'default = "v' docker-bake.hcl | sed 's/.*"\(.*\)".*/\1/')"

docker buildx bake
docker run --rm -it --user=$RUN_AS --entrypoint='' "element-admin:${VERSION}" /bin/sh -l
