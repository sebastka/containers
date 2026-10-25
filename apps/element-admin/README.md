# Element Admin

Element Admin on [Docker Hardened Images](https://hub.docker.com/hardened-images): built with
`dhi.io/node:26-alpine3.24-dev`, served by `dhi.io/nginx:1-alpine3.24`, where upstream uses
`docker.io/library/node:24-alpine` and `ghcr.io/nginx/nginx-unprivileged`.

- Official repo: https://github.com/element-hq/element-admin
- Official Dockerfile: https://github.com/element-hq/element-admin/blob/main/Dockerfile

The source is a named build context in `docker-bake.hcl`, a git checkout of the commit Renovate
pins there, so this image builds upstream's tree with our own Dockerfile rather than theirs.

## This image does not serve Element Admin on its own

It ships the built assets and a **placeholder** server block that answers every path, `/health`
included, with `503` and a message saying so. That is deliberate: an image with no site
configuration must not look healthy to a probe. **The deployment supplies the real server block.**

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
    index index.runtime.html index.html;          # runtime first, built page as the fallback

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
    }
    location = /health {
        default_type application/json;
        return 200 '{"status": "ok"}';
    }
}
```

Mount it over `/etc/nginx/conf.d/default.conf`. Mounting the whole `conf.d` directory instead
replaces `http_customisations.conf` too, which carries `set_real_ip_from` and `real_ip_header`.

Also shipped, for that block to include:

| path | contents |
| --- | --- |
| `/etc/nginx/security_headers.conf` | upstream's CSP, `X-Frame-Options`, `X-Content-Type-Options`, `X-Robots-Tag` |
| `/etc/nginx/conf.d/http_customisations.conf` | upstream's `set_real_ip_from` and `real_ip_header`, minus their `server_tokens`, which the hardened `nginx.conf` already sets and nginx refuses to see twice |

### The runtime configuration is still needed

The built `index.html` contains a literal `APP_CONFIG_PLACEHOLDER`. Serve it unmodified and the app
has no homeserver. Something in the deployment must do what `replace-config.sh` did:

```sh
CONFIG=$(printf '{\n  "serverName": "%s"\n}\n' "$SERVER_NAME" | base64 -w 0)
sed "s/APP_CONFIG_PLACEHOLDER/${CONFIG}/" /dist/index.html > /tmp/index.runtime.html
```

`/dist/index.runtime.html` is a symlink to `/tmp/index.runtime.html`, so writing that path is
enough for the `index index.runtime.html index.html;` above to pick it up, and `/tmp` can stay the
`emptyDir` a read-only root filesystem needs. An init container sharing that volume is the usual
way; the alternative is serving a pre-rendered `index.html` of your own.

## Other differences from upstream's image

**Pre-compression.** Upstream writes `gzip -k /app/dist/**/*`, which needs bash; under `/bin/sh`
that glob reaches one level deep and leaves nested assets uncompressed. This uses `find`, so every
file gets a `.gz` companion for `gzip_static`.
