#!/usr/bin/env python3
"""Updates apps/zabbix-web-nginx's pinned Zabbix release: VERSION in docker-bake.hcl and
ZABBIX_SHA256 in the Dockerfile.

Run by .github/workflows/app-downloads.yaml, which turns the changes into a pull request; also
runnable by hand from the repository root. Standard library only. Renovate cannot do this: the
source tarball's checksum comes from a file beside it, which no datasource yields.

Stays on the branch the pin is already on, 7.4.x while VERSION is a 7.4: Zabbix minor releases are
feature releases with their own support windows, so moving between them is a decision rather than
an update. Change VERSION by hand to move branch.
"""

import json
import os
import re
import sys
import urllib.request

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DOCKERFILE = os.path.join(APP, 'Dockerfile')
BAKE = os.path.join(APP, 'docker-bake.hcl')
USER_AGENT = 'sebastka/containers app-downloads'
VERSION_DEFAULT = re.compile(r'(variable "VERSION" \{.*?default = ")([^"]+)(")', re.S)


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def github(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': USER_AGENT}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = f'Bearer {os.environ["GH_TOKEN"]}'
    request = urllib.request.Request(f'https://api.github.com/{path}', headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main():
    with open(BAKE) as f:
        bake = f.read()
    match = VERSION_DEFAULT.search(bake)
    if not match:
        sys.exit('no VERSION variable in docker-bake.hcl')
    current = match.group(2)
    branch = current.rsplit('.', 1)[0]

    releases = []
    for page in (1, 2):
        for tag in github(f'repos/zabbix/zabbix/tags?per_page=100&page={page}'):
            if re.fullmatch(rf'{re.escape(branch)}\.\d+', tag['name']):
                releases.append(tuple(int(p) for p in tag['name'].split('.')))
    if not releases:
        sys.exit(f'no {branch}.x tag found for zabbix/zabbix')
    version = '.'.join(str(p) for p in max(releases))
    if version == current:
        print(f'Zabbix {current} is current')
        return

    digest = fetch(
        f'https://cdn.zabbix.com/zabbix/sources/stable/{branch}/zabbix-{version}.tar.gz.sha256'
    ).decode().split()[0]
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        sys.exit(f'{version}: no sha256 beside the tarball, got {digest!r}')

    with open(DOCKERFILE) as f:
        dockerfile = f.read()
    dockerfile, count = re.subn(r'^(ARG ZABBIX_SHA256=)\S+$', lambda m: m.group(1) + digest,
                                dockerfile, flags=re.M)
    if count != 1:
        sys.exit(f'expected one ZABBIX_SHA256 line in the Dockerfile, found {count}')

    with open(DOCKERFILE, 'w') as f:
        f.write(dockerfile)
    with open(BAKE, 'w') as f:
        f.write(VERSION_DEFAULT.sub(lambda m: m.group(1) + version + m.group(3), bake))
    print(f'Zabbix {current} → {version} '
          f'(https://www.zabbix.com/rn/rn{version.replace(".", "_")})')


if __name__ == '__main__':
    main()
