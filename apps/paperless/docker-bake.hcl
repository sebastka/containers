target "docker-metadata-action" {}

variable "APP" {
  default = "paperless"
}

variable "VERSION" {
  // The paperless-ngx release. Updated with PAPERLESS_SHA256 in the Dockerfile by
  // .github/workflows/app-downloads.yaml: Renovate could not update the checksum
  default = "3.4.1"
}

variable "SOURCE" {
  default = "https://github.com/paperless-ngx/paperless-ngx"
}

variable "DESCRIPTION" {
  default = "paperless-ngx on Docker Hardened Images, without s6: one process per container"
}

variable "LICENSES" {
  // Upstream ships the plain GPLv3 text with no "or any later version" statement of its
  // own, so the narrower identifier is the accurate one.
  default = "GPL-3.0-only"
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
