#!/bin/sh
set -eux

export VERSION="$(date +'%F')"
export DOCKER_REPO='sebastka/vert-builder'
export RUN_AS='nobody'
# export RUN_AS_TARGET='nobody'

docker image build \
    --progress=plain \
    --build-arg VERSION="${VERSION}" \
    --build-arg PUB_ENV=production \
    --build-arg PUB_HOSTNAME=vert.karlsen.app \
    --build-arg PUB_PLAUSIBLE_URL="" \
    --build-arg PUB_VERTD_URL="https://vertd.karlsen.app" \
    --build-arg PUB_DISABLE_ALL_EXTERNAL_REQUESTS="true" \
    --build-arg PUB_DONATION_URL="https://donations.vert.sh" \
    --build-arg PUB_STRIPE_KEY="pk_live_51RDVmAGSxPVad6bQwzVNnbc28nlmzA30krLWk1fefCMpUPiSRPkavMMbGqa8A3lUaOCMlsUEVy2CWDYg0ip3aPpL00ZJlsMkf2" \
    --build-arg PUB_DISABLE_FAILURE_BLOCKS="false" \
    --tag "${DOCKER_REPO}:${VERSION}" \
    --tag "${DOCKER_REPO}:latest" \
    .

docker run --rm -it --user=$RUN_AS --entrypoint='' "${DOCKER_REPO}:latest" /bin/sh -l
