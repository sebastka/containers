#!/usr/bin/env python3
"""Updates apps/deluge's pinned downloads and its Python dependencies.

In the Dockerfile: libtorrent, Boost, 7-Zip, UnRAR and the DB-IP database. Then Deluge itself
(docker-bake.hcl and requirements.in), and finally requirements.txt, recompiled from
requirements.in.

Run by .github/workflows/app-downloads.yaml, which turns the changes into a pull request; also
runnable by hand from the repository root. No third-party Python packages; the recompile needs the
uv binary, which mise provides. Each source is checked on its own: one being unreachable leaves the
others to update. The recompile is the exception and is fatal, because the three files naming
Deluge have to agree.

- libtorrent: the latest 2.0.x release of arvidn/libtorrent (the series the Dockerfile builds;
  2.1 is released alongside), with the sha256 digest GitHub lists for its source tarball.
- Boost: the latest release of boostorg/boost, likewise (the b2 source tarball without docs).
- 7-Zip: the latest GitHub release of ip7z/7zip, with the sha256 digests GitHub lists for its
  linux-x64 and linux-arm64 assets.
- UnRAR: the source of the newest stable release. Source file names do not tell betas apart
  (unrarsrc-7.3.1 is 7.30 beta 1), so releases come from the Linux binaries RARLAB lists without a
  beta suffix: rarlinux-x64-723 <-> unrarsrc-7.2.3, while 7.30 beta 1 is rarlinux-x64-730b1.
- DB-IP: the current month's IP to Country Lite, once published (early in the month it may not be).
- Deluge: the latest release on PyPI, written to both files that name it. The build checks the
  compiled requirements.txt agrees with VERSION, so they have to move together, in one commit.
- requirements.txt: recompiled every run, which is also how its transitive dependencies move.
  Renovate must not touch this file. Its pip_requirements manager rewrites the version in place but
  writes the new hashes out as a second entry under the name PyPI registers (zope.interface, where
  uv writes the normalised zope-interface), leaving the first entry on the old release's hashes.
  pip then fails --require-hashes. See #144 and .renovaterc.json5.

Prints a Markdown summary of what changed to stdout (the pull request body).
"""

import datetime
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.request

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DOCKERFILE = os.path.join(APP, 'Dockerfile')
BAKE = os.path.join(APP, 'docker-bake.hcl')
REQUIREMENTS_IN = os.path.join(APP, 'requirements.in')
REQUIREMENTS_TXT = os.path.join(APP, 'requirements.txt')
USER_AGENT = 'sebastka/containers app-downloads'
VERSION_DEFAULT = re.compile(r'(variable "VERSION" \{.*?default = ")([^"]+)(")', re.S)


def read(path):
    with open(path) as f:
        return f.read()


def write(path, text):
    with open(path, 'w') as f:
        f.write(text)


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


def check_deluge():
    """Deluge is named in docker-bake.hcl (the image tag) and requirements.in (what pip installs)."""
    with open(BAKE) as f:
        bake = f.read()
    match = VERSION_DEFAULT.search(bake)
    if not match:
        raise RuntimeError('no VERSION variable in docker-bake.hcl')
    current = match.group(2)
    version = json.loads(fetch('https://pypi.org/pypi/deluge/json'))['info']['version']
    if version == current:
        return None

    with open(REQUIREMENTS_IN) as f:
        requirements_in = f.read()
    pinned, count = re.subn(r'^deluge==\S+$', lambda _: f'deluge=={version}', requirements_in, flags=re.M)
    if count != 1:
        raise RuntimeError(f'expected one "deluge==" line in requirements.in, found {count}')

    with open(BAKE, 'w') as f:
        f.write(VERSION_DEFAULT.sub(lambda m: m.group(1) + version + m.group(3), bake))
    with open(REQUIREMENTS_IN, 'w') as f:
        f.write(pinned)
    return f'Deluge {current} → {version} (https://pypi.org/project/deluge/{version}/)'


def pins(requirements):
    return dict(re.findall(r'^([A-Za-z0-9._-]+)==([^\s\\]+)', requirements, re.M))


def compile_requirements():
    """Recompiles requirements.txt with the command its own header documents, so the two cannot
    drift. uv writes the file only when it succeeds, and --no-header means the comment at the top is
    ours to put back."""
    with open(REQUIREMENTS_TXT) as f:
        before = f.read()

    header = ''
    for line in before.splitlines(keepends=True):
        if not line.startswith('#'):
            break
        header += line
    match = re.search(r'^#\s+(uv pip compile \S.*)$', header, re.M)
    if not match:
        raise RuntimeError('no "uv pip compile" command in the header of requirements.txt')

    subprocess.run(shlex.split(match.group(1)), cwd=APP, check=True, capture_output=True, text=True)
    with open(REQUIREMENTS_TXT) as f:
        after = header + f.read()
    with open(REQUIREMENTS_TXT, 'w') as f:
        f.write(after)
    if after == before:
        return None

    old, new = pins(before), pins(after)
    moved = [
        f'{name} {old.get(name, "(new)")} → {new.get(name, "(removed)")}'
        for name in sorted(old.keys() | new.keys())
        if old.get(name) != new.get(name)
    ]
    return 'requirements.txt: ' + (', '.join(moved) or 'hashes only')


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

    # After the Dockerfile, and in this order: the recompile has to see any new Deluge pin. Snapshot
    # all three first, so a failed recompile can put back a Deluge pin that was already written
    originals = {path: read(path) for path in (BAKE, REQUIREMENTS_IN, REQUIREMENTS_TXT)}

    try:
        change = check_deluge()
    except Exception as error:  # Writes nothing unless it succeeds outright, so recompile anyway
        failures.append(f'check_deluge: {error}')
    else:
        if change:
            changes.append(change)

    try:
        change = compile_requirements()
    except Exception as error:
        # Fatal, unlike every source above. A partly updated Dockerfile is still consistent; three
        # files that disagree about Deluge are not, and the build asserts they agree. Failing here
        # stops the workflow before it opens a pull request that could never go green
        for path, text in originals.items():
            write(path, text)
        for failure in failures:
            print(f'::warning::{failure}', file=sys.stderr)
        detail = (getattr(error, 'stderr', '') or '').strip()
        sys.exit(
            f'::error::requirements.txt could not be recompiled, so docker-bake.hcl, '
            f'requirements.in and requirements.txt are unchanged: {error}'
            + (f'\n{detail}' if detail else '')
        )
    else:
        if change:
            changes.append(change)

    print('Updates pinned downloads in `apps/deluge`, versions and sha256:\n')
    print('\n'.join(f'- {change}' for change in changes) or '- (none)')
    for failure in failures:
        print(f'::warning::{failure}', file=sys.stderr)


if __name__ == '__main__':
    main()
