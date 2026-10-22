# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

# Dumps a PostgreSQL or MariaDB database, encrypts it to an age or PGP recipient, and uploads it to
# an S3-compatible bucket. Everything a restore needs is in the image, plus the private key.
#
# Alpine 3.24, not older: pg_dump refuses to dump a server newer than itself. Alpine 3.22 tops out
# at postgresql17-client and 3.23 was the first branch to carry postgresql18-client, so moving the
# base image backwards silently breaks every PostgreSQL backup.
FROM docker.io/library/alpine:3.24.3@sha256:b3413572228e34bd1c9245f5565e6cd127005655e8a7899aef33d8e83255c9e6
ARG VERSION

# The apk packages are deliberately not version-pinned (DL3018 is off repo-wide). An Alpine branch
# carries exactly one version of each package and drops it the moment a patched one replaces it, so
# `age=1.3.1-r6` would turn a security update into a failed build rather than a reproducible one.
# The base image digest above is the pin: it fixes the whole package set, and Renovate bumping that
# digest is what pulls patched packages in.
RUN apk add --no-cache \
        age \
        aws-cli \
        ca-certificates \
        curl \
        gnupg \
        mariadb-client \
        postgresql18-client \
        xz

COPY --chmod=755 assets/dbdump2s3 /usr/local/bin/dbdump2s3

# Numeric, so a Kubernetes runAsNonRoot check can verify it without resolving a name
USER 65532:65532

ENTRYPOINT ["/usr/local/bin/dbdump2s3"]
