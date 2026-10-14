#!/usr/bin/env python3
"""Writes the requirements to install, from a paperless-ngx release's uv.lock and requirements.txt.

Usage: requirements.py <uv.lock> <requirements.txt> > requirements.install.txt

The release's requirements.txt is `uv export --all-extras`, hashes included. This keeps the
entries paperless-ngx needs with the extras below, minus PRUNE and whatever only they need (walking
uv.lock's dependency graph), and the PyPI index only: every kept entry stays pinned to its hashes.

PRUNE is the local HuggingFace embedding backend: PyTorch (several hundred MB) and what builds on it.
paperless imports it only when PAPERLESS_AI_LLM_EMBEDDING_BACKEND is huggingface; the openai-like
and ollama backends do not need it.
"""

import re
import sys
import tomllib

EXTRAS = {'postgres', 'webserver'}  # Not mariadb
PRUNE = {'torch', 'sentence-transformers', 'llama-index-embeddings-huggingface'}


def normalize(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def needed(lock):
    packages = {}
    for package in lock['package']:
        packages.setdefault(normalize(package['name']), []).append(package)

    seen, queue = set(), [('paperless-ngx', frozenset(EXTRAS))]
    while queue:
        name, extras = queue.pop()
        if (name, extras) in seen or name in PRUNE:
            continue
        seen.add((name, extras))
        for package in packages.get(name, []):
            edges = list(package.get('dependencies', []))
            for extra in extras:
                edges += package.get('optional-dependencies', {}).get(extra, [])
            for edge in edges:
                queue.append((normalize(edge['name']), frozenset(edge.get('extra', []))))
    return {name for name, _ in seen}


def main():
    lock_path, requirements_path = sys.argv[1:3]
    with open(lock_path, 'rb') as f:
        keep = needed(tomllib.load(f))

    # An entry starts at column 0 ("name==version ..." or "name @ url ..."); its hashes and
    # "# via" comments follow, indented
    entries, current = [], None
    for line in open(requirements_path):
        if line.startswith(('#', '--')) or not line.strip():
            continue  # Header and index options: PyPI is pip's default
        if not line[0].isspace():
            current = [line]
            entries.append(current)
        elif current is not None:
            current.append(line)

    kept = dropped = 0
    for entry in entries:
        name = normalize(re.split(r'[=@ ;\[]', entry[0], maxsplit=1)[0])
        if name in keep:
            sys.stdout.writelines(line for line in entry if not line.lstrip().startswith('#'))
            kept += 1
        else:
            dropped += 1
    print(f'requirements.py: kept {kept} entries, dropped {dropped}', file=sys.stderr)


if __name__ == '__main__':
    main()
