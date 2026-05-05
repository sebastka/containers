target "docker-metadata-action" {}

variable "APP" {
  default = "element-admin"
}

variable "VERSION" {
  // renovate: datasource=github-releases depName=element-hq/element-admin
  default = "v0.1.11"
}

variable "SOURCE" {
  default = "https://github.com/element-hq/element-admin"
}

group "default" {
  targets = ["image-local"]
}

target "image" {
  inherits = ["docker-metadata-action"]
  context   = "https://github.com/element-hq/element-admin.git#${VERSION}"
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
