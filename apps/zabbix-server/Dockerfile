# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# Zabbix server on Docker Hardened Images: compiled in the -dev variant, run on the runtime one,
# which has no package manager. Only the server is built, where upstream builds the agent, agent2,
# proxy, java gateway and web service from the same tree and splits the outputs afterwards.
#
# The image carries no entrypoint: it ships zabbix_server and the schema, and the chart renders
# zabbix_server.conf and loads the schema. See README.md.
FROM dhi.io/alpine-base:3.24-dev@sha256:7182e0bc2f186386bb23bc0718508913450ba1876e93cf07e5e3cf263c4dbb63 AS build
ARG VERSION

# Updated with VERSION by .github/workflows/app-downloads.yaml
ARG ZABBIX_SHA256=0e2c391dc184acce8e34250e7326a51e19c8bcee31e67b8497f5526247ecd261

RUN apk add --no-cache \
        autoconf \
        automake \
        c-ares-dev \
        curl \
        curl-dev \
        g++ \
        libevent-dev \
        libpq-dev \
        libxml2-dev \
        linux-headers \
        make \
        net-snmp-dev \
        openldap-dev \
        openssl-dev \
        pcre2-dev \
        pkgconf \
        unixodbc-dev \
        zlib-dev

WORKDIR /src
# Upstream's --with- set less three whose -dev packages the hardened apk mirror does not carry:
# libssh (SSH agent items), openipmi (IPMI polling) and libmodbus (Modbus items). SNMP, HTTP agent
# items and webhook media types, ODBC checks, VMware and XML preprocessing are all still in. Only
# --enable-server differs from upstream otherwise, and the hardening flags are theirs.
RUN set -eu; \
    curl -fsSL -o zabbix.tar.gz \
        "https://cdn.zabbix.com/zabbix/sources/stable/${VERSION%.*}/zabbix-${VERSION}.tar.gz"; \
    echo "${ZABBIX_SHA256}  zabbix.tar.gz" | sha256sum -c -; \
    tar -xzf zabbix.tar.gz --strip-components=1; \
    CFLAGS="-O2 -pipe -fPIE -fstack-protector-strong -fstack-clash-protection -D_FORTIFY_SOURCE=3 -Wformat -Werror=format-security" \
    LDFLAGS="-pie -Wl,-z,relro,-z,now -Wl,--as-needed" \
    ./configure \
        --prefix=/usr \
        --sysconfdir=/etc/zabbix \
        --libdir=/usr/lib/zabbix \
        --datadir=/usr/lib \
        --enable-server \
        --enable-ipv6 \
        --with-postgresql \
        --with-ares \
        --with-ldap \
        --with-libcurl \
        --with-libpcre2 \
        --with-libxml2 \
        --with-net-snmp \
        --with-openssl \
        --with-unixodbc \
        --silent; \
    make -j"$(nproc)" -s

# Everything the runtime image gets, under /rootfs. fping is what Zabbix shells out to for its
# icmpping items; the pod needs net.ipv4.ping_group_range to cover the group for it to work
# unprivileged. psql comes along so the schema can be loaded by this image alone: it ships the
# three .sql files, and a deployment that needed a second image for them would need credentials
# for a second registry too. net-snmp's MIBs come too: without them net-snmp resolves no textual
# OID, which is how most of Zabbix's own SNMP templates are written.
RUN apk add --no-cache fping postgresql18-client

RUN set -eu; \
    install -D -m 755 src/zabbix_server/zabbix_server /rootfs/usr/sbin/zabbix_server; \
    install -D -m 755 /usr/sbin/fping /rootfs/usr/sbin/fping; \
    install -D -m 755 /usr/bin/psql /rootfs/usr/bin/psql; \
    install -D -m 644 database/postgresql/schema.sql /rootfs/usr/share/zabbix/schema.sql; \
    install -D -m 644 database/postgresql/images.sql /rootfs/usr/share/zabbix/images.sql; \
    install -D -m 644 database/postgresql/data.sql /rootfs/usr/share/zabbix/data.sql; \
    \
    install -d /rootfs/usr/share/snmp; \
    cp -a /usr/share/snmp/mibs /rootfs/usr/share/snmp/mibs; \
    \
    loader="$(echo /lib/ld-musl-*.so.1)"; \
    for binary in /rootfs/usr/sbin/zabbix_server /rootfs/usr/sbin/fping /rootfs/usr/bin/psql; do \
        "${loader}" --list "${binary}"; \
    done > /tmp/libs.txt; \
    awk '$2 == "=>" && $3 ~ /^\// && $3 !~ /ld-musl/ { print $3 }' /tmp/libs.txt | sort -u > /tmp/needed.txt; \
    test -s /tmp/needed.txt; \
    cat /tmp/needed.txt; \
    while read -r lib; do install -D -m 755 "${lib}" "/rootfs${lib}"; done < /tmp/needed.txt

# The account, written out rather than created: this busybox has no getent, and these are the ids
# upstream uses and the homelab Deployment pins with runAsUser 1997 / runAsGroup 1995
COPY --from=dhi.io/alpine-base:3.24@sha256:7b06d747fcb428a0699679955e903b13322c92c79d94ce94c108634f13a714f1 /etc/passwd /etc/group /runtime-etc/
RUN set -eu; \
    install -d /rootfs/etc; \
    cp /runtime-etc/passwd /runtime-etc/group /rootfs/etc/; \
    printf '%s\n' 'zabbix:x:1997:1995:Zabbix:/var/lib/zabbix:/sbin/nologin' >>/rootfs/etc/passwd; \
    printf '%s\n' 'zabbix:x:1995:' >>/rootfs/etc/group; \
    install -d -o 1997 -g 1995 /rootfs/var/lib/zabbix


FROM dhi.io/alpine-base:3.24@sha256:7b06d747fcb428a0699679955e903b13322c92c79d94ce94c108634f13a714f1

COPY --from=build /rootfs/ /

# Numeric, so a Kubernetes runAsNonRoot check can verify it without resolving a name
USER 1997:1995
WORKDIR /var/lib/zabbix

EXPOSE 10051
ENTRYPOINT ["/usr/sbin/zabbix_server", "--foreground"]
CMD ["-c", "/etc/zabbix/zabbix_server.conf"]
