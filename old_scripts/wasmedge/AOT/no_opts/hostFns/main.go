package main

import (
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"github.com/second-state/WasmEdge-go/wasmedge"
	"os"
	"time"
	"wasm_integration_test/old_scripts/common"
)

func main() {
	hostFn, err := os.ReadFile("./_WASM_BINARIES/hostFns/functionCreateCollections_noOpts_AOTwasmedge.wasm")
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
	pool := wasm.NewWasmedgeExecutorPool(wasm.Config{
		PoolSize:  10,
		Timeout:   5 * time.Second,
		WithCache: false,
		IsAot:     false,
	}, log)

	fnTwoParamOneReturnType := wasmedge.NewFunctionType(
		[]*wasmedge.ValType{wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32()},
		[]*wasmedge.ValType{wasmedge.NewValTypeI32()},
	)
	fnFourParamOneReturnType := wasmedge.NewFunctionType(
		[]*wasmedge.ValType{wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32()},
		[]*wasmedge.ValType{wasmedge.NewValTypeI32()},
	)
	fns := map[string]any{
		"hostGet": wasmedge.NewFunction(fnFourParamOneReturnType, func(data any, callframe *wasmedge.CallingFrame, params []any) ([]any, wasmedge.Result) {
			return []any{1}, wasmedge.Result_Success
		}, nil, 0),
		"hostMultipleGet": wasmedge.NewFunction(fnFourParamOneReturnType, func(data any, callframe *wasmedge.CallingFrame, params []any) ([]any, wasmedge.Result) {
			return []any{1}, wasmedge.Result_Success
		}, nil, 0),
		"hostCreateCollection": wasmedge.NewFunction(fnTwoParamOneReturnType, func(data any, callframe *wasmedge.CallingFrame, params []any) ([]any, wasmedge.Result) {
			return []any{1}, wasmedge.Result_Success
		}, nil, 0),
	}
	err = pool.RegisterHostFns(fns)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	req, ctx := common.GetTestReqAndCtx("userId", 0)
	pool.Invoke(hostFn, "entry", req, ctx)
}
