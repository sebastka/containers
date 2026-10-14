#!/usr/bin/env python3
"""Updates apps/paperless's pinned downloads: the paperless-ngx release (VERSION in docker-bake.hcl,
PAPERLESS_SHA256 in the Dockerfile) and jbig2enc (agl/jbig2enc, built from source).

Run by .github/workflows/app-downloads.yaml, which turns the changes into a pull request; also
runnable by hand. Standard library only. Uses the sha256 digests GitHub lists for release assets.
Prints a Markdown summary of what changed to stdout (part of the pull request body).
"""

import hashlib
import json
import os
import re
import sys
import urllib.request

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DOCKERFILE = os.path.join(APP, 'Dockerfile')
BAKE = os.path.join(APP, 'docker-bake.hcl')


def github(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'sebastka/containers app-downloads'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = f'Bearer {os.environ["GH_TOKEN"]}'
    with urllib.request.urlopen(urllib.request.Request(f'https://api.github.com/{path}', headers=headers), timeout=60) as r:
        return json.load(r)


def asset_digest(release, name):
    asset = next((a for a in release['assets'] if a['name'] == name), None)
    if not asset or not (asset.get('digest') or '').startswith('sha256:'):
        raise RuntimeError(f'{name}: no such asset, or no sha256 digest, in {release["tag_name"]}')
    return asset['digest'].removeprefix('sha256:')


def get_arg(text, name):
    return re.search(rf'^ARG {name}=(\S+)$', text, re.M).group(1)


def set_arg(text, name, value):
    return re.sub(rf'^(ARG {name}=)\S+$', lambda m: m.group(1) + value, text, flags=re.M)


def check_paperless(dockerfile, bake):
    current = re.search(r'variable "VERSION" \{.*?default = "([^"]+)"', bake, re.S).group(1)
    release = github('repos/paperless-ngx/paperless-ngx/releases/latest')
    version = release['tag_name'].removeprefix('v')
    digest = asset_digest(release, f'paperless-ngx-v{version}.tar.xz')
    if version == current and digest == get_arg(dockerfile, 'PAPERLESS_SHA256'):
        return dockerfile, bake, None
    bake = re.sub(r'(variable "VERSION" \{.*?default = ")[^"]+(")', lambda m: m.group(1) + version + m.group(2), bake, flags=re.S)
    dockerfile = set_arg(dockerfile, 'PAPERLESS_SHA256', digest)
    return dockerfile, bake, f'paperless-ngx {current} → {version} ({release["html_url"]})'


def check_jbig2enc(dockerfile, bake):
    """The latest release of agl/jbig2enc, built from its tag archive (no source asset on every
    release, so the sha256 is computed from the archive GitHub serves)."""
    current = get_arg(dockerfile, 'JBIG2ENC_VERSION')
    release = github('repos/agl/jbig2enc/releases/latest')
    version = release['tag_name']
    url = f'https://github.com/agl/jbig2enc/archive/refs/tags/{version}.tar.gz'
    request = urllib.request.Request(url, headers={'User-Agent': 'sebastka/containers app-downloads'})
    with urllib.request.urlopen(request, timeout=120) as r:
        digest = hashlib.sha256(r.read()).hexdigest()
    if version == current and digest == get_arg(dockerfile, 'JBIG2ENC_SHA256'):
        return dockerfile, bake, None
    dockerfile = set_arg(dockerfile, 'JBIG2ENC_VERSION', version)
    dockerfile = set_arg(dockerfile, 'JBIG2ENC_SHA256', digest)
    return dockerfile, bake, f'jbig2enc {current} → {version} ({release["html_url"]})'


def main():
    dockerfile, bake = open(DOCKERFILE).read(), open(BAKE).read()
    original = (dockerfile, bake)
    changes = []
    for check in (check_paperless, check_jbig2enc):
        try:
            dockerfile, bake, change = check(dockerfile, bake)
        except Exception as error:  # One source failing must not hold back the other
            print(f'::warning::{check.__name__}: {error}', file=sys.stderr)
            continue
        if change:
            changes.append(change)
    if (dockerfile, bake) != original:
        open(DOCKERFILE, 'w').write(dockerfile)
        open(BAKE, 'w').write(bake)
    print('`apps/paperless`:\n')
    print('\n'.join(f'- {change}' for change in changes) or '- (none)')


if __name__ == '__main__':
    main()
