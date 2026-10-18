target "docker-metadata-action" {}

variable "APP" {
  default = "debian-debug"
}

variable "VERSION" {
  default = formatdate("YYYY.M.D", timestamp())
}

variable "SOURCE" {
  default = "https://github.com/docker-library/official-images"
}

variable "DESCRIPTION" {
  default = "Debian with networking, database and troubleshooting tools, to debug from inside a cluster"
}

variable "LICENSES" {
  // The Dockerfile in this repository. Everything it installs is Debian's, under the many
  // licences those packages carry.
  default = "MIT"
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
