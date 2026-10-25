target "docker-metadata-action" {}

variable "APP" {
  default = "element-admin"
}

variable "COMMIT" {
  // renovate: datasource=git-refs depName=https://github.com/element-hq/element-admin branch=main
  default = "5feeaf904c9727f4eac477db0edfc215eb53461b"
}

variable "VERSION" {
  default = formatdate("YYYY.M.D", timestamp())
}

variable "SOURCE" {
  default = "https://github.com/element-hq/element-admin"
}

variable "DESCRIPTION" {
  default = "Element Admin, the administration interface for a Matrix homeserver"
}

variable "LICENSES" {
  // Upstream declares "AGPL-3.0-only OR LicenseRef-Element-Commercial". No commercial
  // agreement is involved here, so this image is distributed under the AGPL arm.
  default = "AGPL-3.0-only"
}

group "default" {
  targets = ["image-local"]
}

target "image" {
  inherits = ["docker-metadata-action"]
  // Upstream's tree as a named context, so the Dockerfile beside this file can build it: the
  // default context stays local, which is where assets/entrypoint.sh comes from
  contexts = {
    src = "https://github.com/element-hq/element-admin.git#${COMMIT}"
  }
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
