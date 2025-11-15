package main

import (
	"context"
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"os"
	"time"
	"wasm_integration_test/old_scripts/common"
)

func main() {
	lightweight, err := os.ReadFile("./_WASM_BINARIES/lightweight/lightweight.wasm")
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
	pool := wasm.NewWazeroExecutorPool(wasm.Config{
		PoolSize:  10,
		Timeout:   5 * time.Second,
		WithCache: false,
		IsAot:     true,
	}, context.Background(), log)
	defer pool.Close()

	req, ctx := common.GetTestReqAndCtx("userId", common.LightweightInput)
	response := pool.Invoke(lightweight, "entry", req, ctx)
	_ = response
}
