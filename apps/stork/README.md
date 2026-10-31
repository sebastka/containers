# Stork

ISC Stork server on [Docker Hardened Images](https://hub.docker.com/hardened-images): installed in `dhi.io/alpine-base:3.24-dev`, which has apk, and run on `dhi.io/alpine-base:3.24`, which does not.

- Stork Administrator Reference Manual: https://stork.readthedocs.io/en/stable/
- Installation: https://stork.readthedocs.io/en/stable/install.html#installing-on-alpine
- Downloads: https://downloads.isc.org/isc/stork/

ISC publishes Stork to its own Cloudsmith repository, which the build adds to the hardened image's apk configuration. `docker-bake.hcl` tracks the versions actually published there rather than the git tags, which run ahead of the packages.

## What the hardened base changes

**The Alpine branch is an argument, not something read from the image.** These images ship no `/etc/alpine-release`, so `ALPINE_BRANCH` names the branch for the Cloudsmith repository URL and the build checks it against `/etc/apk/repositories` before anything else runs. A base bumped to a new Alpine therefore fails the build rather than quietly installing from the wrong branch. It stays an argument so it can be pinned deliberately when ISC has not published for a new branch yet — the error message says so.

**The account is created by the Dockerfile.** The package's pre-install script calls `getent`, which this busybox does not have, so it fails and creates nothing:

```
* /proc/self/fd/7: line 7: getent: not found
```

The build writes the entries itself, appending to the runtime image's own `passwd` and `group` rather than replacing them.

**Do not change the uid or gid.** `stork-server` is **100:101**, which is what the image has always used and what the homelab Deployment pins with `runAsUser: 100` / `runAsGroup: 101`. The data in `/var/lib/stork-server` is owned by them, so moving to the hardened images' usual 65532 would orphan an existing volume.

## What the runtime image gets

`stork-server`, `stork-tool`, the LDAP hook, the web UI and the zone data — files only. Both binaries and the hook link musl and nothing else, checked through the musl loader at build time, so there is no library closure to carry along.
