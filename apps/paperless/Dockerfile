# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# paperless-ngx on Docker Hardened Images, Debian 13 (trixie, as upstream): built in the -dev variant
# (apt, shell), run on the runtime variant (no shell, no package manager). No s6: each container
# runs its own command (granian, celery, manage.py). See README.md.

# jbig2enc, for OCRmyPDF's lossless JBIG2 optimisation: not in Debian. Built from its author's
# release tag (paperless-ngx/builder only has 0.30 packages). Links Leptonica, which Tesseract
# already brings into the image. Updated with its sha256 by .github/workflows/app-downloads.yaml
FROM dhi.io/python:3.14.8-debian13-dev@sha256:5b7724d3ca177d536fe88db1de8c900f29671f2cca613358e618567acfe526b2 AS jbig2enc
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG JBIG2ENC_VERSION=0.32
ARG JBIG2ENC_SHA256=5b3b1c48617e5b1608f916a78038ea867a2c9eb20c2ff34a78a48a243f655c2a

ENV DEBIAN_FRONTEND=noninteractive
# hadolint ignore=DL3008
RUN apt-get update && apt-get install --yes --quiet --no-install-recommends build-essential cmake curl gzip libleptonica-dev pkg-config

WORKDIR /src
RUN \
    curl -fsSL -o jbig2enc.tar.gz "https://github.com/agl/jbig2enc/archive/refs/tags/${JBIG2ENC_VERSION}.tar.gz" \
    && echo "${JBIG2ENC_SHA256}  jbig2enc.tar.gz" | sha256sum -c - \
    && tar -xzf jbig2enc.tar.gz \
    && cmake -S "jbig2enc-${JBIG2ENC_VERSION}" -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j"$(nproc)" \
    && install -D -m 755 "$(find build -type f -name jbig2 -perm -u+x | head -1)" /out/jbig2 \
    && /out/jbig2 --version


FROM dhi.io/python:3.14.8-debian13-dev@sha256:5b7724d3ca177d536fe88db1de8c900f29671f2cca613358e618567acfe526b2 AS build
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG VERSION

# The release tarball: backend, prebuilt frontend, collected static files, compiled translations,
# and the hash-locked requirements. Updated with its sha256 by .github/workflows/app-downloads.yaml
ARG PAPERLESS_SHA256=438d0df9adbb4319cb5d5ac83c97834e93a1dd10cd8b4b7bd3b5dae9992a4fd1

ENV DEBIAN_FRONTEND=noninteractive

# What paperless runs besides Python (paperless 3.3 code, OCRmyPDF): see README.md. Not the
# PostgreSQL client (assets/paperless-wait-for-db), MariaDB, gosu, s6, or Tesseract languages
# beyond English (assets/paperless-tessdata fetches them).
ARG RUNTIME_PACKAGES="\
    fonts-liberation \
    ghostscript \
    gpg \
    icc-profiles-free \
    imagemagick-7.q16 \
    jbig2dec \
    libmagic1t64 \
    libpq5 \
    media-types \
    pngquant \
    poppler-utils \
    qpdf \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    unpaper"

# libpq 18 from PostgreSQL's own repository (apt.postgresql.org): paperless's prebuilt psycopg-c
# wheel needs it (PQfullProtocolVersion), and Debian trixie has 17. Upstream's image has 17, so
# psycopg there falls back to its pure-Python implementation; here it uses the C one.
ARG PGDG_KEY_FINGERPRINT=B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8

# hadolint ignore=DL3008
RUN \
    apt-get update \
    && apt-get install --yes --quiet --no-install-recommends ca-certificates curl gpg \
    && curl -fsSL -o /tmp/pgdg.asc https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    && test "$(gpg --show-keys --with-colons /tmp/pgdg.asc | awk -F: '$1 == "fpr" { print $10; exit }')" = "${PGDG_KEY_FINGERPRINT}" \
    && gpg --dearmor -o /usr/share/keyrings/pgdg.gpg /tmp/pgdg.asc \
    && echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install --yes --quiet --no-install-recommends fontconfig imagemagick xz-utils ${RUNTIME_PACKAGES} \
    && dpkg-query -W -f '${Version}' libpq5 | grep -q '^18' \
    && fc-cache -f

WORKDIR /build
COPY . .

# paperless itself, under /usr/src/paperless as upstream; its Python packages in a virtualenv
RUN \
    curl -fsSL -o paperless.tar.xz \
        "https://github.com/paperless-ngx/paperless-ngx/releases/download/v${VERSION}/paperless-ngx-v${VERSION}.tar.xz" \
    && echo "${PAPERLESS_SHA256}  paperless.tar.xz" | sha256sum -c - \
    && mkdir -p /usr/src/paperless \
    && tar -xJf paperless.tar.xz -C /usr/src/paperless --strip-components=1 \
        paperless-ngx/src paperless-ngx/static paperless-ngx/uv.lock paperless-ngx/requirements.txt \
        paperless-ngx/docker/rootfs/usr/local/bin/wait-for-redis.py \
        paperless-ngx/docker/rootfs/etc/ImageMagick-6/paperless-policy.xml \
    && python3 scripts/requirements.py /usr/src/paperless/uv.lock /usr/src/paperless/requirements.txt > requirements.install.txt \
    && python3 -m venv /opt/paperless \
    && /opt/paperless/bin/pip install --no-cache-dir --require-hashes --requirement requirements.install.txt \
    && /opt/paperless/bin/pip uninstall --yes pip \
    && /opt/paperless/bin/python -m compileall -q /opt/paperless /usr/src/paperless/src

# Everything the runtime image gets besides /opt/paperless and /usr/src/paperless, under /rootfs:
# the packages above with their dependencies (minus what the runtime image has), jbig2enc, the
# fontconfig cache, the helper commands, and upstream's ImageMagick policy (resource limits, PDF
# allowed, SVG/MVG/PostScript and URL delegates refused). Trixie has ImageMagick 7, which reads
# /etc/ImageMagick-7: upstream's image still writes the policy to ImageMagick-6, where it is unused.
COPY --from=dhi.io/python:3.14.8-debian13@sha256:b2dee88be07689a608f86c392dd863f20399f8ffcbe99eff6bdb4f04485d9298 /var/lib/dpkg /runtime-dpkg
COPY --from=dhi.io/python:3.14.8-debian13@sha256:b2dee88be07689a608f86c392dd863f20399f8ffcbe99eff6bdb4f04485d9298 /etc/passwd /etc/group /runtime-etc/
COPY --from=jbig2enc /out/jbig2 /rootfs/usr/local/bin/jbig2
RUN \
    python3 scripts/stage-packages.py /runtime-dpkg /rootfs ${RUNTIME_PACKAGES} \
    && install -D -m 644 /usr/src/paperless/docker/rootfs/etc/ImageMagick-6/paperless-policy.xml \
        /rootfs/etc/ImageMagick-7/policy.xml \
    && mkdir -p /rootfs/var/cache \
    && cp -a /var/cache/fontconfig /rootfs/var/cache/ \
    && install -D -m 755 /usr/src/paperless/docker/rootfs/usr/local/bin/wait-for-redis.py /rootfs/usr/local/bin/wait-for-redis.py \
    && install -m 755 assets/paperless-tessdata assets/paperless-wait-for-db /rootfs/usr/local/bin/ \
    && rm -rf /usr/src/paperless/docker /usr/src/paperless/uv.lock /usr/src/paperless/requirements.txt \
    && python3 scripts/deduplicate.py /usr/src/paperless \
    && mkdir -p /usr/src/paperless/data /usr/src/paperless/media /usr/src/paperless/consume /usr/src/paperless/export \
    && install -D -m 644 /runtime-etc/passwd /rootfs/etc/passwd \
    && install -D -m 644 /runtime-etc/group /rootfs/etc/group \
    && echo 'paperless:x:1000:1000:paperless:/usr/src/paperless:/usr/sbin/nologin' >> /rootfs/etc/passwd \
    && echo 'paperless:x:1000:' >> /rootfs/etc/group


FROM dhi.io/python:3.14.8-debian13@sha256:b2dee88be07689a608f86c392dd863f20399f8ffcbe99eff6bdb4f04485d9298

ENV PATH="/opt/paperless/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONWARNINGS="ignore:::django.http.response:517" \
    PNGX_CONTAINERIZED=1 \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

COPY --from=build /rootfs/ /
COPY --from=build /opt/paperless /opt/paperless
COPY --from=build --chown=1000:1000 /usr/src/paperless /usr/src/paperless

# paperless (1000), as upstream: the IDs deployments of upstream's image already run as. With an
# /etc/group entry, Celery's start-up check finds the group; without one it assumes root and warns.
USER 1000:1000
WORKDIR /usr/src/paperless/src
EXPOSE 8000

CMD ["granian", "--interface", "asginl", "--ws", "paperless.asgi:application"]
