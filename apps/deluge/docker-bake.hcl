target "docker-metadata-action" {}

variable "APP" {
  default = "deluge"
}

variable "VERSION" {
  // Deluge from PyPI; requirements.in pins the same version and requirements.txt is compiled from
  // it (the build checks they agree). Updated in all three by .github/workflows/app-downloads.yaml:
  // Renovate cannot be trusted with the hashes in requirements.txt, see .renovaterc.json5
  default = "2.2.0"
}

variable "SOURCE" {
  default = "https://github.com/deluge-torrent/deluge"
}

variable "DESCRIPTION" {
  default = "Deluge on Docker Hardened Images, with libtorrent and its Python binding built from source"
}

variable "LICENSES" {
  // Deluge's LICENSE says "version 3"; its source headers say "3.0, or later". It adds a
  // special exception for linking against OpenSSL, which SPDX has no identifier for.
  default = "GPL-3.0-or-later"
}

group "default" {
  targets = ["image-local"]
}

target "image" {
  inherits = ["docker-metadata-action"]
  args = {
    VERSION = "${VERSION}"
  }
  labels = {
    "org.opencontainers.image.description" = "${DESCRIPTION}"
    "org.opencontainers.image.licenses" = "${LICENSES}"
    "org.opencontainers.image.source" = "${SOURCE}"
  }
}

target "image-local" {
  inherits = ["image"]
  output = ["type=docker"]
  tags = ["${APP}:${VERSION}"]
}

target "image-all" {
  inherits = ["image"]
  platforms = [
    "linux/amd64",
    "linux/arm64"
  ]
}
