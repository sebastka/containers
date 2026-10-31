# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# The Zabbix frontend's PHP half: php-fpm and nothing else. Upstream runs this and nginx together
# in one container under supervisord; here they are two, and the nginx one is zabbix-web-nginx.
#
# Docker Hardened Images publish no FPM SAPI -- dhi.io/php ships the CLI only -- so php-fpm and
# its extensions come from Alpine's community repository, added below. The base layers are still
# the hardened ones; the PHP packages are stock Alpine.
FROM dhi.io/alpine-base:3.24-dev@sha256:7182e0bc2f186386bb23bc0718508913450ba1876e93cf07e5e3cf263c4dbb63 AS build
ARG VERSION

# Updated with VERSION by .github/workflows/app-downloads.yaml
ARG ZABBIX_SHA256=0e2c391dc184acce8e34250e7326a51e19c8bcee31e67b8497f5526247ecd261

# Spelled out because these images ship no /etc/alpine-release to read it from, and checked against
# the base's own repository so a base bumped to a new Alpine fails here rather than mixing branches
ARG ALPINE_BRANCH=v3.24

RUN set -eu; \
    base_branch="$(sed -n 's|.*/alpine/\(v[0-9][0-9.]*\)/.*|\1|p' /etc/apk/repositories | head -1)"; \
    [ "${base_branch}" = "${ALPINE_BRANCH}" ] \
        || { echo "ALPINE_BRANCH is ${ALPINE_BRANCH} but the base image is ${base_branch}" >&2; exit 1; }; \
    printf -- 'https://dl-cdn.alpinelinux.org/alpine/%s/community\n' "${ALPINE_BRANCH}" \
        >>/etc/apk/repositories; \
    apk add --no-cache curl \
        php85-fpm \
        php85-bcmath \
        php85-ctype \
        php85-curl \
        php85-fileinfo \
        php85-gd \
        php85-gettext \
        php85-ldap \
        php85-mbstring \
        php85-openssl \
        php85-pgsql \
        php85-session \
        php85-simplexml \
        php85-sockets \
        php85-xmlreader \
        php85-xmlwriter

WORKDIR /src
RUN set -eu; \
    curl -fsSL -o zabbix.tar.gz \
        "https://cdn.zabbix.com/zabbix/sources/stable/${VERSION%.*}/zabbix-${VERSION}.tar.gz"; \
    echo "${ZABBIX_SHA256}  zabbix.tar.gz" | sha256sum -c -; \
    tar -xzf zabbix.tar.gz --strip-components=1

COPY assets/php-fpm.conf /src/php-fpm.conf

# Everything the runtime image gets, under /rootfs: the FPM binary, the extensions and the ini
# files that load them, the frontend, and the libraries the loader reports for each.
COPY --from=dhi.io/alpine-base:3.24@sha256:7b06d747fcb428a0699679955e903b13322c92c79d94ce94c108634f13a714f1 /etc/passwd /etc/group /runtime-etc/
RUN set -eu; \
    install -D -m 755 /usr/sbin/php-fpm85 /rootfs/usr/sbin/php-fpm85; \
    install -d /rootfs/usr/lib/php85/modules /rootfs/etc/php85/conf.d; \
    cp -a /usr/lib/php85/modules/. /rootfs/usr/lib/php85/modules/; \
    cp -a /etc/php85/php.ini /rootfs/etc/php85/php.ini; \
    cp -a /etc/php85/conf.d/. /rootfs/etc/php85/conf.d/; \
    install -D -m 644 /src/php-fpm.conf /rootfs/etc/php85/php-fpm.conf; \
    \
    mkdir -p /rootfs/usr/share/zabbix; \
    cp -a /src/ui/. /rootfs/usr/share/zabbix/; \
    chown -R 0:0 /rootfs/usr/share/zabbix; \
    chmod -R go-w /rootfs/usr/share/zabbix; \
    \
    cp /runtime-etc/passwd /runtime-etc/group /rootfs/etc/; \
    printf '%s\n' 'zabbix:x:1997:1995:Zabbix:/var/lib/zabbix:/sbin/nologin' >>/rootfs/etc/passwd; \
    printf '%s\n' 'zabbix:x:1995:' >>/rootfs/etc/group; \
    \
    loader="$(echo /lib/ld-musl-*.so.1)"; \
    { "${loader}" --list /usr/sbin/php-fpm85; \
      for so in /usr/lib/php85/modules/*.so; do "${loader}" --list "${so}" || true; done; \
    } >/tmp/libs.txt; \
    awk '$2 == "=>" && $3 ~ /^\// && $3 !~ /ld-musl/ { print $3 }' /tmp/libs.txt | sort -u >/tmp/needed.txt; \
    test -s /tmp/needed.txt; \
    while read -r lib; do install -D -m 755 "${lib}" "/rootfs${lib}"; done </tmp/needed.txt


FROM dhi.io/alpine-base:3.24@sha256:7b06d747fcb428a0699679955e903b13322c92c79d94ce94c108634f13a714f1

COPY --from=build /rootfs/ /

# Numeric, so a Kubernetes runAsNonRoot check can verify it without resolving a name
USER 1997:1995
WORKDIR /usr/share/zabbix

EXPOSE 9000
ENTRYPOINT ["/usr/sbin/php-fpm85", "--nodaemonize", "--fpm-config", "/etc/php85/php-fpm.conf"]
