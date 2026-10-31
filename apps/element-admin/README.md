# Element Admin

Element Admin on [Docker Hardened Images](https://hub.docker.com/hardened-images): built with `dhi.io/node:26-alpine3.24-dev`, served by `dhi.io/nginx:1-alpine3.24`, where upstream uses `docker.io/library/node:24-alpine` and `ghcr.io/nginx/nginx-unprivileged`.

- Official repo: https://github.com/element-hq/element-admin
- Official Dockerfile: https://github.com/element-hq/element-admin/blob/main/Dockerfile

The source is a named build context in `docker-bake.hcl`, a git checkout of the commit Renovate pins there, so this image builds upstream's tree with our own Dockerfile rather than theirs.

## This image does not serve Element Admin on its own

It ships the built assets and a **placeholder** server block that answers every path, `/health` included, with `503` and a message saying so. That is deliberate: an image with no site configuration must not look healthy to a probe. **The deployment supplies the real server block.**

Upstream's image instead carries two start-up scripts. Neither is here:

| upstream script | what it did | why not here |
| --- | --- | --- |
| `configure-listen.sh` | probed `/proc/net` for IPv4/IPv6 and generated the `listen` directives | your server block states its own, and it knows the cluster's address families |
| `replace-config.sh` | injected `SERVER_NAME` into `index.html` | not nginx configuration at all — see below |

### What your server block has to do

```nginx
server {
    listen 8080;                                  # the image exposes 8080
    root /dist;
    index index.html;

    gzip on;
    gzip_static on;                               # every asset has a .gz companion

    include /etc/nginx/security_headers.conf;     # shipped, upstream's

    location /assets {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
        include /etc/nginx/security_headers.conf;
    }
    location / {
        add_header Cache-Control "no-cache";
        try_files $uri $uri/ /;
        include /etc/nginx/security_headers.conf;

        # The runtime configuration, see below
        sub_filter 'APP_CONFIG_PLACEHOLDER' 'ewogICJzZXJ2ZXJOYW1lIjogImV4YW1wbGUuY29tIgp9Cg==';
        sub_filter_once on;
        sub_filter_types text/html;
        gzip_static off;
    }
    location = /health {
        default_type application/json;
        return 200 '{"status": "ok"}';
    }
}
```

Mount it over `/etc/nginx/conf.d/default.conf`. Mounting the whole `conf.d` directory instead replaces `http_customisations.conf` too, which carries `set_real_ip_from` and `real_ip_header`.

Also shipped, for that block to include:

| path | contents |
| --- | --- |
| `/etc/nginx/security_headers.conf` | upstream's CSP, `X-Frame-Options`, `X-Content-Type-Options`, `X-Robots-Tag` |
| `/etc/nginx/conf.d/http_customisations.conf` | upstream's `set_real_ip_from` and `real_ip_header`, minus their `server_tokens`, which the hardened `nginx.conf` already sets and nginx refuses to see twice |

### The runtime configuration

The built `index.html` contains `window.APP_CONFIG_BASE64 = "APP_CONFIG_PLACEHOLDER"`. Serve it unmodified and the app has no homeserver. Upstream's image replaced that from a start-up script; this one has no scripts, so the server block does it with `sub_filter`, as above. The value is base64 of the app's configuration:

```sh
printf '{\n  "serverName": "%s"\n}\n' example.com | base64 -w 0
```

**`gzip_static off` in that location is not optional.** Every file in `/dist` has a `.gz` companion, and `sub_filter` cannot rewrite a response nginx sends precompressed: with `gzip_static on`, `index.html.gz` goes out untouched and the placeholder reaches any client that accepts gzip, which is every browser. Turning it off for the HTML only costs the precompression of one 4 KB file — responses are still gzipped, just compressed per request, and `/assets` keeps its `.gz` files.

A deployment that would rather pre-render the page can still do so: `/dist/index.runtime.html` is a symlink to `/tmp/index.runtime.html`, so an init container writing that path is picked up by `index index.runtime.html index.html;`, and `/tmp` can stay the `emptyDir` a read-only root filesystem needs. Do not pre-render it into a ConfigMap, though: `index.html` names the hashed asset bundles, so a copy stops matching the image on its next build and serves 404s for its own JavaScript with nothing failing a probe.

### What nginx needs writable

This nginx is compiled with `--pid-path=/run/nginx/nginx.pid` and its temp paths under `/var/lib/nginx/tmp`, not under `/tmp` as `nginx-unprivileged` was. On a read-only root filesystem both have to be writable or it will not start. Logs need nothing: `access.log` and `error.log` are already symlinks to `/dev/stdout` and `/dev/stderr`.

Run it as **65532**, the image's own user. `/var/lib/nginx` is mode `0750` and owned by it, so another uid cannot even traverse in.

## Other differences from upstream's image

**Pre-compression.** Upstream writes `gzip -k /app/dist/**/*`, which needs bash; under `/bin/sh` that glob reaches one level deep and leaves nested assets uncompressed. This uses `find`, so every file gets a `.gz` companion for `gzip_static`.
