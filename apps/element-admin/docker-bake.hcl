target "docker-metadata-action" {}

variable "APP" {
  default = "element-admin"
}

variable "COMMIT" {
  // renovate: datasource=git-refs depName=https://github.com/element-hq/element-admin branch=main
  default = "20cc4abc811c154111305b41ec6ab60845b5ea4a"
}

variable "VERSION" {
  default = formatdate("YYYY.M.D", timestamp())
}

variable "SOURCE" {
  default = "https://github.com/element-hq/element-admin"
}

group "default" {
  targets = ["image-local"]
}

target "image" {
  inherits = ["docker-metadata-action"]
  context   = "https://github.com/element-hq/element-admin.git#${COMMIT}"
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
