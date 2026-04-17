package main

import (
	"context"
	"testing"

	"github.com/home-operations/containers/testhelpers"
)

func Test(t *testing.T) {
	ctx := context.Background()
	image := testhelpers.GetTestImage("ghcr.io/sebastka/stork:rolling")
	testhelpers.TestCommandSucceeds(t, ctx, image, nil, "/stork-server", "--version")
}
