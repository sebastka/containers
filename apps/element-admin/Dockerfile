# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# Element Admin on Docker Hardened Images, built where upstream builds on docker.io/library/node
# and served where they serve on ghcr.io/nginx/nginx-unprivileged. The source is the named build
# context "src" in docker-bake.hcl, a git checkout of the commit Renovate pins there, so this
# Dockerfile replaces upstream's while still building exactly their tree.
#
# Unlike upstream's image this one has no start-up scripts: it serves the built assets and a
# placeholder server block, and the deployment supplies the real one. See README.md.
# The favicon, which upstream does not have: it draws its logo inline in a React component and
# ships no icon file anywhere, so the built dist/ has nothing to answer a browser's automatic
# request for /favicon.ico. scripts/extract-logo.py lifts the square mark out of that component --
# and stops the build rather than guess if it can no longer find it -- and this stage rasterises
# it. The rasteriser and the ICO tool are not in the hardened apk mirror, so they come from
# upstream Alpine's community repository; nothing from this stage but the .ico reaches the image.
FROM dhi.io/python:3.15.2-alpine3.24-dev@sha256:637851b6e6d508e16b6e979c47db73d294f4019c38a7eb2493236ddffb4fa67e AS favicon
ARG ALPINE_BRANCH=v3.24

RUN set -eu; \
    base_branch="$(sed -n 's|.*/alpine/\(v[0-9][0-9.]*\)/.*|\1|p' /etc/apk/repositories | head -1)"; \
    [ -n "${base_branch}" ] || { echo "cannot read the Alpine branch from /etc/apk/repositories" >&2; exit 1; }; \
    [ "${base_branch}" = "${ALPINE_BRANCH}" ] \
        || { echo "ALPINE_BRANCH is ${ALPINE_BRANCH} but the base image is on ${base_branch}" >&2; exit 1; }; \
    printf -- 'https://dl-cdn.alpinelinux.org/alpine/%s/community\n' "${ALPINE_BRANCH}" \
        >>/etc/apk/repositories; \
    apk add --no-cache icoutils rsvg-convert

COPY scripts/extract-logo.py /extract-logo.py
# src is a named build context from docker-bake.hcl, not a stage, which hadolint cannot see
# hadolint ignore=DL3022
COPY --from=src src/components/logo.tsx /logo.tsx

# Recoloured on the way out: Element's own mark is a green disc, and a tab of this next to a tab
# of Element itself would be the same icon twice. The disc takes Element's dark background and the
# arcs take the green, which reads as the same mark at 16 px without being mistaken for it.
ARG FAVICON_DISC="#1B1D22"
ARG FAVICON_ARCS="#0DBD8B"

# 16, 32 and 48 px: what a browser picks between for a tab, a bookmark and a desktop shortcut
RUN set -eu; \
    python3 /extract-logo.py /logo.tsx /favicon.svg --disc "${FAVICON_DISC}" --arcs "${FAVICON_ARCS}"; \
    for size in 16 32 48; do \
        rsvg-convert --width "${size}" --height "${size}" --output "/favicon-${size}.png" /favicon.svg; \
    done; \
    icotool --create --output /favicon.ico /favicon-16.png /favicon-32.png /favicon-48.png; \
    icotool --list /favicon.ico


FROM dhi.io/node:26-alpine3.24-dev@sha256:b1968ad63fbbcbbea96cf552a1ccd13f60034d42606e06122513f4fd3f971737 AS build
ARG VERSION

ENV PNPM_HOME="/pnpm" \
    PATH="/pnpm:${PATH}"

WORKDIR /app
# src is a named build context from docker-bake.hcl, not a stage, which hadolint cannot see
# hadolint ignore=DL3022
COPY --from=src . .

# corepack ships with this image, so pnpm comes from the version the repo asks for in its
# packageManager field rather than whatever is newest.
#
# --no-runtime: upstream's devEngines.runtime asks pnpm to download its own Node when the one in
# use does not satisfy the range, and pnpm fetches it whether or not it is needed. What it fetches
# is nodejs.org's glibc build, which cannot run here -- this image is musl, so the binary dies on
# its missing ELF interpreter and vite exits 127 with "node: not found" (#288). The flag leaves it
# unfetched and unlinked, and the build runs on this image's own Node, which is the version the
# range asked for anyway.
RUN corepack enable \
    && pnpm install --frozen-lockfile --no-runtime \
    && pnpm run build

# Pre-compressed copies for nginx's gzip_static. find, not the `dist/**/*` upstream writes: that
# glob needs bash and only reaches one level deep under /bin/sh, leaving nested assets
# uncompressed. The symlink is upstream's: a server block can point index at index.runtime.html
# and have a deployment write the configured page to /tmp, on a read-only root filesystem.
COPY --from=favicon /favicon.ico dist/favicon.ico

RUN find dist -type f ! -name '*.gz' -exec gzip -9 -k {} + \
    && ln -s /tmp/index.runtime.html dist/

# The two nginx snippets worth keeping, for a deployment's server block to include. Not upstream's
# default.conf: it includes a listen file their start-up script generated, which this image has no
# script to write. nginx refuses a duplicate server_tokens and the hardened nginx.conf already sets
# it, so upstream's line is dropped -- after checking it still says exactly what the base says, so
# a change on either side stops the build instead of silently losing a directive.
RUN set -eu; \
    mkdir -p /rootfs/etc/nginx/conf.d; \
    grep -qx 'server_tokens off;' docker/http_customisations.conf \
        || { echo "docker/http_customisations.conf no longer sets 'server_tokens off;': compare it with the base image's nginx.conf before dropping anything" >&2; exit 1; }; \
    grep -vx 'server_tokens off;' docker/http_customisations.conf \
        >/rootfs/etc/nginx/conf.d/http_customisations.conf; \
    cp docker/security_headers.conf /rootfs/etc/nginx/security_headers.conf


FROM dhi.io/nginx:1-alpine3.24@sha256:34c5f1f63c57c0fb1b52505aecbb213520e15918dc822eb16371edff5183cbd1

COPY --from=build /app/dist /dist
COPY --from=build /rootfs/ /
COPY assets/default.conf /etc/nginx/conf.d/default.conf

# Numeric, so a Kubernetes runAsNonRoot check can verify it without resolving a name. The same id
# the Docker Hardened Images nginx already runs as, whose entrypoint starts nginx for us.
USER 65532:65532

EXPOSE 8080
