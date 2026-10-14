#!/usr/bin/env python3
"""Hard-links identical files under a directory, so each content is stored once in the image layer.

Usage: deduplicate.py <directory>

The release ships the frontend twice (src/documents/static/frontend, and collected in static/),
along with other repeated files: about 580 MB, the job upstream's deduplicate.py does in its image.
"""

import collections
import hashlib
import os
import sys


def main():
    by_content = collections.defaultdict(list)
    for root, _, files in os.walk(sys.argv[1]):
        for name in files:
            path = os.path.join(root, name)
            if os.path.isfile(path) and not os.path.islink(path):
                with open(path, 'rb') as f:
                    by_content[(os.path.getsize(path), hashlib.file_digest(f, 'sha256').digest())].append(path)

    saved = 0
    for (size, _), paths in by_content.items():
        first, *others = sorted(paths)
        for path in others:
            if not os.path.samefile(first, path):
                os.remove(path)
                os.link(first, path)
                saved += size
    print(f'deduplicate.py: {saved // 1048576} MiB saved')


if __name__ == '__main__':
    main()
