target "docker-metadata-action" {}

variable "APP" {
  default = "jq"
}

variable "VERSION" {
  // renovate: datasource=custom.jq depName=jq
  default = formatdate("YYYY.M.D", timestamp())
}

variable "SOURCE" {
  default = "https://github.com/jqlang/jq"
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
