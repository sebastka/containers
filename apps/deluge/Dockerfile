# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# Deluge on Docker Hardened Images: built in the -dev variant (shell, apk, compilers), run on the
# runtime variant (no shell, no package manager, non-root). See README.md.

# libtorrent and its Python binding, from source: the 2.0 series, the one Deluge 2.2 was mostly
# developed against (it requires >= 1.2, and also runs on 2.1). PyPI only has musl wheels of 2.1, up
# to Python 3.13. Boost.Python, libtorrent and the C++ runtime are linked statically into the
# binding, which then only needs musl and the runtime image's OpenSSL.
FROM dhi.io/python:3.14.8-alpine3.24-dev@sha256:a8b209bdf92fa536c182203eb2b09f0ddf55b4d3c37a4ab00eed2602d7ac33bb AS libtorrent

# Updated with their sha256 by .github/workflows/app-downloads.yaml
ARG BOOST_VERSION=1.92.0
ARG BOOST_SHA256=ea7b982002cc9dfbe59b0b217b206f470dc75f3de0bb2973d844118934d82411
ARG LIBTORRENT_VERSION=2.0.15
ARG LIBTORRENT_SHA256=5e2e79129823b7ea48721164c32b5aaf83d3fd733b5502100f6705b29f27bb02

# python-3.14-dev: the headers of the image's own Python, from DHI's apk repository (the -dev
# image does not include them)
RUN apk add --no-cache build-base cmake curl linux-headers openssl-dev python-3.14-dev xz

WORKDIR /src
RUN \
    curl -fsSL -o boost.tar.xz \
        "https://github.com/boostorg/boost/releases/download/boost-${BOOST_VERSION}/boost-${BOOST_VERSION}-b2-nodocs.tar.xz" \
    && echo "${BOOST_SHA256}  boost.tar.xz" | sha256sum -c - \
    && tar -xJf boost.tar.xz

WORKDIR /src/boost-${BOOST_VERSION}
RUN \
    ./bootstrap.sh --with-libraries=python --with-python=python3 \
    && ./b2 -j"$(nproc)" -d0 --with-python variant=release link=static runtime-link=shared \
        cxxflags=-fPIC cflags=-fPIC stage

WORKDIR /src

# The binding may only link musl and OpenSSL dynamically: checked on its dependency lines, since
# listed alone it also reports Python's own symbols as missing (the interpreter provides them).
RUN \
    curl -fsSL -o libtorrent.tar.gz \
        "https://github.com/arvidn/libtorrent/releases/download/v${LIBTORRENT_VERSION}/libtorrent-rasterbar-${LIBTORRENT_VERSION}.tar.gz" \
    && echo "${LIBTORRENT_SHA256}  libtorrent.tar.gz" | sha256sum -c - \
    && tar -xzf libtorrent.tar.gz \
    && cmake -S "libtorrent-rasterbar-${LIBTORRENT_VERSION}" -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=OFF \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
        -Dpython-bindings=ON \
        -Dpython-egg-info=OFF \
        -DBoost_ROOT="/src/boost-${BOOST_VERSION}/stage" \
        -DBoost_INCLUDE_DIR="/src/boost-${BOOST_VERSION}" \
        -DBoost_USE_STATIC_LIBS=ON \
        -DCMAKE_MODULE_LINKER_FLAGS="-static-libstdc++ -static-libgcc" \
    && cmake --build build -j"$(nproc)" \
    && mkdir -p /out \
    && find build -name 'libtorrent*.so' -path '*bindings/python*' -exec install -m 755 {} /out/ \; \
    && loader="$(echo /lib/ld-musl-*.so.1)" \
    && { "${loader}" --list /out/libtorrent*.so || true; } | grep '=>' > deps.txt \
    && cat deps.txt \
    && ! grep -v -E 'libc\.musl|libssl\.so|libcrypto\.so' deps.txt \
    && PYTHONPATH=/out python3 -c 'import libtorrent; print("libtorrent", libtorrent.__version__)'


FROM dhi.io/python:3.14.8-alpine3.24-dev@sha256:a8b209bdf92fa536c182203eb2b09f0ddf55b4d3c37a4ab00eed2602d7ac33bb AS build
ARG VERSION
ARG TARGETARCH

# 7-Zip's own static Linux build, as 7zr for the Extractor plugin (.7z)
# 7-Zip, UnRAR and DB-IP: updated with their sha256 by .github/workflows/app-downloads.yaml
ARG SEVENZIP_VERSION=26.05
ARG SEVENZIP_SHA256_AMD64=22cf82fcc6eb7474f1d5bb4f02c0f8ebd573a718089d6833dc30f8350a3b232e
ARG SEVENZIP_SHA256_ARM64=0b71f6cfc34669b3bf69f2347efd3429f77020665003a13b9cdc53b784270421

# UnRAR, built from RARLAB's source (their Linux binaries are x64 only), for the Extractor plugin
# (.rar). The latest stable source: unrarsrc-7.3.x are 7.30 betas.
ARG UNRAR_VERSION=7.2.3
ARG UNRAR_SHA256=3995af0aa32b1505a566da053725551a1f0698dc42b2fdf7ba7d65db0d004e33

# DB-IP's IP to Country Lite (CC BY 4.0, https://db-ip.com), from its publisher. Monthly releases.
ARG DBIP_MONTH=2026-10
ARG DBIP_SHA256=4cd44536ddfd40fec7eca94a233f7d19f38d470e6522e653cb8d27001f5fe177

# python-3.14-dev: lets zope.interface build its C extension rather than fall back to pure Python
RUN apk add --no-cache build-base curl libarchive-tools patch patchelf python-3.14-dev tzdata xz

WORKDIR /build
COPY . .
COPY --from=libtorrent /out/ /libtorrent/

# Deluge, in a virtualenv: every package pinned with its hash; zope.interface builds from source
# (no musl wheel). Then Alpine's pyOpenSSL fix, the GeoIP shim as a top-level module, and the
# libtorrent binding built above.
RUN \
    python3 -m venv /opt/deluge \
    && /opt/deluge/bin/pip install --no-cache-dir --require-hashes --requirement requirements.txt \
    && /opt/deluge/bin/python -c "import importlib.metadata as m, sys; v = m.version('deluge'); sys.exit(0 if v == '${VERSION}' else f'requirements.txt has deluge {v}, docker-bake.hcl ${VERSION}')" \
    && site="$(/opt/deluge/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')" \
    && patch -d "${site}" -p1 < patches/pyopenssl-26.patch \
    && install -m 644 assets/GeoIP.py "${site}/GeoIP.py" \
    && install -m 755 /libtorrent/libtorrent*.so "${site}/" \
    && /opt/deluge/bin/pip uninstall --yes pip \
    && /opt/deluge/bin/python -m compileall -q "${site}"

# Everything else the runtime image gets, staged under /rootfs
RUN \
    mkdir -p /rootfs/usr/local/bin /rootfs/usr/share/GeoIP /rootfs/usr/share/zoneinfo /config-dir \
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
# runtime's. musl's loader lists the libraries (`--list`, what ldd wraps): the -dev image has no
# ldd. Written to files rather than piped, since sh here has no pipefail.
RUN \
    mkdir -p /rootfs/usr/lib/archive-tools \
    && for bin in bsdtar bsdunzip; do install -m 755 "/usr/bin/${bin}" "/rootfs/usr/local/bin/${bin}"; done \
    && ln -s bsdtar /rootfs/usr/local/bin/tar \
    && ln -s bsdunzip /rootfs/usr/local/bin/unzip \
    && loader="$(echo /lib/ld-musl-*.so.1)" \
    && for bin in bsdtar bsdunzip; do "${loader}" --list "/usr/bin/${bin}"; done > libs.txt \
    && awk '$2 == "=>" && $3 !~ /ld-musl/ { print $3 }' libs.txt | sort -u > libs-to-copy.txt \
    && test -s libs-to-copy.txt \
    && xargs -I{} cp -L {} /rootfs/usr/lib/archive-tools/ < libs-to-copy.txt \
    && patchelf --set-rpath /usr/lib/archive-tools \
        /rootfs/usr/local/bin/bsdtar /rootfs/usr/local/bin/bsdunzip /rootfs/usr/lib/archive-tools/*


FROM dhi.io/python:3.14.8-alpine3.24@sha256:e50a61536c68e94237553f32a59f703f9766817cc4580734c516da27fbe0211d

ENV DELUGE_BIN="deluged" \
    XDG_CONFIG_HOME="/config" \
    PYTHON_EGG_CACHE="/config/plugins/.python-eggs" \
    TMPDIR="/tmp" \
    PATH="/opt/deluge/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

COPY --from=build /opt/deluge /opt/deluge
COPY --from=build /rootfs/ /
# Outside /rootfs: --chown only applies to a directory this COPY creates, not to one that exists
COPY --from=build --chown=65532:65532 /config-dir /config

# The runtime image's non-root user
USER 65532:65532
WORKDIR /config
VOLUME ["/config"]

ENTRYPOINT ["/opt/deluge/bin/python", "/entrypoint.py"]
