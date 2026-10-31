# Zabbix server

Zabbix server for PostgreSQL on [Docker Hardened Images](https://hub.docker.com/hardened-images): compiled in `dhi.io/alpine-base:3.24-dev`, run on `dhi.io/alpine-base:3.24`, which has no package manager.

- Zabbix documentation: https://www.zabbix.com/documentation/7.4/
- Upstream's images: https://github.com/zabbix/zabbix-docker
- Source releases: https://cdn.zabbix.com/zabbix/sources/stable/

Built from the source tarball, verified against the checksum published beside it. Only `--enable-server`, where upstream builds the agent, agent2, proxy, java gateway and web service from the same tree and splits the outputs afterwards.

## This image has no entrypoint

Upstream's image carries one that renders `/etc/zabbix/zabbix_server.conf` from `ZBX_*` environment variables and loads the database schema on first start. This one does neither: it runs

```
/usr/sbin/zabbix_server --foreground -c /etc/zabbix/zabbix_server.conf
```

and the deployment supplies that file. The chart in `sebastka/charts` renders it and loads the schema from an init container, from the files this image stages at `/usr/share/zabbix/`:

| file | what it is |
| --- | --- |
| `schema.sql` | tables, indexes and constraints |
| `images.sql` | the stock icon set |
| `data.sql` | templates, value maps and the default admin user |

Load all three, in that order, into an empty database before the server first starts. `psql` is in the image for exactly that: the schema would otherwise need a second image, and so a second registry to hold it and credentials to pull from it, to load files this one already carries.

One consequence worth having: upstream's entrypoint copies `ssl/ssl_ca` into `ssl/ssl_ca_internal` under `/var/lib/zabbix` and fails when it cannot, which is why deployments that mount an emptyDir there need an init container to seed the image's layout first. Nothing here reads those paths, so no seeding is needed.

## What differs from upstream's build

**Three item types are missing.** The hardened apk mirror carries no `libssh-dev`, `openipmi-dev` or `libmodbus-dev`, so the build drops `--with-ssh`, `--with-openipmi` and `--with-libmodbus`: SSH agent items, IPMI polling and Modbus items will not work. Everything else upstream enables is here — SNMP, HTTP agent items and webhook media types, ODBC, LDAP, VMware and XML preprocessing.

**fping is staged explicitly.** Zabbix shells out to it for `icmpping` items. The pod needs `net.ipv4.ping_group_range` to cover the server's group for it to work unprivileged:

```yaml
securityContext:
  sysctls:
    - {name: net.ipv4.ping_group_range, value: '0 1995'}
```

**The account is written out, not created.** This busybox has no `getent`, so the ids are written directly: **1997:1995**, upstream's, and what the homelab Deployment pins.

## Versions

`docker-bake.hcl` holds the release and the Dockerfile its checksum; `scripts/update-downloads.py` moves both together, nightly, since no Renovate datasource yields a checksum. It stays on the branch the pin is already on — 7.4.x while VERSION is a 7.4 — because Zabbix minor releases are feature releases with their own support windows. Change `VERSION` by hand to move branch.
