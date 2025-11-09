package main

import (
	"context"
	"empty_binary/common"
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"os"
)

func main() {
	fibonacci, err := os.ReadFile("./_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	log, err := logger.NewLogger(logger.Config{
		Level:         zerolog.FatalLevel,
		Format:        "text",
		Output:        nil,
		StdoutEnabled: false,
		AddSource:     false,
		Colored:       false,
		Rolling:       false,
		Muted:         true,
	})
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, true, false, context.Background(), log)
	defer pool.Close()

	executor := pool.Acquire()

	req, ctx := common.GetTestReqAndCtx("userId", common.FibonacciInput)
	response := executor.Invoke(fibonacci, "entry", req, ctx)
	_ = response
	executor.Release()
}
