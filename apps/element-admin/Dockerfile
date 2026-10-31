# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# Element Admin on Docker Hardened Images, built where upstream builds on docker.io/library/node
# and served where they serve on ghcr.io/nginx/nginx-unprivileged. The source is the named build
# context "src" in docker-bake.hcl, a git checkout of the commit Renovate pins there, so this
# Dockerfile replaces upstream's while still building exactly their tree.
#
# Unlike upstream's image this one has no start-up scripts: it serves the built assets and a
# placeholder server block, and the deployment supplies the real one. See README.md.
FROM dhi.io/node:26-alpine3.24-dev@sha256:4f971dcdc1fdf59f9d3e84dbd529690c2d15f75ae898fb310acad9c12d7bbdf9 AS build
ARG VERSION

ENV PNPM_HOME="/pnpm" \
    PATH="/pnpm:${PATH}"

WORKDIR /app
# src is a named build context from docker-bake.hcl, not a stage, which hadolint cannot see
# hadolint ignore=DL3022
COPY --from=src . .

# corepack ships with this image, so pnpm comes from the version the repo asks for in its
# packageManager field rather than whatever is newest
RUN corepack enable \
    && pnpm install --frozen-lockfile \
    && pnpm run build

# Pre-compressed copies for nginx's gzip_static. find, not the `dist/**/*` upstream writes: that
# glob needs bash and only reaches one level deep under /bin/sh, leaving nested assets
# uncompressed. The symlink is upstream's: a server block can point index at index.runtime.html
# and have a deployment write the configured page to /tmp, on a read-only root filesystem.
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


FROM dhi.io/nginx:1-alpine3.24@sha256:7a4e9021737f414ad0f851efb939600690d9d092f51712ce6512bfd0a767ceae

COPY --from=build /app/dist /dist
COPY --from=build /rootfs/ /
COPY assets/default.conf /etc/nginx/conf.d/default.conf

# Numeric, so a Kubernetes runAsNonRoot check can verify it without resolving a name. The same id
# the Docker Hardened Images nginx already runs as, whose entrypoint starts nginx for us.
USER 65532:65532

EXPOSE 8080
