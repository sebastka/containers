#!/usr/bin/env python3
"""Updates the pinned downloads in apps/deluge/Dockerfile: libtorrent, Boost, 7-Zip, UnRAR and the
DB-IP database.

Run by .github/workflows/app-downloads.yaml, which turns the changes into a pull request; also
runnable by hand from the repository root. Standard library only. Each source is checked on its
own: one being unreachable leaves the others to update.

- libtorrent: the latest 2.0.x release of arvidn/libtorrent (the series the Dockerfile builds;
  2.1 is released alongside), with the sha256 digest GitHub lists for its source tarball.
- Boost: the latest release of boostorg/boost, likewise (the b2 source tarball without docs).
- 7-Zip: the latest GitHub release of ip7z/7zip, with the sha256 digests GitHub lists for its
  linux-x64 and linux-arm64 assets.
- UnRAR: the source of the newest stable release. Source file names do not tell betas apart
  (unrarsrc-7.3.1 is 7.30 beta 1), so releases come from the Linux binaries RARLAB lists without a
  beta suffix: rarlinux-x64-723 <-> unrarsrc-7.2.3, while 7.30 beta 1 is rarlinux-x64-730b1.
- DB-IP: the current month's IP to Country Lite, once published (early in the month it may not be).

Prints a Markdown summary of what changed to stdout (the pull request body).
"""

import datetime
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

DOCKERFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Dockerfile')
USER_AGENT = 'sebastka/containers app-downloads'


def fetch(url, headers=None):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def sha256_of(url):
    return hashlib.sha256(fetch(url)).hexdigest()


def get_arg(dockerfile, name):
    match = re.search(rf'^ARG {name}=(\S+)$', dockerfile, re.M)
    if not match:
        sys.exit(f'ARG {name} not found in the Dockerfile')
    return match.group(1)


def set_arg(dockerfile, name, value):
    return re.sub(rf'^(ARG {name}=)\S+$', lambda m: m.group(1) + value, dockerfile, flags=re.M)


def github(path):
    headers = {'Accept': 'application/vnd.github+json'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = f'Bearer {os.environ["GH_TOKEN"]}'
    return json.loads(fetch(f'https://api.github.com/{path}', headers))


def asset_digest(release, name):
    asset = next((a for a in release['assets'] if a['name'] == name), None)
    if not asset or not (asset.get('digest') or '').startswith('sha256:'):
        raise RuntimeError(f'{name}: no such asset, or no sha256 digest, in {release["tag_name"]}')
    return asset['digest'].removeprefix('sha256:')


def check_libtorrent(dockerfile):
    current = get_arg(dockerfile, 'LIBTORRENT_VERSION')
    releases = [
        r for r in github('repos/arvidn/libtorrent/releases?per_page=50')
        if not r['prerelease'] and not r['draft'] and r['tag_name'].startswith('v2.0.')
    ]
    if not releases:
        raise RuntimeError('no 2.0.x release of arvidn/libtorrent')
    release = max(releases, key=lambda r: tuple(int(p) for p in r['tag_name'][1:].split('.')))
    version = release['tag_name'][1:]
    digest = asset_digest(release, f'libtorrent-rasterbar-{version}.tar.gz')
    if version == current and digest == get_arg(dockerfile, 'LIBTORRENT_SHA256'):
        return dockerfile, None
    dockerfile = set_arg(dockerfile, 'LIBTORRENT_VERSION', version)
    dockerfile = set_arg(dockerfile, 'LIBTORRENT_SHA256', digest)
    return dockerfile, f'libtorrent {current} → {version} ({release["html_url"]})'


def check_boost(dockerfile):
    current = get_arg(dockerfile, 'BOOST_VERSION')
    release = github('repos/boostorg/boost/releases/latest')
    version = release['tag_name'].removeprefix('boost-')
    digest = asset_digest(release, f'boost-{version}-b2-nodocs.tar.xz')
    if version == current and digest == get_arg(dockerfile, 'BOOST_SHA256'):
        return dockerfile, None
    dockerfile = set_arg(dockerfile, 'BOOST_VERSION', version)
    dockerfile = set_arg(dockerfile, 'BOOST_SHA256', digest)
    return dockerfile, f'Boost {current} → {version} ({release["html_url"]})'


def check_7zip(dockerfile):
    current = get_arg(dockerfile, 'SEVENZIP_VERSION')
    release = github('repos/ip7z/7zip/releases/latest')
    version = release['tag_name']
    digests = {}
    for arch, asset_arch in (('AMD64', 'x64'), ('ARM64', 'arm64')):
        digests[arch] = asset_digest(release, f'7z{version.replace(".", "")}-linux-{asset_arch}.tar.xz')

    changed = version != current or any(
        get_arg(dockerfile, f'SEVENZIP_SHA256_{arch}') != digest for arch, digest in digests.items()
    )
    if not changed:
        return dockerfile, None
    dockerfile = set_arg(dockerfile, 'SEVENZIP_VERSION', version)
    for arch, digest in digests.items():
        dockerfile = set_arg(dockerfile, f'SEVENZIP_SHA256_{arch}', digest)
    return dockerfile, f'7-Zip {current} → {version} ({release["html_url"]})'


def check_unrar(dockerfile):
    current = get_arg(dockerfile, 'UNRAR_VERSION')

    # RAR 7.23 <-> rarlinux-x64-723 <-> unrarsrc-7.2.3. rar_add.htm only links the newest source,
    # a beta while one is out, so try each stable Linux release, newest first, until its source
    # is there: RARLAB keeps older sources.
    downloads = fetch('https://www.rarlab.com/download.htm').decode('utf-8', 'replace')
    stable = sorted(set(re.findall(r'rar/rarlinux-x64-(\d{3})\.tar\.gz', downloads)), reverse=True)
    if not stable:
        raise RuntimeError('no stable rarlinux-x64 release on download.htm')

    for release in stable:
        version = '.'.join(release)
        if version == current:
            return dockerfile, None
        try:
            digest = sha256_of(f'https://www.rarlab.com/rar/unrarsrc-{version}.tar.gz')
            break
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
    else:
        raise RuntimeError(f'no source for any stable release: {", ".join(stable)}')

    dockerfile = set_arg(dockerfile, 'UNRAR_VERSION', version)
    dockerfile = set_arg(dockerfile, 'UNRAR_SHA256', digest)
    return dockerfile, f'UnRAR {current} → {version} (https://www.rarlab.com/rarnew.htm)'


def check_dbip(dockerfile):
    current = get_arg(dockerfile, 'DBIP_MONTH')
    month = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')
    if month == current:
        return dockerfile, None
    try:
        digest = sha256_of(f'https://download.db-ip.com/free/dbip-country-lite-{month}.mmdb.gz')
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return dockerfile, None  # Not published yet
        raise
    dockerfile = set_arg(dockerfile, 'DBIP_MONTH', month)
    dockerfile = set_arg(dockerfile, 'DBIP_SHA256', digest)
    return dockerfile, f'DB-IP IP to Country Lite {current} → {month}'


def main():
    with open(DOCKERFILE) as f:
        original = dockerfile = f.read()

    changes, failures = [], []
    for check in (check_libtorrent, check_boost, check_7zip, check_unrar, check_dbip):
        try:
            dockerfile, change = check(dockerfile)
        except Exception as error:  # One source failing must not hold back the others
            failures.append(f'{check.__name__}: {error}')
            continue
        if change:
            changes.append(change)

    if dockerfile != original:
        with open(DOCKERFILE, 'w') as f:
            f.write(dockerfile)

    print('Updates pinned downloads in `apps/deluge/Dockerfile`, versions and sha256:\n')
    print('\n'.join(f'- {change}' for change in changes) or '- (none)')
    for failure in failures:
        print(f'::warning::{failure}', file=sys.stderr)


if __name__ == '__main__':
    main()
