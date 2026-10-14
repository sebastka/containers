#!/usr/bin/env python3
"""Stages installed Debian packages, with their dependencies, for a runtime image without apt.

Usage: stage-packages.py <runtime dpkg dir> <rootfs> <package>...

Run in the build image after `apt-get install <package>...`. Resolves the packages' dependency
closure from dpkg's database (Depends and Pre-Depends; for alternatives, the one installed; virtual
packages through Provides), leaves out what the runtime image already has (its dpkg status, in
<runtime dpkg dir>) and the shell-providing essentials below, and copies the rest under <rootfs>:
each package's files except documentation, man pages and translations, a dpkg status entry per
package (status.d, as Docker Hardened Images keep theirs), and the update-alternatives links that
point into what was copied (/usr/bin/convert...).
"""

import glob
import os
import re
import shutil
import subprocess
import sys

# Never copied, even when depended on: the runtime image has no shell and should get none
EXCLUDE = {'bash', 'dash', 'coreutils', 'debianutils', 'dpkg', 'perl-base', 'sed', 'grep', 'tar',
           'findutils', 'util-linux', 'login', 'passwd', 'sysvinit-utils', 'init-system-helpers'}
SKIP_PREFIXES = ('/usr/share/doc/', '/usr/share/man/', '/usr/share/info/', '/usr/share/lintian/',
                 '/usr/share/locale/', '/usr/share/bug/')


def dpkg_query(*args):
    return subprocess.run(['dpkg-query', *args], check=True, capture_output=True, text=True).stdout


def installed():
    """name -> (depends, provides) for every installed package."""
    out = dpkg_query('-W', '-f', '${db:Status-Abbrev}\t${Package}\t${Pre-Depends}, ${Depends}\t${Provides}\n')
    packages = {}
    for line in out.splitlines():
        status, name, depends, provides = line.split('\t')
        if status.startswith('ii'):
            packages[name] = (depends, provides)
    return packages


def runtime_packages(dpkg_dir):
    names = {os.path.basename(p) for p in glob.glob(os.path.join(dpkg_dir, 'status.d', '*'))}
    status = os.path.join(dpkg_dir, 'status')
    if os.path.exists(status):
        names |= {l.split(':', 1)[1].strip() for l in open(status) if l.startswith('Package:')}
    return {n.split(':')[0] for n in names}


def closure(roots, packages):
    providers = {}
    for name, (_, provides) in packages.items():
        for item in filter(None, (p.strip() for p in provides.split(','))):
            providers.setdefault(re.split(r'[ (:]', item)[0], []).append(name)

    def resolve(dependency):  # "a (>= 1) | b" -> an installed package satisfying it
        for alternative in dependency.split('|'):
            name = re.split(r'[ (:]', alternative.strip())[0]
            if name in packages:
                return name
            if providers.get(name):
                return providers[name][0]
        return None

    seen, queue = set(), list(roots)
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        if name not in packages:
            sys.exit(f'{name}: not installed')
        seen.add(name)
        for dependency in filter(None, (d.strip() for d in packages[name][0].split(','))):
            resolved = resolve(dependency)
            if resolved is None:
                sys.exit(f'{name}: unsatisfied dependency {dependency}')
            queue.append(resolved)
    return seen


def copy(path, rootfs):
    target = rootfs + path
    if os.path.lexists(target):
        return
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.islink(path):
        os.symlink(os.readlink(path), target)
    elif os.path.isfile(path):
        shutil.copy2(path, target)


def main():
    dpkg_dir, rootfs, *roots = sys.argv[1:]
    packages = installed()
    present = runtime_packages(dpkg_dir)
    wanted = sorted(closure(roots, packages) - present - EXCLUDE)

    shells = [p for p in wanted for f in dpkg_query('-L', p).splitlines() if f in ('/bin/sh', '/usr/bin/sh')]
    if shells:
        sys.exit(f'would add a shell: {shells}')

    copied = set()
    for package in wanted:
        for path in dpkg_query('-L', package).splitlines():
            if path.startswith(SKIP_PREFIXES) or os.path.isdir(path) and not os.path.islink(path):
                continue
            copy(path, rootfs)
            copied.add(os.path.realpath(path))
        os.makedirs(f'{rootfs}/var/lib/dpkg/status.d', exist_ok=True)
        with open(f'{rootfs}/var/lib/dpkg/status.d/{package}', 'w') as f:
            f.write(dpkg_query('-s', package))

    # update-alternatives links: /usr/bin/convert -> /etc/alternatives/convert -> convert-im6.q16
    for link in glob.glob('/etc/alternatives/*'):
        if os.path.realpath(link) in copied:
            copy(link, rootfs)
            for directory in ('/usr/bin', '/usr/sbin', '/usr/lib'):
                for candidate in glob.glob(f'{directory}/*'):
                    if os.path.islink(candidate) and os.readlink(candidate) == link:
                        copy(candidate, rootfs)

    print(f'stage-packages.py: {len(wanted)} packages: {" ".join(wanted)}')


if __name__ == '__main__':
    main()
