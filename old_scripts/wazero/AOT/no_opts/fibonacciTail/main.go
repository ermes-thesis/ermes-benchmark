package main

import (
	"context"
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"os"
	"wasm_integration_test/old_scripts/common"
)

func main() {
	tailFibonacci, err := os.ReadFile("./_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci.wasm")
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
	pool := wasm.NewWazeroExecutorPool(10, false, false, context.Background(), log)
	defer pool.Close()

	executor := pool.Acquire()

	req, ctx := common.GetTestReqAndCtx("userId", common.FibonacciTailInput)
	response := executor.Invoke(tailFibonacci, "entry", req, ctx)
	_ = response
	executor.Release()
}
