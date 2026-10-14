target "docker-metadata-action" {}

variable "APP" {
  default = "paperless"
}

variable "VERSION" {
  // The paperless-ngx release. Updated with PAPERLESS_SHA256 in the Dockerfile by
  // .github/workflows/app-downloads.yaml: Renovate could not update the checksum
  default = "3.3.1"
}

variable "SOURCE" {
  default = "https://github.com/paperless-ngx/paperless-ngx"
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
