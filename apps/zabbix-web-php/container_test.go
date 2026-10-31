package main

import (
	"testing"

	helpers "github.com/home-operations/containers/tests"
)

func Test(t *testing.T) {
	image := helpers.GetTestImage("ghcr.io/sebastka/zabbix-web-php:rolling")

	helpers.RequireCommandSucceeds(t, image, nil, "/usr/sbin/php-fpm85", "-v")
	helpers.RequireFileExists(t, image, "/usr/share/zabbix/index.php")

	// The pool configuration has to parse, or the container starts and dies
	helpers.RequireCommandSucceeds(t, image, nil,
		"/usr/sbin/php-fpm85", "--fpm-config", "/etc/php85/php-fpm.conf", "-t")

	// Every extension the Zabbix frontend requires. Losing one shows up as a blank page or a
	// failed pre-requisites check in the setup wizard, not as a build error.
	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`set -e
		/usr/sbin/php-fpm85 -m > /tmp/mods
		for m in bcmath ctype curl fileinfo gd gettext ldap mbstring openssl pgsql session SimpleXML sockets xmlreader xmlwriter; do
			grep -qx "$m" /tmp/mods || { echo "php extension missing: $m"; exit 1; }
		done`)
}
