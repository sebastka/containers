package main

import (
	"testing"

	helpers "github.com/home-operations/containers/tests"
)

func Test(t *testing.T) {
	image := helpers.GetTestImage("ghcr.io/sebastka/deluge:rolling")

	helpers.RequireHTTPEndpoint(t, image, helpers.HTTPTestConfig{
		Port: "8112",
	}, &helpers.ContainerConfig{
		Env: map[string]string{
			"DELUGE_BIN": "deluge-web",
		},
	})

	// What this image adds over a plain pip install: plugins found, libtorrent loads, country
	// lookups work, and the Extractor plugin's tools are there (see README.md)
	helpers.RequireCommandSucceeds(t, image, nil, "/opt/deluge/bin/python", "-c", `
import shutil, subprocess, sys

import libtorrent
import deluge.pluginmanagerbase as pmb
from GeoIP import GeoIP

class Scanner(pmb.PluginManagerBase):
    def __init__(self):
        pass

scanner = Scanner()
scanner.scan_for_plugins()
missing = {"AutoAdd", "Extractor", "Label", "Stats"} - set(scanner.available_plugins)
if missing:
    sys.exit(f"plugins not found: {sorted(missing)}")

country = GeoIP("/usr/share/GeoIP/dbip-country-lite.mmdb", 0).country_code_by_addr("8.8.8.8")
if len(country) != 2:
    sys.exit(f"GeoIP lookup failed: {country!r}")

for command in (["unrar", "-iver"], ["7zr", "i"], ["deluged", "--version"]):
    if not shutil.which(command[0]):
        sys.exit(f"{command[0]} not on PATH")
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

# The Extractor plugin's tar and unzip invocations (deluge_extractor/core.py), on archives made here
import bz2, gzip, io, lzma, os, tarfile, tempfile, zipfile

work = tempfile.mkdtemp()
data = io.BytesIO()
with tarfile.open(fileobj=data, mode="w") as tar:
    info = tarfile.TarInfo("hello.txt")
    info.size = 6
    tar.addfile(info, io.BytesIO(b"hello\n"))
archives = {
    "a.tar": (data.getvalue(), ["tar", "-xf"]),
    "a.tar.gz": (gzip.compress(data.getvalue()), ["tar", "-xzf"]),
    "a.tar.bz2": (bz2.compress(data.getvalue()), ["tar", "-xjf"]),
    "a.tar.xz": (lzma.compress(data.getvalue()), ["tar", "--xz", "-xf"]),
    "a.tar.lzma": (lzma.compress(data.getvalue(), format=lzma.FORMAT_ALONE), ["tar", "--lzma", "-xf"]),
}
zipped = io.BytesIO()
with zipfile.ZipFile(zipped, "w") as z:
    z.writestr("hello.txt", "hello\n")
archives["a.zip"] = (zipped.getvalue(), ["unzip"])

for name, (content, command) in archives.items():
    dest = os.path.join(work, name + ".d")
    os.mkdir(dest)
    with open(os.path.join(work, name), "wb") as f:
        f.write(content)
    subprocess.run(command + [os.path.join(work, name)], cwd=dest, check=True, stdout=subprocess.DEVNULL)
    if open(os.path.join(dest, "hello.txt")).read() != "hello\n":
        sys.exit(f"{name}: wrong content")

print("libtorrent", libtorrent.__version__, "| plugins", sorted(scanner.available_plugins), "| 8.8.8.8:", country)
`)
}
