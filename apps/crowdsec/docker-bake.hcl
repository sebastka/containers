target "docker-metadata-action" {}

variable "APP" {
  default = "crowdsec"
}

variable "VERSION" {
  default = "v1.7.8" // renovate: datasource=docker depName=docker.io/crowdsecurity/crowdsec
}

variable "SOURCE" {
  default = "https://github.com/crowdsecurity/crowdsec"
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
