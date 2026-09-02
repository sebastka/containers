target "docker-metadata-action" {}

variable "APP" {
  default = "stork"
}

variable "VERSION" {
  // Tracks the Alpine packages ISC publishes to Cloudsmith, not the git tags:
  // tags run ahead of the packages, and a version with no package cannot build.
  // renovate: datasource=custom.stork depName=isc-stork-server
  default = "2.4.1"
}

variable "SOURCE" {
  default = "https://github.com/isc-projects/stork"
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
