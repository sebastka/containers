package main

import (
	"testing"

	helpers "github.com/home-operations/containers/tests"
)

func Test(t *testing.T) {
	image := helpers.GetTestImage("ghcr.io/sebastka/paperless:rolling")

	// The external programs paperless and OCRmyPDF call, its compiled Python modules, Django's
	// system checks, and a real OCR run: text rendered into a PDF, OCRmyPDF over it (Tesseract,
	// Ghostscript, PDF/A), read back with pdftotext.
	helpers.RequireCommandSucceeds(t, image, nil, "/opt/paperless/bin/python", "-c", `
import os, shutil, sqlite3, subprocess, sys, tempfile

for command in (["tesseract", "--version"], ["gs", "--version"], ["convert", "-version"],
                ["qpdf", "--version"], ["pdftotext", "-v"], ["pdftoppm", "-v"], ["unpaper", "--version"],
                ["pngquant", "--version"], ["jbig2", "--version"], ["gpg", "--version"]):
    if not shutil.which(command[0]):
        sys.exit(f"{command[0]} not on PATH")
    subprocess.run(command, check=True, capture_output=True)
for helper in ("paperless-tessdata", "paperless-wait-for-db", "wait-for-redis.py", "granian", "celery"):
    if not shutil.which(helper):
        sys.exit(f"{helper} not on PATH")

# The running user and group resolve (Celery assumes root, and warns, when the group does not)
import grp, pwd
print("user:", pwd.getpwuid(os.getuid()).pw_name, "group:", grp.getgrgid(os.getgid()).gr_name)

import granian, magic, ocrmypdf, pikepdf, psycopg, sqlite_vec, zxingcpp
if psycopg.pq.__impl__ != "c":
    sys.exit(f"psycopg implementation: {psycopg.pq.__impl__}, expected c")
db = sqlite3.connect(":memory:")
db.enable_load_extension(True)
sqlite_vec.load(db)
print("sqlite-vec", db.execute("select vec_version()").fetchone()[0], "| libmagic:", magic.from_buffer(b"%PDF-1.7\n", mime=True))

work = tempfile.mkdtemp()
env = dict(os.environ, PAPERLESS_DATA_DIR=f"{work}/data", PAPERLESS_MEDIA_ROOT=f"{work}/media",
           PAPERLESS_CONSUMPTION_DIR=f"{work}/consume", PAPERLESS_SECRET_KEY="test")
for directory in ("data", "media", "consume"):
    os.makedirs(f"{work}/{directory}")
# Django's system checks load every setting, app and model; migrations would need Redis (the cache)
subprocess.run([sys.executable, "manage.py", "check"], check=True, capture_output=True, env=env,
               cwd="/usr/src/paperless/src")

from PIL import Image, ImageDraw, ImageFont
font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 64)
page = Image.new("RGB", (1700, 600), "white")
ImageDraw.Draw(page).text((100, 250), "Paperless hardened image", fill="black", font=font)
page.save(f"{work}/in.pdf", resolution=200)
ocrmypdf.ocr(f"{work}/in.pdf", f"{work}/out.pdf", language=["eng"], output_type="pdfa", progress_bar=False)
text = subprocess.run(["pdftotext", f"{work}/out.pdf", "-"], check=True, capture_output=True, text=True).stdout
if "hardened" not in text.lower():
    sys.exit(f"OCR did not find the text: {text!r}")
print("OCR:", text.strip())
`)
}
