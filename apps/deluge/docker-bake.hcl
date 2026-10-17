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

group "default" {
  targets = ["image-local"]
}

target "image" {
  inherits = ["docker-metadata-action"]
  args = {
    VERSION = "${VERSION}"
  }
  labels = {
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
