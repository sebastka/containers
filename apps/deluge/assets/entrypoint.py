"""Runs $DELUGE_BIN (deluged by default, or deluge-web) in the foreground on /config: upstream's
entrypoint.sh, in Python since the image has no shell."""

import os
import shutil
import sys

CONFIG = '/config'
LOG_LEVELS = {'deluged': 'info', 'deluge-web': 'warning'}

binary = os.environ.get('DELUGE_BIN', 'deluged')
if binary not in LOG_LEVELS:
    sys.exit(f'DELUGE_BIN must be one of {", ".join(LOG_LEVELS)}, not {binary!r}')

if not os.path.exists(os.path.join(CONFIG, 'core.conf')):
    shutil.copy('/defaults/core.conf', os.path.join(CONFIG, 'core.conf'))
os.makedirs(os.path.join(CONFIG, 'plugins', '.python-eggs'), exist_ok=True)

# sys.prefix: the virtualenv this runs from (/opt/deluge)
os.execv(
    os.path.join(sys.prefix, 'bin', binary),
    [binary, '--do-not-daemonize', '--config', CONFIG, '--loglevel', LOG_LEVELS[binary], *sys.argv[1:]],
)
