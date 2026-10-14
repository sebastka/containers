# paperless-ngx

[paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) on
[Docker Hardened Images](https://hub.docker.com/hardened-images/catalog/dhi/python), Debian 13
(trixie) as upstream: built in `dhi.io/python:3.14-debian13-dev`, run on `dhi.io/python:3.14-debian13`
(no shell, no package manager, user 65532). Replaces `ghcr.io/paperless-ngx/paperless-ngx` without
its s6 supervision: each container runs its own command, as the homelab manifests already do.
About 1.4 GB uncompressed, against 2.5 GB for upstream's image.

## Contents

- **paperless**, from the release tarball (backend, prebuilt frontend, collected static files,
  compiled translations; pinned by sha256), under `/usr/src/paperless` as upstream. The tarball
  ships the frontend twice (in `src/` and collected in `static/`), so identical files are
  hard-linked (`scripts/deduplicate.py`, about 580 MB): upstream's image avoids the copies with
  `collectstatic --link`, this only matches it. The size difference with upstream comes from what
  is left out (below), PyTorch above all.
- **Python packages**, in a virtualenv at `/opt/paperless` (on `PATH`: `granian`, `celery`), from
  the release's hash-locked `requirements.txt` with the `postgres` and `webserver` extras
  (`scripts/requirements.py`). **Left out**: PyTorch, sentence-transformers and the local
  HuggingFace embedding backend, several hundred MB that only `PAPERLESS_AI_LLM_EMBEDDING_BACKEND=huggingface`
  uses (paperless imports it only then; openai-like and ollama work), and MariaDB's client library.
- **libpq 18** from PostgreSQL's apt repository (key checked by fingerprint): paperless's prebuilt
  `psycopg-c` wheel needs it. With Debian's 17, upstream's image silently falls back to psycopg's
  pure-Python implementation; here it uses the C one.
- **What paperless and OCRmyPDF run**: Tesseract (English and orientation detection; other
  languages through `paperless-tessdata`), Ghostscript, ImageMagick 7 (with upstream's policy:
  resource limits, PDF allowed, SVG/MVG/PostScript and URL delegates refused), poppler-utils, qpdf,
  unpaper, pngquant, jbig2dec, libmagic, gpg, Liberation fonts. Installed with apt in the build
  image, then copied with their dependencies, minus what the runtime image has
  (`scripts/stage-packages.py`), with their dpkg status entries for scanners.
- **jbig2enc**, built from its author's release (`agl/jbig2enc`), for OCRmyPDF's lossless JBIG2.

## Commands

- `paperless-tessdata`: for an init container sharing a volume with paperless. Copies the image's
  Tesseract data to `$TESSDATA_PREFIX` and downloads each language in `$PAPERLESS_OCR_LANGUAGES`
  (`nor deu+fra`) from tesseract-ocr/tessdata at `$TESSDATA_REF` (default `4.1.0`); languages
  already there are kept.
- `paperless-wait-for-db`: waits for PostgreSQL with psycopg (`pg_isready`'s job, without the
  PostgreSQL client), from the `PAPERLESS_DB*` variables.
- `wait-for-redis.py`: upstream's.
- The default command serves the web UI with granian; the worker, scheduler and consumer run
  `celery --app paperless worker|beat` and `python3 manage.py document_consumer`.

## Updating

`.github/workflows/app-downloads.yaml` runs `scripts/update-downloads.py` every Monday (or by
hand, Actions > App Downloads) and opens a pull request for a new paperless release (`VERSION` in
`docker-bake.hcl` with `PAPERLESS_SHA256`) or jbig2enc release, checksums included. Base images:
Renovate.

`container_test.go` checks every program above, the compiled Python modules (psycopg's C
implementation, sqlite-vec, zxing-cpp, libmagic), Django's system checks, and a real OCR run:
text rendered into a PDF, OCRmyPDF over it (Tesseract, Ghostscript, PDF/A), read back.
