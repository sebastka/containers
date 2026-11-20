# syntax=docker/dockerfile:1@sha256:572cebbc2b15e6f84c077742952674889cb63cd5e9b80abdffcbe587b6f19183

# Dumps a PostgreSQL or MariaDB database, encrypts it to an age or PGP recipient, and uploads it to
# an S3-compatible bucket. Everything a restore needs is in the image, plus the private key.
#
# Debian, where this was Alpine: pg_dump refuses to dump a server newer than itself, and no Alpine
# branch carries a PostgreSQL 19 client -- not 3.24, not edge. Both projects publish apt
# repositories and neither publishes apk ones, so the clients now come from PostgreSQL and MariaDB
# themselves rather than from a distribution, each repository's key checked by fingerprint before
# anything is installed from it.
FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2
ARG VERSION

# Checked against the keys as downloaded, so a substituted key fails the build rather than signing
# packages nobody meant to trust
ARG PGDG_KEY_FINGERPRINT=B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8
ARG MARIADB_KEY_FINGERPRINT=177F4010FE56CA3336300305F1656F24C74CD1D8

# The series, not a patch release: it serves 13.0.2 today and its patch releases as they appear,
# the way the base image digest carries patched Debian packages. A major is a deliberate edit.
ARG MARIADB_SERIES=13.0

# gnupg, not just gpg: Debian splits the suite, and the agent it pulls in is what holds a secret
# key -- without it a PGP recipient can be encrypted to but never generated or restored from.
#
# The apt packages are deliberately not version-pinned (DL3008 is off repo-wide): a suite carries
# one version of each package and replaces it the moment a patched one lands, so a pinned version
# would turn a security update into a failed build. The base image digest is the pin.
RUN set -eu; \
    apt-get update; \
    apt-get install --yes --quiet --no-install-recommends ca-certificates curl gpg; \
    \
    curl -fsSL -o /tmp/pgdg.asc https://www.postgresql.org/media/keys/ACCC4CF8.asc; \
    test "$(gpg --show-keys --with-colons /tmp/pgdg.asc | awk -F: '$1 == "fpr" { print $10; exit }')" \
        = "${PGDG_KEY_FINGERPRINT}"; \
    gpg --dearmor -o /usr/share/keyrings/pgdg.gpg /tmp/pgdg.asc; \
    echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list; \
    \
    curl -fsSL -o /tmp/mariadb.asc https://supplychain.mariadb.com/MariaDB-Server-GPG-KEY; \
    test "$(gpg --show-keys --with-colons /tmp/mariadb.asc | awk -F: '$1 == "fpr" { print $10; exit }')" \
        = "${MARIADB_KEY_FINGERPRINT}"; \
    gpg --dearmor -o /usr/share/keyrings/mariadb.gpg /tmp/mariadb.asc; \
    echo "deb [signed-by=/usr/share/keyrings/mariadb.gpg] https://deb.mariadb.org/${MARIADB_SERIES}/debian trixie main" \
        > /etc/apt/sources.list.d/mariadb.list; \
    \
    apt-get update; \
    apt-get install --yes --quiet --no-install-recommends \
        age \
        awscli \
        gnupg \
        mariadb-client \
        postgresql-client \
        xz-utils; \
    \
    pg_version="$(dpkg-query -W -f '${Version}' postgresql-client)"; \
    dpkg --compare-versions "${pg_version}" ge 19 \
        || { echo "postgresql-client is ${pg_version}: the pgdg repository did not apply, and Debian's 17 cannot dump a 19 server" >&2; exit 1; }; \
    \
    mariadb_version="$(dpkg-query -W -f '${Version}' mariadb-client)"; \
    case "${mariadb_version}" in \
        *+maria*) ;; \
        *) echo "mariadb-client is ${mariadb_version}: that is Debian's, not MariaDB's own repository" >&2; exit 1 ;; \
    esac; \
    \
    rm -rf /var/lib/apt/lists/* /tmp/pgdg.asc /tmp/mariadb.asc

COPY --chmod=755 assets/dbdump2s3 /usr/local/bin/dbdump2s3

# Numeric, so a Kubernetes runAsNonRoot check can verify it without resolving a name
USER 65532:65532

ENTRYPOINT ["/usr/local/bin/dbdump2s3"]
