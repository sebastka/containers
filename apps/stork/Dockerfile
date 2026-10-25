# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# Stork on Docker Hardened Images: installed in the -dev variant (apk, shell), run on the runtime
# variant, which has no package manager. Both Stork binaries and the LDAP hook link musl and
# nothing else, so the runtime image gets files only, with no library closure to carry.
FROM dhi.io/alpine-base:3.24-dev@sha256:7182e0bc2f186386bb23bc0718508913450ba1876e93cf07e5e3cf263c4dbb63 AS build
ARG VERSION

# ISC publishes Stork to its own Cloudsmith repository; DHI's apk mirror does not carry it. The
# branch is spelled out because these images ship no /etc/alpine-release to read it from, unlike
# docker.io/library/alpine: keep it in step with the base image tag above.
ARG ALPINE_BRANCH=v3.24

RUN set -eu; \
    wget -qO /etc/apk/keys/stork@isc-6914F776A579B428.rsa.pub \
        https://dl.cloudsmith.io/public/isc/stork/rsa.6914F776A579B428.key; \
    printf -- 'https://dl.cloudsmith.io/public/isc/stork/alpine/%s/main\n' "${ALPINE_BRANCH}" \
        >>/etc/apk/repositories; \
    apk add --no-cache \
        tzdata \
        isc-stork-server=~"${VERSION}" \
        isc-stork-server-hook-ldap=~"${VERSION}"

# The runtime image's own accounts, to append to rather than replace
COPY --from=dhi.io/alpine-base:3.24@sha256:7b06d747fcb428a0699679955e903b13322c92c79d94ce94c108634f13a714f1 /etc/passwd /etc/group /runtime-etc/

# Everything the runtime image gets, staged under /rootfs. The package's pre-install script cannot
# create the account here, since DHI's busybox has no getent, so it is written out instead -- with
# the ids this image has always used: the homelab Deployment pins runAsUser 100 and runAsGroup 101,
# and the volume's files are owned by them.
RUN set -eu; \
    mkdir -p /rootfs/usr/bin /rootfs/usr/lib /rootfs/usr/share /rootfs/etc; \
    cp -a /usr/bin/stork-server /usr/bin/stork-tool /rootfs/usr/bin/; \
    cp -a /usr/lib/stork-server /rootfs/usr/lib/; \
    cp -a /usr/share/stork /rootfs/usr/share/; \
    cp -a /usr/share/zoneinfo /rootfs/usr/share/; \
    cp -a /etc/stork /rootfs/etc/; \
    cp /runtime-etc/passwd /runtime-etc/group /rootfs/etc/; \
    printf '%s\n' 'stork-server:x:100:101:Stork Server User:/var/lib/stork-server:/sbin/nologin' \
        >>/rootfs/etc/passwd; \
    printf '%s\n' 'stork-server:x:101:' >>/rootfs/etc/group; \
    install -d -o 100 -g 101 /rootfs/var/lib/stork-server


FROM dhi.io/alpine-base:3.24@sha256:7b06d747fcb428a0699679955e903b13322c92c79d94ce94c108634f13a714f1

COPY --from=build /rootfs/ /

# Numeric, so a Kubernetes runAsNonRoot check can verify it without resolving a name
USER 100:101
WORKDIR /var/lib/stork-server
ENV TZ=Europe/Oslo

EXPOSE 8080
ENTRYPOINT []
CMD ["stork-server"]
