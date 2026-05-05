package main

import (
	"context"
	"testing"

	"github.com/home-operations/containers/testhelpers"
)

func Test(t *testing.T) {
	ctx := context.Background()
	image := testhelpers.GetTestImage("ghcr.io/sebastka/element-admin:rolling")
	testhelpers.TestCommandSucceeds(t, ctx, image, nil, "nginx", "-version")
}
