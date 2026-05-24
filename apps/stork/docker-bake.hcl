target "docker-metadata-action" {}

variable "APP" {
  default = "stork"
}

variable "VERSION" {
  // renovate: datasource=github-tags depName=isc-projects/stork
  default = "2.4.0"
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
