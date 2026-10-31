target "docker-metadata-action" {}

variable "APP" {
  default = "zabbix-server"
}

variable "VERSION" {
  // The Zabbix source release. Updated with ZABBIX_SHA256 in the Dockerfile by
  // .github/workflows/app-downloads.yaml: Renovate has no datasource that yields the checksum
  default = "7.4.16"
}

variable "SOURCE" {
  default = "https://github.com/zabbix/zabbix"
}

variable "DESCRIPTION" {
  default = "Zabbix server for PostgreSQL, one process per container"
}

variable "LICENSES" {
  // Zabbix moved to AGPL-3.0-only with 7.0; earlier releases were GPL-2.0-or-later
  default = "AGPL-3.0-only"
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
