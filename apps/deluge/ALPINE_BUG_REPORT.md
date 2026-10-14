# community/deluge: no-pkg_resources.patch finds no plugins (bundled eggs are zipped)

**Package:** `community/deluge` 2.2.0-r3 (3.24-stable), also 2.2.0-r4 (master), same patch
**Python:** 3.14.5, py3-setuptools 82.0.1

## Summary

`no-pkg_resources.patch` replaces `pkg_resources` in `deluge/pluginmanagerbase.py` with
`importlib.metadata`. The new `scan_for_plugins()` only recognises plugins as **directories**:
`<name>.egg/` with an `EGG-INFO/` inside, or `.egg-info/` / `.dist-info/` directories. The
package installs Deluge's bundled plugins as **zipped** `.egg` files, so none is found and no
plugin can be enabled. Before the patch, `pkg_resources.Environment` handled zipped eggs.

## Steps to reproduce

```console
$ apk add deluge
$ ls -l /usr/lib/python3.14/site-packages/deluge/plugins/
-rw-r--r-- 1 root root 53145 ... AutoAdd-1.8-py3.14.egg
-rw-r--r-- 1 root root 41167 ... Label-0.3-py3.14.egg
...
$ deluged --do-not-daemonize --loglevel info
... [WARNING ][deluge.pluginmanagerbase] Cannot enable non-existent plugin Label
```

With `"enabled_plugins": ["AutoAdd", "Label", "Stats"]` in `core.conf`, none is enabled, and the
web UI's Preferences > Plugins list is empty. The same applies to third-party plugins dropped
into the user's `plugins` directory, which are distributed as zipped eggs too.

## Expected

The bundled plugins (AutoAdd, Blocklist, Execute, Extractor, Label, Notifications, Scheduler,
Stats, Toggle, WebUi) are listed and can be enabled, as with `pkg_resources`.

## Cause

In the patched `scan_for_plugins()`:

```python
if item.endswith('.egg') and os.path.isdir(item_path):
```

`os.path.isdir()` is false for a zipped egg, and no other branch matches a `.egg` file.

## Suggested fix

`importlib.metadata.PathDistribution` accepts a `zipfile.Path`, and `zipimport` imports from a
zipped egg on `sys.path`, so zipped eggs can be handled alongside the directory case:

```python
import zipfile
from importlib.metadata import Distribution, PathDistribution

if item.endswith('.egg') and os.path.isfile(item_path) and zipfile.is_zipfile(item_path):
    if item_path not in sys.path:
        sys.path.insert(0, item_path)  # zipimport
    dist = PathDistribution(zipfile.Path(item_path, 'EGG-INFO/'))
elif item.endswith('.egg') and os.path.isdir(item_path):
    ...  # existing branch
```

Checked on 2.2.0-r3 with the bundled eggs: all ten plugins are found, with their entry points,
and `deluge_label:CorePlugin` loads from the zipped egg.

## Workaround

Unpack each egg in place under the same name, e.g. in a derived container image:

```sh
cd /usr/lib/python3*/site-packages/deluge/plugins
for egg in *.egg; do
    mv "$egg" "$egg.zip" && python3 -m zipfile -e "$egg.zip" "$egg" && rm "$egg.zip"
done
```
