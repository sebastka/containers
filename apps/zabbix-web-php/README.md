# Zabbix frontend (PHP)

The PHP half of the Zabbix web interface: `php-fpm` and nothing else. The nginx half is [zabbix-web-nginx](../zabbix-web-nginx). Upstream runs both in one container under supervisord.

- Zabbix documentation: https://www.zabbix.com/documentation/7.4/
- Upstream's image: https://github.com/zabbix/zabbix-docker/tree/7.4/Dockerfiles/web-nginx-pgsql

Built from the same verified source tarball as [zabbix-server](../zabbix-server); the frontend is the `ui/` directory of that release.

## Where PHP comes from

Docker Hardened Images publish no FPM SAPI — `dhi.io/php` ships the CLI in both variants — and `php85-fpm` is not in the hardened apk mirror either. It comes from **upstream Alpine's community repository**, which the Dockerfile adds explicitly rather than inheriting invisibly from `dhi.io/php`, whose dev variant has Alpine's repos configured. The base layers are hardened; PHP and its extensions are stock Alpine.

The extensions are the set upstream installs, which is what the setup wizard's pre-requisites page checks: `bcmath ctype curl fileinfo gd gettext ldap mbstring openssl pgsql session simplexml sockets xmlreader xmlwriter`. `ldap` is there because the frontend can authenticate against it.

## Configuration

`/etc/php85/php-fpm.conf` ships with one pool listening on **9000**, with the limits the Zabbix documentation asks for. It is tuning only, so mount over it if you want different `pm` settings.

The deployment-specific part is the frontend's own config, which this image deliberately does not ship:

```
/usr/share/zabbix/conf/zabbix.conf.php
```

That path is not a convention: it is `CConfigFile::CONFIG_FILE_PATH`, which the frontend resolves against its own root and reads from nowhere else. Upstream's image puts the file under `/etc/zabbix/web` and symlinks it here; mounting it where it is read saves the indirection.

It holds the database credentials and the address of zabbix-server. Without it the frontend redirects to `setup.php` and offers its installation wizard, which is the right behaviour for an unconfigured container. The chart renders it.

Both containers need the frontend files — nginx serves the static assets from its copy, php-fpm executes from its own — so neither needs a shared volume, at the cost of about 60 MB duplicated.

Runs as **1997:1995**, upstream's ids.
