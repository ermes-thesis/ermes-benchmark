package main

import (
	"empty_binary/common"
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"os"
)

func main() {
	fibonacci, err := os.ReadFile("./_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts_AOTwasmtime.wasm")
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
	pool := wasm.NewWasmtimeExecutorPool(10, false, log)
	defer pool.Close()

	executor := pool.Acquire()

	req, ctx := common.GetTestReqAndCtx("userId", common.FibonacciInput)
	_, _, _ = req, ctx, fibonacci
	executor.Release()
}
