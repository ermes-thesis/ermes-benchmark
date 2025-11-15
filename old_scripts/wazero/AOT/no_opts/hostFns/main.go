package main

import (
	"context"
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"github.com/tetratelabs/wazero/api"
	"os"
	"time"
	"wasm_integration_test/old_scripts/common"
)

func main() {
	hostFn, err := os.ReadFile("./_WASM_BINARIES/hostFns/functionCreateCollections.wasm")
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

	fns := map[string]any{
		"hostGet": func(ctx context.Context, m api.Module, collIdPtr, collIdLength, recordNamePtr, recordNameLength, groupsPtr, groupsLength, userIdPtr, userIdLength int32) int32 {
			return 0
		},
		"hostMultipleGet": func(ctx context.Context, m api.Module, collIdPtr, collIdLength, recordNamesPtr, recordNamesLength, groupsPtr, groupsLength, userIdPtr, userIdLength int32) int32 {
			return 0
		},
		"hostCreateCollection": func(ctx context.Context, m api.Module, metadataPointer, metadataLength, skipUniquenessCheck int32) int32 {
			return 0
		},
	}

	err = pool.RegisterHostFns(fns)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	req, ctx := common.GetTestReqAndCtx("userId", 0)
	pool.Invoke(hostFn, "entry", req, ctx)
}
