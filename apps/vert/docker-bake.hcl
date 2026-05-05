target "docker-metadata-action" {}

variable "APP" {
  default = "vert"
}

variable "VERSION" {
  default = formatdate("YYYY.M.D", timestamp())
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
    PUB_ENV = "production"
    PUB_HOSTNAME = "vert.karlsen.app"
    PUB_PLAUSIBLE_URL = ""
    // PUB_VERTD_URL = "https://vertd.karlsen.app"
    PUB_VERTD_URL = "https://vertd.vert.sh"
    PUB_DISABLE_ALL_EXTERNAL_REQUESTS = true
    PUB_DONATION_URL = "https://donations.vert.sh"
    PUB_STRIPE_KEY = "pk_live_51RDVmAGSxPVad6bQwzVNnbc28nlmzA30krLWk1fefCMpUPiSRPkavMMbGqa8A3lUaOCMlsUEVy2CWDYg0ip3aPpL00ZJlsMkf2"
    PUB_DISABLE_FAILURE_BLOCKS = false
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
