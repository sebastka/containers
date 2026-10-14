# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# Deluge on Docker Hardened Images: built in the -dev variant (shell, apk, compilers), run on the
# runtime variant (no shell, no package manager, non-root). Python 3.13: libtorrent's musl wheels
# stop there. See README.md.

FROM dhi.io/python:3.13.16-alpine3.24-dev@sha256:6496a70947b87a9ea1a9bf9b6a7f50e9df1872a8e16ee4fbecf6bb3722553dc2 AS build
ARG VERSION
ARG TARGETARCH

# 7-Zip's own static Linux build, as 7zr for the Extractor plugin (.7z)
# renovate: datasource=github-releases depName=ip7z/7zip versioning=loose
ARG SEVENZIP_VERSION=26.04
ARG SEVENZIP_SHA256_AMD64=fc0327ba27e89bd086cf426dff17d77de582953cdbbc10a6576540a06853ffcd
ARG SEVENZIP_SHA256_ARM64=5b0ac3aa91c1e3499f011d6af69d7f6b4de3ef2f011d9e2ff44c58ebd04aa388

# UnRAR, built from RARLAB's source (their Linux binaries are x64 only), for the Extractor plugin
# (.rar). The latest stable source: unrarsrc-7.3.x are 7.30 betas.
ARG UNRAR_VERSION=7.2.3
ARG UNRAR_SHA256=3995af0aa32b1505a566da053725551a1f0698dc42b2fdf7ba7d65db0d004e33

# DB-IP's IP to Country Lite (CC BY 4.0, https://db-ip.com), from its publisher. Monthly releases.
ARG DBIP_MONTH=2026-10
ARG DBIP_SHA256=4cd44536ddfd40fec7eca94a233f7d19f38d470e6522e653cb8d27001f5fe177

RUN apk add --no-cache build-base curl libarchive-tools patch patchelf tzdata xz

WORKDIR /build
COPY . .

# Deluge, in a virtualenv: every package pinned with its hash; zope.interface builds from source
# (no musl wheel). Then Alpine's pyOpenSSL fix, and the GeoIP shim as a top-level module.
RUN \
    python3 -m venv /opt/deluge \
    && /opt/deluge/bin/pip install --no-cache-dir --require-hashes --requirement requirements.txt \
    && /opt/deluge/bin/python -c "import importlib.metadata as m, sys; v = m.version('deluge'); sys.exit(0 if v == '${VERSION}' else f'requirements.txt has deluge {v}, docker-bake.hcl ${VERSION}')" \
    && site="$(/opt/deluge/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')" \
    && patch -d "${site}" -p1 < patches/pyopenssl-26.patch \
    && install -m 644 assets/GeoIP.py "${site}/GeoIP.py" \
    && /opt/deluge/bin/pip uninstall --yes pip \
    && /opt/deluge/bin/python -m compileall -q "${site}"

# Everything else the runtime image gets, staged under /rootfs
RUN \
    mkdir -p /rootfs/usr/local/bin /rootfs/usr/share/GeoIP /rootfs/usr/share/zoneinfo /rootfs/config \
    && install -m 644 assets/entrypoint.py /rootfs/entrypoint.py \
    && cp -r defaults /rootfs/defaults \
    && cp -r /usr/share/zoneinfo/. /rootfs/usr/share/zoneinfo/ \
    \
    && case "${TARGETARCH}" in \
        amd64) arch=x64; sha="${SEVENZIP_SHA256_AMD64}" ;; \
        arm64) arch=arm64; sha="${SEVENZIP_SHA256_ARM64}" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && curl -fsSL -o 7z.tar.xz \
        "https://github.com/ip7z/7zip/releases/download/${SEVENZIP_VERSION}/7z$(echo "${SEVENZIP_VERSION}" | tr -d .)-linux-${arch}.tar.xz" \
    && echo "${sha}  7z.tar.xz" | sha256sum -c - \
    && bsdtar -xf 7z.tar.xz 7zzs \
    && install -m 755 7zzs /rootfs/usr/local/bin/7zzs \
    && ln -s 7zzs /rootfs/usr/local/bin/7zr \
    \
    && curl -fsSL -o unrar.tar.gz "https://www.rarlab.com/rar/unrarsrc-${UNRAR_VERSION}.tar.gz" \
    && echo "${UNRAR_SHA256}  unrar.tar.gz" | sha256sum -c - \
    && tar -xzf unrar.tar.gz \
    && make -C unrar -j"$(nproc)" unrar LDFLAGS="-pthread -static" \
    && install -m 755 unrar/unrar /rootfs/usr/local/bin/unrar \
    \
    && curl -fsSL -o dbip.mmdb.gz "https://download.db-ip.com/free/dbip-country-lite-${DBIP_MONTH}.mmdb.gz" \
    && echo "${DBIP_SHA256}  dbip.mmdb.gz" | sha256sum -c - \
    && gunzip -c dbip.mmdb.gz > /rootfs/usr/share/GeoIP/dbip-country-lite.mmdb

# tar and unzip for the Extractor plugin (.tar, .tar.gz/bz2/xz/lzma, .zip): libarchive's bsdtar and
# bsdunzip, from Alpine. bsdtar decompresses by itself, where GNU tar would run gzip, bzip2 and xz.
# Dynamically linked: their libraries go to a directory of their own, found through their RUNPATH,
# so they cannot replace the runtime image's (Python's libssl, libz...). musl itself is the
# runtime's.
RUN \
    mkdir -p /rootfs/usr/lib/archive-tools \
    && for bin in bsdtar bsdunzip; do install -m 755 "/usr/bin/${bin}" "/rootfs/usr/local/bin/${bin}"; done \
    && ln -s bsdtar /rootfs/usr/local/bin/tar \
    && ln -s bsdunzip /rootfs/usr/local/bin/unzip \
    && ldd /usr/bin/bsdtar /usr/bin/bsdunzip \
        | awk '$2 == "=>" && $3 !~ /ld-musl/ { print $3 }' | sort -u \
        | xargs -I{} cp -L {} /rootfs/usr/lib/archive-tools/ \
    && patchelf --set-rpath /usr/lib/archive-tools \
        /rootfs/usr/local/bin/bsdtar /rootfs/usr/local/bin/bsdunzip /rootfs/usr/lib/archive-tools/*


FROM dhi.io/python:3.13.16-alpine3.24@sha256:de5a7323ef92a3a89981600520a9ad5494b43b21fd594b31aa3a0b3266ef88f1

ENV DELUGE_BIN="deluged" \
    XDG_CONFIG_HOME="/config" \
    PYTHON_EGG_CACHE="/config/plugins/.python-eggs" \
    TMPDIR="/tmp" \
    PATH="/opt/deluge/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

COPY --from=build /opt/deluge /opt/deluge
COPY --from=build /rootfs/ /
COPY --from=build --chown=65532:65532 /rootfs/config /config

# The runtime image's non-root user
USER 65532:65532
WORKDIR /config
VOLUME ["/config"]

ENTRYPOINT ["/opt/deluge/bin/python", "/entrypoint.py"]
