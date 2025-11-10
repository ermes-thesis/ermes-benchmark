package wasm_integration_test

import (
	"context"
	"db"
	"metadataManager/propagation"
	datamanager_mock "mocks/dataManager"
	metadataManager_mock "mocks/metadataManager"
	"os"
	"scheduler"
	"server"

	"github.com/bytecodealliance/wasmtime-go/v37"
	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"github.com/second-state/WasmEdge-go/wasmedge"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
	"github.com/tetratelabs/wazero/api"

	"strconv"
	"testing"
	"time"
)

func createNewLogger(t testing.TB) logger.Logger {
	log, err := logger.NewLogger(logger.Config{
		Level:     zerolog.DebugLevel,
		Format:    "text",
		AddSource: false,
		Muted:     true,
	})
	require.NoError(t, err)
	return log
}

const primeNumsInput = 2000000
const fibonacciInput = 40
const lightweightInput = 20000
const fibonacciTailInput = 20000
const hostFnsInput = 0
const warmBench = false

var fnTwoParamOneReturnType = wasmedge.NewFunctionType(
	[]*wasmedge.ValType{wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32()},
	[]*wasmedge.ValType{wasmedge.NewValTypeI32()},
)
var fnFourParamOneReturnType = wasmedge.NewFunctionType(
	[]*wasmedge.ValType{wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32(), wasmedge.NewValTypeI32()},
	[]*wasmedge.ValType{wasmedge.NewValTypeI32()},
)
var wasmedgeFns = map[string]any{
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

var wasmtimeFns = map[string]any{
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

var wazeroFns = map[string]any{
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

func createHostFns(b *testing.B, log logger.Logger) *scheduler.HostFunctions {
	dataManager := datamanager_mock.NewDataManager(b)
	dataManager.EXPECT().SetCollectionAndPropagate(mock.Anything, "testCollection", map[string]db.RecordValue{}, []string{"groupA"}, "userId", false, false).Return(nil)
	dataManager.EXPECT().SetCollectionAndPropagate(mock.Anything, "seqCollection", map[string]db.RecordValue{}, []string{"groupA"}, "userId", true, false).Return(nil)
	metadataManager := metadataManager_mock.NewMetadataManager(b)
	metadataManager.
		EXPECT().
		CreateMetadata(mock.Anything, mock.AnythingOfType("Metadata"), propagation.FROM_LOCAL).
		Return(nil).
		Maybe()

	serverInfo := server.ServerInfo{
		HostName:                   "hostname",
		Address:                    "address",
		Port:                       "port",
		MetadataDomain:             "domain",
		Father:                     nil,
		Children:                   nil,
		Secret:                     "very secret",
		ClientSecret:               "client secret",
		CloudNode:                  nil,
		ExistingDomains:            map[string]struct{}{"IT": {}},
		GroupTokenProviderHostName: "hostnameGTP",
		Stateful:                   false,
		IsCentralStorage:           false,
	}
	return scheduler.NewHostFunctions(dataManager, metadataManager, &serverInfo, log)
}

func BenchmarkExecutionTime_Native_PrimeNumbers(b *testing.B) {
	// Compute intensive prime numbers computation function
	var computePrimes func(n int) int
	computePrimes = func(n int) int {
		count := 0
		for i := 2; i <= n; i++ {
			isPrime := true
			for j := 2; j*j <= i; j++ {
				if i%j == 0 {
					isPrime = false
					break
				}
			}
			if isPrime {
				count++
			}
		}
		return count
	}

	for b.Loop() {
		computePrimes(primeNumsInput)
	}
}

func BenchmarkExecutionTime_Native_Fibonacci(b *testing.B) {
	for b.Loop() {
		// Compute intensive fibonacci function
		var fibFun func(n int) int
		fibFun = func(n int) int {
			if n <= 1 {
				return n
			}
			return fibFun(n-1) + fibFun(n-2)
		}
		fibFun(fibonacciInput)
	}
}

func BenchmarkExecutionTime_Native_Lightweight(b *testing.B) {
	// Lightweight computation function
	var result int

	for b.Loop() {
		count := 0
		for i := 0; i <= lightweightInput; i++ {
			count++
		}
		result = count
	}

	if result == 0 {
		b.Fatalf("unexpected zero result")
	}
}

// 124856503	        96.77 ns/op
func BenchmarkExecutionTime_Native_TailFibonacci(b *testing.B) {
	var result int
	// Compute intensive fibonacci function
	var fibTailFun func(n, a, b int) int
	fibTailFun = func(n, a, b int) int {
		if n == 0 {
			return a
		}
		return fibTailFun(n-1, b, a+b)
	}

	for b.Loop() {
		result = fibTailFun(fibonacciTailInput, 0, 1)
	}

	if result == 0 {
		b.Fatalf("unexpected zero result")
	}
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_NoOpts_PrimeNumbers(b *testing.B) {
	primeNums, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNums, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_NoOpts_Fibonacci(b *testing.B) {
	fibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_NoOpts_Lightweight(b *testing.B) {
	lightweight, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweight, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_NoOpts_TailFibonacci(b *testing.B) {
	tailFibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_NoOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFns, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, log)
	err = createHostFns(b, log).RegisterWasmedgeHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFns, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_WithOpts_PrimeNumbers(b *testing.B) {
	primeNumsWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_WithOpts_Fibonacci(b *testing.B) {
	fibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_WithOpts_Lightweight(b *testing.B) {
	lightweightWOpts, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	executor := pool.Acquire()
	req, ctx := getTestReqAndCtx("userId", lightweightInput)

	for b.Loop() {
		response := executor.Invoke(lightweightWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
	}
	executor.Release()
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_WithOpts_TailFibonacci(b *testing.B) {
	tailFibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_Interpreter_WithOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFnsWOpts, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, log)
	err = createHostFns(b, log).RegisterWasmedgeHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_NoOpts_PrimeNumbers(b *testing.B) {
	primeNumsAOT, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums_noOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_NoOpts_Fibonacci(b *testing.B) {
	fibonacciAOT, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_noOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_NoOpts_Lightweight(b *testing.B) {
	lightweightAOT, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight_noOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_NoOpts_TailFibonacci(b *testing.B) {
	tailFibonacciAOT, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_noOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_NoOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFnsAOT, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections_noOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, log)
	err = createHostFns(b, log).RegisterWasmedgeHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_WithOpts_PrimeNumbers(b *testing.B) {
	primeNumsWOptsAOT, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums_wOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOptsAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_WithOpts_Fibonacci(b *testing.B) {
	fibonacciWOptsAOT, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOptsAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_WithOpts_Lightweight(b *testing.B) {
	lightweightWOptsAOT, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight_wOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightWOptsAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_WithOpts_TailFibonacci(b *testing.B) {
	tailFibonacciWOptsAOT, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOptsAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmedge_AOT_WithOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFnsWOptsAOT, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections_wOpts_AOTwasmedge.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmedgeExecutorPool(10, createNewLogger(b))
	err = createHostFns(b, log).RegisterWasmedgeHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOptsAOT, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_NoOpts_PrimeNumbers(b *testing.B) {
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}
	primeNums, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNums, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNums, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_NoOpts_Fibonacci(b *testing.B) {
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}

	fibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_NoOpts_Lightweight(b *testing.B) {
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}

	lightweight, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweight, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweight, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_NoOpts_TailFibonacci(b *testing.B) {
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}

	tailFibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_NoOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}

	hostFns, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, log)
	err = createHostFns(b, log).RegisterWasmtimeHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFns, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFns, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_WithOpts_PrimeNumbers(b *testing.B) {
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}

	primeNumsWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_WithOpts_Fibonacci(b *testing.B) {
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}

	fibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_WithOpts_Lightweight(b *testing.B) {
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}

	lightweightWOpts, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_WithOpts_TailFibonacci(b *testing.B) {
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}

	tailFibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_JIT_WithOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	homeFolder := os.Getenv("HOME")
	err := os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	if err != nil {
		panic(err)
	}

	hostFnsWOpts, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, false, log)
	err = createHostFns(b, log).RegisterWasmtimeHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

// For Wasmtime AOT the cache is not used anyway
func BenchmarkExecutionTime_Wasmtime_AOT_NoOpts_PrimeNumbers(b *testing.B) {
	primeNums, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums_noOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNums, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNums, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_AOT_NoOpts_Fibonacci(b *testing.B) {
	fibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_noOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_AOT_NoOpts_Lightweight(b *testing.B) {
	lightweight, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight_noOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweight, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweight, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_AOT_NoOpts_TailFibonacci(b *testing.B) {
	tailFibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_noOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_AOT_NoOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFns, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections_noOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, log)
	err = createHostFns(b, log).RegisterWasmtimeHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFns, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFns, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_AOT_WithOpts_PrimeNumbers(b *testing.B) {
	primeNumsWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums_wOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_AOT_WithOpts_Fibonacci(b *testing.B) {
	fibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_AOT_WithOpts_Lightweight(b *testing.B) {
	lightweightWOpts, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight_wOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_AOT_WithOpts_TailFibonacci(b *testing.B) {
	tailFibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wasmtime_AOT_WithOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFnsWOpts, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections_wOpts_AOTwasmtime.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWasmtimeExecutorPool(10, warmBench, true, log)
	err = createHostFns(b, log).RegisterWasmtimeHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_NoOpts_PrimeNumbers(b *testing.B) {
	primeNums, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNums, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNums, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_NoOpts_Fibonacci(b *testing.B) {
	fibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_NoOpts_Lightweight(b *testing.B) {
	lightweight, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweight, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweight, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_NoOpts_TailFibonacci(b *testing.B) {
	tailFibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_NoOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFns, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), log)
	err = createHostFns(b, log).RegisterWazeroHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFns, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFns, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_WithOpts_PrimeNumbers(b *testing.B) {
	primeNumsWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_WithOpts_Fibonacci(b *testing.B) {
	fibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_WithOpts_Lightweight(b *testing.B) {
	lightweightWOpts, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_WithOpts_TailFibonacci(b *testing.B) {
	tailFibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_AOT_WithOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFnsWOpts, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections_wOpts.wasm")
	if err != nil {
		panic(err)
	}
	pool := wasm.NewWazeroExecutorPool(10, false, warmBench, context.Background(), log)
	err = createHostFns(b, log).RegisterWazeroHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_WithOpts_PrimeNumbers(b *testing.B) {
	primeNumsWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums_wOpts.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNumsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_WithOpts_Fibonacci(b *testing.B) {
	fibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_WithOpts_Lightweight(b *testing.B) {
	lightweightWOpts, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight_wOpts.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweightWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_WithOpts_TailFibonacci(b *testing.B) {
	tailFibonacciWOpts, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacciWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_WithOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFnsWOpts, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), log)
	err = createHostFns(b, log).RegisterWazeroHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFnsWOpts, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_NoOpts_PrimeNumbers(b *testing.B) {
	primeNums, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNums, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", primeNumsInput)
		response := executor.Invoke(primeNums, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_NoOpts_Fibonacci(b *testing.B) {
	fibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciInput)
		response := executor.Invoke(fibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_NoOpts_Lightweight(b *testing.B) {
	lightweight, err := os.ReadFile("_WASM_BINARIES/lightweight/lightweight.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweight, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", lightweightInput)
		response := executor.Invoke(lightweight, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_NoOpts_TailFibonacci(b *testing.B) {
	tailFibonacci, err := os.ReadFile("_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), createNewLogger(b))
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", fibonacciTailInput)
		response := executor.Invoke(tailFibonacci, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func BenchmarkExecutionTime_Wazero_Interpreter_NoOpts_HostFns(b *testing.B) {
	log := createNewLogger(b)
	hostFns, err := os.ReadFile("_WASM_BINARIES/hostFns/functionCreateCollections.wasm")
	if err != nil {
		panic(err)
	}

	pool := wasm.NewWazeroExecutorPool(10, true, warmBench, context.Background(), log)
	err = createHostFns(b, log).RegisterWazeroHostFns(pool)
	if err != nil {
		panic(err)
	}
	defer pool.Close()

	// Execute the first time to allow to start the b.Loop() with a cached compiled binary
	if warmBench {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFns, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}

	for b.Loop() {
		executor := pool.Acquire()

		req, ctx := getTestReqAndCtx("userId", hostFnsInput)
		response := executor.Invoke(hostFns, "entry", req, ctx)

		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
		executor.Release()
	}
}

func getTestReqAndCtx(userId string, inputN int) ([]byte, []byte) {
	req := "{\"prova\": \"ciao\", \"n\":\"" + strconv.FormatInt(int64(inputN), 10) + "\"}"

	timestamp, _ := time.Now().MarshalJSON()
	ctx := "{" +
		"\"userId\": \"" + userId + "\"," +
		"\"groupList\": [\"test\"]," +
		"\"collections\": {" +
		"\"test_collection\": [" +
		"{" +
		"\"Id\": \"255ef4af-3a49-4382-a90d-6524bdee5ad1\"," +
		"\"Metadata\": {" +
		"\"consistency\": 1," +
		"\"name\": \"dati\"," +
		"\"owner\": \"pippo\"," +
		"\"createdAt\": " + string(timestamp) + "" +
		"}" +
		"}" +
		"]" +
		"}" +
		"}"
	return []byte(req), []byte(ctx)
}
