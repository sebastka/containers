# Containers

Collection of container images heavily inspired by [home-operations/containers](https://github.com/home-operations/containers).

| App | What it is |
| --- | --- |
| [dbdump2s3](apps/dbdump2s3) | PostgreSQL and MariaDB backups, encrypted to an age or PGP recipient and uploaded to S3 |
| [debian-debug](apps/debian-debug) | Debian with networking, database and troubleshooting tools, to debug from inside a cluster |
| [deluge](apps/deluge) | Deluge, with libtorrent and its Python binding built from source |
| [element-admin](apps/element-admin) | Element Admin, the administration interface for a Matrix homeserver |
| [paperless](apps/paperless) | paperless-ngx, without s6: one process per container |
| [stork](apps/stork) | ISC Stork server, the monitoring dashboard for Kea DHCP and BIND 9 |
| [zabbix-server](apps/zabbix-server) | Zabbix server for PostgreSQL, compiled from source |
| [zabbix-web-nginx](apps/zabbix-web-nginx) | nginx serving the Zabbix frontend's static files |
| [zabbix-web-php](apps/zabbix-web-php) | php-fpm running the Zabbix frontend |

Each app has a README covering what differs from upstream's image and anything a deployment has to provide. Most run on [Docker Hardened Images](https://hub.docker.com/hardened-images), whose runtime variants have no package manager and, in some cases, no shell.

## How an app is built

`apps/<name>/docker-bake.hcl` declares the version, source, description and licence, and `.github/workflows/release.yaml` builds every app whose directory changed, plus all of them weekly so patched base packages reach the images.

`container_test.go` runs on pull requests, on a native runner for each platform in the matrix, against the image loaded into that runner's daemon. The release path skips it: by then the change has already passed on its pull request, and the image is pushed by digest rather than loaded.

Versions come from Renovate where a datasource can supply them, and from `.github/workflows/app-downloads.yaml` where one cannot — a pinned download needs its checksum updating in the same commit, which no datasource provides.
