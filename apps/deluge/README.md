# Deluge

Deluge on [Docker Hardened Images](https://hub.docker.com/hardened-images/catalog/dhi/python):
built in `dhi.io/python:3.14-alpine3.24-dev`, run on `dhi.io/python:3.14-alpine3.24` (no shell,
no package manager, user 65532). Replaces `ghcr.io/home-operations/deluge`, whose plugins do not
load (Alpine's package bug, [ALPINE_BUG_REPORT.md](ALPINE_BUG_REPORT.md)) and whose GeoIP lookups
never worked.

## Contents

- **Deluge**, from PyPI, in a virtualenv at `/opt/deluge` (on `PATH`): `deluged`, `deluge-web`,
  `deluge-console`. Every Python package is pinned with its hash in `requirements.txt`, generated
  from `requirements.in` (command in its header).
  - **libtorrent 2.0**, built from source with its Python binding (the `libtorrent` stage).
    Deluge 2.2 requires libtorrent >= 1.2 and also runs on 2.1, but was mostly developed against
    2.0, the more conservative choice; PyPI only has musl wheels of 2.1, up to Python 3.13.
    Boost.Python, libtorrent and the C++ runtime are linked statically into the binding, which
    only needs musl and the runtime image's OpenSSL, so OpenSSL fixes come with DHI's updates. The
    stage only rebuilds when libtorrent or Boost change (build cache).
  - **setuptools < 81**: Deluge 2.2 finds its plugins through `pkg_resources`, which setuptools 81
    removed. With it, the bundled (zipped) plugin eggs load as they should.
  - **`patches/pyopenssl-26.patch`**, from Alpine: Deluge 2.2 does not start with pyOpenSSL 25+.
- **GeoIP**: Deluge 2.2 only reads the discontinued legacy `.dat` format, so
  `assets/GeoIP.py` provides the `GeoIP` module interface it imports over a MaxMind-format
  database, read by MaxMind's `maxminddb`. The data is DB-IP's
  [IP to Country Lite](https://db-ip.com/db/download/ip-to-country-lite), from its publisher,
  pinned by month and sha256, at `/usr/share/GeoIP/dbip-country-lite.mmdb` (set as
  `geoip_db_location`). Licensed CC BY 4.0: "IP Geolocation by DB-IP", https://db-ip.com.
- **For the Extractor plugin**, every format it handles:
  - `unrar` (.rar), built statically from RARLAB's source, and 7-Zip's static `7zzs` from its
    GitHub releases, as `7zr` (.7z). Both pinned by sha256.
  - libarchive's `bsdtar` and `bsdunzip` from Alpine, as `tar` (.tar, .tar.gz/bz2/xz/lzma) and
    `unzip` (.zip). bsdtar decompresses by itself, so no gzip, bzip2 or xz programs are needed.
    Their shared libraries live in `/usr/lib/archive-tools`, found through their RUNPATH, so they
    never replace the runtime image's own. (`unxz`, `unlzma` and `bunzip2` are on Extractor's
    list of commands but no format uses them.)
- `tzdata`, for `TZ`.

## Running

The entrypoint (`assets/entrypoint.py`) starts `$DELUGE_BIN`, `deluged` (default) or
`deluge-web`, in the foreground on `/config`, seeding `/config/core.conf` from
`defaults/core.conf` when missing. Kubernetes manifests can instead run
`/opt/deluge/bin/deluged` or `/opt/deluge/bin/deluge-web` with their own arguments.

## Updating

- **Deluge**: `VERSION` in `docker-bake.hcl` and `deluge` in `requirements.in`, then regenerate
  `requirements.txt`. The build fails when the two disagree.
- **Python packages**: Renovate updates `requirements.txt`, hashes included; it keeps setuptools
  below 81 (`.renovaterc.json5`).
- **libtorrent, Boost, 7-Zip, UnRAR and DB-IP**: `.github/workflows/app-downloads.yaml` runs
  `scripts/update-downloads.py` every Monday (or by hand, Actions > App Downloads) and opens a
  pull request with the new versions and their sha256. libtorrent stays on the 2.0 series. UnRAR
  betas are skipped: the script takes the newest release RARLAB lists as stable. DB-IP moves to the
  new month once it is published.
  The script also runs locally, from the repository root.

Once Alpine's package is fixed and home-operations' image ships it, going back to their image is
an option, at the cost of the hardened base, GeoIP and the static archive tools.
