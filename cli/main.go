package main

import (
	"os"

	"github.com/projanvil/belt/cmd"
)

func main() {
	if err := cmd.Execute(); err != nil {
		os.Exit(1)
	}
}
