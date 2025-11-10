package main

import (
	"empty_binary/old_scripts/common"
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"github.com/second-state/WasmEdge-go/wasmedge"
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
	pool := wasm.NewWasmedgeExecutorPool(10, log)

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

	executor := pool.Acquire()

	req, ctx := common.GetTestReqAndCtx("userId", 0)
	_, _, _ = req, ctx, hostFn
	executor.Release()
}
