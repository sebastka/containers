# Zabbix frontend (nginx)

The nginx half of the Zabbix web interface: serves the static assets and hands `.php` to [zabbix-web-php](../zabbix-web-php). Upstream runs both in one container under supervisord.

- Zabbix documentation: https://www.zabbix.com/documentation/7.4/
- Upstream's image: https://github.com/zabbix/zabbix-docker/tree/7.4/Dockerfiles/web-nginx-pgsql

Built from the same verified source tarball as [zabbix-server](../zabbix-server). Assets are pre-compressed for `gzip_static`; the `.php` files are not, since nginx never sends their contents.

## This image serves nothing on its own

It ships the frontend's files and a **placeholder** server block that answers every path with `503`, because it has no idea where php-fpm is. The deployment supplies the real one:

```nginx
server {
    listen 8080;
    root /usr/share/zabbix;
    index index.php;

    gzip on;
    gzip_static on;

    location = /ping { access_log off; default_type text/plain; return 200 "pong\n"; }
    location /assets { expires 10d; }

    location ~ \.php$ {
        fastcgi_pass <the php service>:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
        fastcgi_read_timeout 300;
    }

    location ~ /\.ht { deny all; }
}
```

Mount it over `/etc/nginx/conf.d/default.conf`.

`SCRIPT_FILENAME` must resolve inside the **php-fpm** container, not this one: both carry the frontend at the same path, which is why `$document_root` works for either.

## What nginx needs writable

This nginx is compiled with `--pid-path=/run/nginx/nginx.pid` and its temp paths under `/var/lib/nginx/tmp`. On a read-only root filesystem both have to be writable or it will not start. Logs need nothing: they are already symlinks to `/dev/stdout` and `/dev/stderr`.

Runs as **65532**, the hardened image's own user, which only needs to read the frontend's files.
