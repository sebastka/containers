package main

import (
	"testing"

	helpers "github.com/home-operations/containers/tests"
)

func Test(t *testing.T) {
	image := helpers.GetTestImage("ghcr.io/sebastka/jq:rolling")
	helpers.RequireCommandSucceeds(t, image, nil, "jq", "--help")
}
