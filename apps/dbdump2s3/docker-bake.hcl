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

variable "DESCRIPTION" {
  default = "Logical backups of PostgreSQL and MariaDB, encrypted to an age or PGP recipient and uploaded to S3"
}

variable "LICENSES" {
  // The script in this repository. The Alpine packages it ships -- gnupg, the database
  // clients, aws-cli -- keep their own licences, as any base image's contents do.
  default = "MIT"
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
