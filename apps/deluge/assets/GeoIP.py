"""The legacy `GeoIP` module interface Deluge 2.2 looks countries up with, over a MaxMind-format
(.mmdb) database read by MaxMind's maxminddb.

Deluge imports `GeoIP` (or `pygeoip`), both for the discontinued legacy .dat format, and only
calls `GeoIP(path, flags)` and `.country_code_by_addr(ip)`. Installed into Deluge's virtualenv as
a top-level module by the Dockerfile.
"""

import maxminddb


class GeoIP:
    def __init__(self, path, flags=0):
        self._reader = maxminddb.open_database(path)

    def country_code_by_addr(self, addr):
        record = self._reader.get(addr) or {}
        return (record.get('country') or {}).get('iso_code') or ''
