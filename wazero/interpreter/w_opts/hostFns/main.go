package main

import (
	"context"
	"empty_binary/common"
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"github.com/tetratelabs/wazero/api"
	"os"
)

func main() {
	hostFn, err := os.ReadFile("./_WASM_BINARIES/hostFns/functionCreateCollections_wOpts.wasm")
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

	executor := pool.Acquire()

	req, ctx := common.GetTestReqAndCtx("userId", 0)
	executor.Invoke(hostFn, "entry", req, ctx)
	executor.Release()
}
