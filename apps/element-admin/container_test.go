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

	// Upstream draws its logo in a React component and ships no icon file, so this one is built
	// from that component (see README.md). Browsers request it unprompted, so it is served from
	// /dist like any other asset. The header is checked rather than just the name: a rasteriser
	// that silently produced nothing would otherwise still leave a file here.
	helpers.RequireFileExists(t, image, "/dist/favicon.ico")
	helpers.RequireCommandSucceeds(t, image, nil, "sh", "-c",
		`set -e
		# ICONDIR: reserved, type 1 for an icon, then the number of images in it
		bytes=$(head -c 6 /dist/favicon.ico | od -An -t u1 | tr -s " " | sed "s/^ //;s/ $//")
		[ "$bytes" = "0 0 1 0 3 0" ] || { echo "not an ICO holding three sizes: $bytes"; exit 1; }`)

	// nginx starts on its own, with no entrypoint of ours, and answers with the placeholder. 503
	// rather than 200 on purpose: an image with no site configuration mounted must not look
	// healthy to a probe.
	helpers.RequireHTTPEndpoint(t, image, helpers.HTTPTestConfig{
		Port:       "8080",
		Path:       "/",
		StatusCode: 503,
	}, nil)
}
