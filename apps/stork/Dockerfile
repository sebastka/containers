# syntax=docker/dockerfile:1@sha256:572cebbc2b15e6f84c077742952674889cb63cd5e9b80abdffcbe587b6f19183

# Stork on Docker Hardened Images: installed in the -dev variant (apk, shell), run on the runtime
# variant, which has no package manager. Both Stork binaries and the LDAP hook link musl and
# nothing else, so the runtime image gets files only, with no library closure to carry.
FROM dhi.io/alpine-base:3.24-dev@sha256:ab3130d401f94092d65c15d38566fbffdba1b4fe0f766968003535cdddf6d2e0 AS build
ARG VERSION

# ISC publishes Stork to its own Cloudsmith repository; DHI's apk mirror does not carry it. These
# images ship no /etc/alpine-release to read the branch from, unlike docker.io/library/alpine, so
# it is named here and checked against the base below. It stays an argument rather than being
# derived outright: when a new Alpine lands before ISC has published for it, pinning the older
# branch on purpose is the way out, and the check then states the mismatch instead of hiding it.
ARG ALPINE_BRANCH=v3.24

RUN set -eu; \
    base_branch="$(sed -n 's|.*/alpine/\(v[0-9][0-9.]*\)/.*|\1|p' /etc/apk/repositories | head -1)"; \
    [ -n "${base_branch}" ] \
        || { echo "cannot read the Alpine branch from /etc/apk/repositories" >&2; exit 1; }; \
    [ "${base_branch}" = "${ALPINE_BRANCH}" ] \
        || { echo "ALPINE_BRANCH is ${ALPINE_BRANCH} but the base image is ${base_branch}: move the two together, or pin ALPINE_BRANCH on purpose if ISC has not published for ${base_branch} yet" >&2; exit 1; }; \
    wget -qO /etc/apk/keys/stork@isc-6914F776A579B428.rsa.pub \
        https://dl.cloudsmith.io/public/isc/stork/rsa.6914F776A579B428.key; \
    printf -- 'https://dl.cloudsmith.io/public/isc/stork/alpine/%s/main\n' "${ALPINE_BRANCH}" \
        >>/etc/apk/repositories; \
    apk add --no-cache \
        tzdata \
        isc-stork-server=~"${VERSION}" \
        isc-stork-server-hook-ldap=~"${VERSION}"

# The runtime image's own accounts, to append to rather than replace
COPY --from=dhi.io/alpine-base:3.24@sha256:7d9384f025a398c7a60c4a978bf419f3b4bd86bde0577d352d902224d4dc7d87 /etc/passwd /etc/group /runtime-etc/

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


FROM dhi.io/alpine-base:3.24@sha256:7d9384f025a398c7a60c4a978bf419f3b4bd86bde0577d352d902224d4dc7d87

COPY --from=build /rootfs/ /

# Numeric, so a Kubernetes runAsNonRoot check can verify it without resolving a name
USER 100:101
WORKDIR /var/lib/stork-server
ENV TZ=Europe/Oslo

EXPOSE 8080
ENTRYPOINT []
CMD ["stork-server"]
