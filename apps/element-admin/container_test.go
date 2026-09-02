package main

import (
	"testing"

	helpers "github.com/home-operations/containers/tests"
)

func Test(t *testing.T) {
	image := helpers.GetTestImage("ghcr.io/sebastka/element-admin:rolling")
	helpers.RequireCommandSucceeds(t, image, nil, "nginx", "-version")
}
