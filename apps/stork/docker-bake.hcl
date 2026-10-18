target "docker-metadata-action" {}

variable "APP" {
  default = "stork"
}

variable "VERSION" {
  // Tracks the Alpine packages ISC publishes to Cloudsmith, not the git tags:
  // tags run ahead of the packages, and a version with no package cannot build.
  // renovate: datasource=custom.stork depName=isc-stork-server
  default = "2.6.0"
}

variable "SOURCE" {
  default = "https://github.com/isc-projects/stork"
}

variable "DESCRIPTION" {
  default = "ISC Stork server, the monitoring dashboard for Kea DHCP and BIND 9"
}

variable "LICENSES" {
  default = "MPL-2.0"
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
