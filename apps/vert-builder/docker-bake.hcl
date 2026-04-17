target "docker-metadata-action" {}

variable "APP" {
  default = "vert-builder"
}

variable "VERSION" {
  // renovate: datasource=custom.vert-builder depName=vert-builder
  default = formatdate("YYYY-MM-DD", timestamp())
}

variable "SOURCE" {
  default = "https://github.com/VERT-sh/VERT"
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
