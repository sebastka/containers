target "docker-metadata-action" {}

variable "APP" {
  default = "dbdump2s3"
}

variable "VERSION" {
  // First-party: there is no upstream release to track, so the date of the build is the version.
  // The weekly rebuild in .github/workflows/release.yaml is what rolls it, which is also what
  // pulls patched Alpine packages in behind the pinned base digest.
  default = formatdate("YYYY.M.D", timestamp())
}

variable "SOURCE" {
  default = "https://github.com/sebastka/containers"
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
