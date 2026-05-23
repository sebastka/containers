#!/bin/sh
set -eux

export VERSION="v1.7.8"

docker buildx bake
docker run --rm -it --entrypoint='' "crowdsec:${VERSION}" /bin/sh -l
