# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# The Zabbix frontend's nginx half. Upstream runs nginx and php-fpm together in one container under
# supervisord; here they are two, and the PHP one is zabbix-web-php.
#
# Both carry the frontend: nginx serves the static assets from its copy and php-fpm executes from
# its own, so neither needs a shared volume. About 60 MB duplicated for one less moving part.
FROM dhi.io/alpine-base:3.24-dev@sha256:7182e0bc2f186386bb23bc0718508913450ba1876e93cf07e5e3cf263c4dbb63 AS build
ARG VERSION

# Updated with VERSION by .github/workflows/app-downloads.yaml
ARG ZABBIX_SHA256=0e2c391dc184acce8e34250e7326a51e19c8bcee31e67b8497f5526247ecd261

RUN apk add --no-cache curl

WORKDIR /src
RUN set -eu; \
    curl -fsSL -o zabbix.tar.gz \
        "https://cdn.zabbix.com/zabbix/sources/stable/${VERSION%.*}/zabbix-${VERSION}.tar.gz"; \
    echo "${ZABBIX_SHA256}  zabbix.tar.gz" | sha256sum -c -; \
    tar -xzf zabbix.tar.gz --strip-components=1

# The frontend, and pre-compressed copies of what nginx will serve itself for gzip_static. The
# .php files are not compressed: nginx never sends their contents, it hands them to php-fpm.
RUN set -eu; \
    mkdir -p /rootfs/usr/share/zabbix; \
    cp -a /src/ui/. /rootfs/usr/share/zabbix/; \
    chown -R 0:0 /rootfs/usr/share/zabbix; \
    chmod -R go-w /rootfs/usr/share/zabbix; \
    find /rootfs/usr/share/zabbix \
        \( -name '*.js' -o -name '*.css' -o -name '*.svg' -o -name '*.json' \) \
        -type f ! -name '*.gz' -exec gzip -9 -k {} +


FROM dhi.io/nginx:1-alpine3.24@sha256:7a4e9021737f414ad0f851efb939600690d9d092f51712ce6512bfd0a767ceae

COPY --from=build /rootfs/ /
COPY assets/default.conf /etc/nginx/conf.d/default.conf

# Numeric, so a Kubernetes runAsNonRoot check can verify it without resolving a name. The id the
# Docker Hardened Images nginx already runs as; it only reads the frontend's files.
USER 65532:65532

EXPOSE 8080
