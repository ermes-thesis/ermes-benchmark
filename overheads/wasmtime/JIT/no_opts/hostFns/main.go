package main

import (
	"empty_binary/common"
	"github.com/bytecodealliance/wasmtime-go/v37"
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"os"
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
	pool := wasm.NewWasmtimeExecutorPool(10, false, log)

	fns := map[string]any{
		"hostGet": func(collIdPtr, collIdLength, recordNamePtr, recordNameLength, groupsPtr, groupsLength, userIdPtr, userIdLength int32, caller *wasmtime.Caller) int32 {
			return 0
		},
		"hostMultipleGet": func(collIdPtr, collIdLength, recordNamesPtr, recordNamesLength, groupsPtr, groupsLength, userIdPtr, userIdLength int32, caller *wasmtime.Caller) int32 {
			return 0
		},
		"hostCreateCollection": func(metadataPointer, metadataLength, skipUniquenessCheck int32, caller *wasmtime.Caller) int32 {
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
	_, _, _ = req, ctx, hostFn
	executor.Release()
}
