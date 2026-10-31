package main

import (
	"testing"

	helpers "github.com/home-operations/containers/tests"
)

func Test(t *testing.T) {
	image := helpers.GetTestImage("ghcr.io/sebastka/zabbix-web-nginx:rolling")

	helpers.RequireCommandSucceeds(t, image, nil, "nginx", "-version")

	// The frontend's own files, not the base image's default page
	helpers.RequireFileExists(t, image, "/usr/share/zabbix/index.php")
	helpers.RequireFileExists(t, image, "/usr/share/zabbix/assets/styles/blue-theme.css")

	// nginx starts with no entrypoint of ours and answers with the placeholder. 503 rather than
	// 200 on purpose: an image with no site configuration mounted must not look healthy.
	helpers.RequireHTTPEndpoint(t, image, helpers.HTTPTestConfig{
		Port:       "8080",
		Path:       "/",
		StatusCode: 503,
	}, nil)
}
