package main

import (
	"testing"

	helpers "github.com/home-operations/containers/tests"
)

func Test(t *testing.T) {
	image := helpers.GetTestImage("ghcr.io/sebastka/element-admin:rolling")

	helpers.RequireCommandSucceeds(t, image, nil, "nginx", "-version")

	// Upstream's build output, not the base image's default page: nginx ships one of those at
	// /usr/share/nginx/html whether or not anything was built here
	helpers.RequireFileExists(t, image, "/dist/index.html")

	// The snippets a deployment's server block can include
	helpers.RequireFileExists(t, image, "/etc/nginx/security_headers.conf")
	helpers.RequireFileExists(t, image, "/etc/nginx/conf.d/http_customisations.conf")

	// nginx starts on its own, with no entrypoint of ours, and answers with the placeholder. 503
	// rather than 200 on purpose: an image with no site configuration mounted must not look
	// healthy to a probe.
	helpers.RequireHTTPEndpoint(t, image, helpers.HTTPTestConfig{
		Port:       "8080",
		Path:       "/",
		StatusCode: 503,
	}, nil)
}
