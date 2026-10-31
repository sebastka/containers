package main

import (
	"testing"

	helpers "github.com/home-operations/containers/tests"
)

func Test(t *testing.T) {
	image := helpers.GetTestImage("ghcr.io/sebastka/zabbix-server:rolling")

	helpers.RequireCommandSucceeds(t, image, nil, "/usr/sbin/zabbix_server", "-V")

	// fping is what Zabbix shells out to for icmpping items, and it is easy to lose: nothing in
	// the build references it except the staging step
	helpers.RequireCommandSucceeds(t, image, nil, "/usr/sbin/fping", "-v")

	// The schema the chart loads before first start, and the client it loads it with
	helpers.RequireFileExists(t, image, "/usr/share/zabbix/schema.sql")
	helpers.RequireFileExists(t, image, "/usr/share/zabbix/images.sql")
	helpers.RequireFileExists(t, image, "/usr/share/zabbix/data.sql")
	helpers.RequireCommandSucceeds(t, image, nil, "/usr/bin/psql", "--version")

	// The configure flags that matter, checked through what the binary actually links rather than
	// trusting the build: losing --with-postgresql or --with-net-snmp would otherwise only show up
	// as a server that cannot reach its database or poll an SNMP device.
	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`set -e
		loader=$(echo /lib/ld-musl-*.so.1)
		"$loader" --list /usr/sbin/zabbix_server > /tmp/libs
		for lib in libpq libnetsnmp libcurl libxml2 libpcre2-8 libssl; do
			grep -q "$lib" /tmp/libs || { echo "zabbix_server is not linked against $lib"; exit 1; }
		done`)

	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`/usr/sbin/zabbix_server -V | grep -qE '^zabbix_server \(Zabbix\) 7\.'`)

	// net-snmp resolves textual OIDs, which is how Zabbix's own SNMP templates are written, only
	// from these. They come with net-snmp-libs in the build stage and are easy to leave behind.
	helpers.RequireFileExists(t, image, "/usr/share/snmp/mibs/IF-MIB.txt")
	helpers.RequireFileExists(t, image, "/usr/share/snmp/mibs/SNMPv2-MIB.txt")
}
