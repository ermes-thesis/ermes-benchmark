package wasm_benchmark

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/stretchr/testify/require"
)

// --- Constants & Enums ---

const (
	primeNumsInput     = 2000000
	fibonacciInput     = 40
	lightweightInput   = 20000
	fibonacciTailInput = 20000
	hostFnsInput       = 0
)

type Runtime string

const (
	RuntimeWasmedge Runtime = "Wasmedge"
	RuntimeWasmtime Runtime = "Wasmtime"
	RuntimeWazero   Runtime = "Wazero"
)

type Workload string

const (
	WorkloadPrime    Workload = "PrimeNumbers"
	WorkloadFib      Workload = "Fibonacci"
	WorkloadLight    Workload = "Lightweight"
	WorkloadTailFib  Workload = "TailFibonacci"
	WorkloadStateful Workload = "Stateful"
)

// BenchConfig centralizes the configuration for a single benchmark run
type BenchConfig struct {
	Runtime     Runtime
	Workload    Workload
	Input       int
	WithOpts    bool
	IsAOT       bool
	Cache       wasm.CacheType
	AddTestColl bool
}

// --- Helper Functions ---

func createNewLogger(t testing.TB) logger.Logger {
	log, err := logger.NewLogger(logger.Config{
		Level:     logger.WarnLevel,
		Format:    "text",
		AddSource: false,
		Muted:     true,
	})
	require.NoError(t, err)
	return log
}

func getTestReqAndCtxWithTestCol(userId string, addTestColl bool, inputN int) ([]byte, []byte) {
	req := "{\"prova\": \"ciao\", \"n\":\"" + strconv.FormatInt(int64(inputN), 10) + "\"}"

	var testColl string
	if addTestColl {
		timestamp, _ := time.Now().MarshalJSON()
		testColl = "\"test_collection\": [" +
			"{" +
			"\"Id\": \"255ef4af-3a49-4382-a90d-6524bdee5ad1\"," +
			"\"Metadata\": {" +
			"\"consistency\": 1," +
			"\"name\": \"dati\"," +
			"\"owner\": \"pippo\"," +
			"\"createdAt\": " + string(timestamp) + "" +
			"}" +
			"}" +
			"]"
	}

	ctx := "{" +
		"\"userId\": \"" + userId + "\"," +
		"\"groupList\": [\"test\"]," +
		"\"collections\": {" +
		testColl +
		"}" +
		"}"
	return []byte(req), []byte(ctx)
}

// getWasmFilePath constructs the path based on configuration
func getWasmFilePath(cfg BenchConfig) string {
	baseDir := "_WASM_BINARIES/"
	var folder, name string

	switch cfg.Workload {
	case WorkloadPrime:
		folder = "cpuIntensive/primeNums/"
		name = "primeNums"
	case WorkloadFib:
		folder = "cpuIntensive/fibonacci/"
		name = "fibonacci"
	case WorkloadTailFib:
		folder = "cpuIntensive/tailFibonacci/"
		name = "tailFibonacci"
	case WorkloadLight:
		folder = "lightweight/"
		name = "lightweight"
	case WorkloadStateful:
		folder = "stateful/"
		name = "statefulFunction"
	}

	suffix := ""
	if cfg.IsAOT && cfg.Runtime != RuntimeWazero {
		optsPart := "noOpts"
		if cfg.WithOpts {
			optsPart = "wOpts"
		}
		runtimePart := strings.ToLower(string(cfg.Runtime))
		suffix = fmt.Sprintf("_%s_AOT%s.wasm", optsPart, runtimePart)
	} else {
		if cfg.WithOpts {
			suffix = "_wOpts.wasm"
		} else {
			suffix = ".wasm"
		}
	}
	return baseDir + folder + name + suffix
}

// runWasmBenchmark is the low-level driver for a SINGLE benchmark run
func runWasmBenchmark(b *testing.B, cfg BenchConfig) {
	log := createNewLogger(b)

	// Special Cleanup for Wasmtime Cold Start
	if cfg.Runtime == RuntimeWasmtime && cfg.Cache == wasm.CacheNone {
		homeFolder := os.Getenv("HOME")
		_ = os.RemoveAll(homeFolder + "/.cache/wasmtime/modules")
	}

	path := getWasmFilePath(cfg)
	binary, err := os.ReadFile(path)
	if err != nil {
		b.Fatalf("failed to read wasm file at %s: %v", path, err)
	}

	var pool wasm.ExecutorPool
	poolConfig := wasm.Config{
		PoolSize:  10,
		Timeout:   5 * time.Second,
		WithCache: cfg.Cache,
		CacheSize: 2,
		IsAot:     cfg.IsAOT,
	}

	switch cfg.Runtime {
	case RuntimeWasmedge:
		pool = wasm.NewWasmedgeExecutorPool(poolConfig, log)
	case RuntimeWasmtime:
		pool = wasm.NewWasmtimeExecutorPool(poolConfig, log)
	case RuntimeWazero:
		pool = wasm.NewWazeroExecutorPool(poolConfig, context.Background(), log)
	default:
		b.Fatalf("unknown runtime: %s", cfg.Runtime)
	}
	defer pool.Close()

	if cfg.Workload == WorkloadStateful {
		hostFns := createHostFns(b, log)
		var err error
		switch cfg.Runtime {
		case RuntimeWasmedge:
			err = hostFns.RegisterWasmedgeHostFns(pool.(*wasm.WasmedgeExecutorPool))
		case RuntimeWasmtime:
			err = hostFns.RegisterWasmtimeHostFns(pool.(*wasm.WasmtimeExecutorPool))
		case RuntimeWazero:
			err = hostFns.RegisterWazeroHostFns(pool.(*wasm.WazeroExecutorPool))
		}
		if err != nil {
			b.Fatalf("failed to register host functions: %v", err)
		}
	}

	userId := "userId"
	req, ctx := getTestReqAndCtxWithTestCol(userId, cfg.AddTestColl, cfg.Input)

	// Warmup / First execution logic
	if cfg.Cache != wasm.CacheNone {
		// For warm benchmarks, ensure cache is populated
		resp := pool.Invoke("fun", binary, "entry", req, ctx)
		if resp.HttpCode != 200 {
			b.Fatalf("warmup invoke failed: %s", resp.Response)
		}
	} else if cfg.Runtime == RuntimeWasmtime || cfg.Runtime == RuntimeWazero {
		// For Cold benchmarks on Wasmtime/Wazero, execute once before loop as per original logic
		resp := pool.Invoke("fun", binary, "entry", req, ctx)
		if resp.HttpCode != 200 {
			b.Fatalf("cold-start invoke failed: %s", resp.Response)
		}
	}

	b.ResetTimer()
	for b.Loop() {
		response := pool.Invoke("fun", binary, "entry", req, ctx)
		if response.HttpCode != 200 {
			b.Fatalf("invoke function failed: %s", response.Response)
		}
	}
}

// runBenchSuite executes the benchmark for all 3 cache levels: Cold, WarmStd, WarmHybrid
func runBenchSuite(b *testing.B, baseCfg BenchConfig) {
	b.Run("Cold", func(b *testing.B) {
		cfg := baseCfg
		cfg.Cache = wasm.CacheNone
		runWasmBenchmark(b, cfg)
	})
	b.Run("WarmStd", func(b *testing.B) {
		cfg := baseCfg
		cfg.Cache = wasm.CacheStandard
		runWasmBenchmark(b, cfg)
	})
	b.Run("WarmHybrid", func(b *testing.B) {
		cfg := baseCfg
		cfg.Cache = wasm.CacheHybrid
		runWasmBenchmark(b, cfg)
	})
}

// --- NATIVE BENCHMARKS ---

func BenchmarkExecutionTime_Native_PrimeNumbers(b *testing.B) {
	computePrimes := func(n int) int {
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
	var fibFun func(n int) int
	fibFun = func(n int) int {
		if n <= 1 {
			return n
		}
		return fibFun(n-1) + fibFun(n-2)
	}
	for b.Loop() {
		fibFun(fibonacciInput)
	}
}
func BenchmarkExecutionTime_Native_Lightweight(b *testing.B) {
	for b.Loop() {
		count := 0
		for i := 0; i <= lightweightInput; i++ {
			count++
		}
		if count == 0 {
			b.Fatal("zero result")
		}
	}
}
func BenchmarkExecutionTime_Native_TailFibonacci(b *testing.B) {
	var fibTailFun func(n, a, b int) int
	fibTailFun = func(n, a, b int) int {
		if n == 0 {
			return a
		}
		return fibTailFun(n-1, b, a+b)
	}
	for b.Loop() {
		if fibTailFun(fibonacciTailInput, 0, 1) == 0 {
			b.Fatal("zero result")
		}
	}
}

// =========================================================================================
// WASMEDGE SUITES
// =========================================================================================

// --- Interpreter NoOpts ---
func Benchmark_Wasmedge_Interpreter_NoOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadPrime, Input: primeNumsInput})
}
func Benchmark_Wasmedge_Interpreter_NoOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadFib, Input: fibonacciInput})
}
func Benchmark_Wasmedge_Interpreter_NoOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadLight, Input: lightweightInput})
}
func Benchmark_Wasmedge_Interpreter_NoOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadTailFib, Input: fibonacciTailInput})
}
func Benchmark_Wasmedge_Interpreter_NoOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadStateful, Input: hostFnsInput, AddTestColl: true})
}

// --- Interpreter WithOpts ---
func Benchmark_Wasmedge_Interpreter_WithOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadPrime, Input: primeNumsInput, WithOpts: true})
}
func Benchmark_Wasmedge_Interpreter_WithOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadFib, Input: fibonacciInput, WithOpts: true})
}
func Benchmark_Wasmedge_Interpreter_WithOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadLight, Input: lightweightInput, WithOpts: true})
}
func Benchmark_Wasmedge_Interpreter_WithOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadTailFib, Input: fibonacciTailInput, WithOpts: true})
}
func Benchmark_Wasmedge_Interpreter_WithOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadStateful, Input: hostFnsInput, WithOpts: true, AddTestColl: true})
}

// --- AOT NoOpts ---
func Benchmark_Wasmedge_AOT_NoOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadPrime, Input: primeNumsInput, IsAOT: true})
}
func Benchmark_Wasmedge_AOT_NoOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadFib, Input: fibonacciInput, IsAOT: true})
}
func Benchmark_Wasmedge_AOT_NoOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadLight, Input: lightweightInput, IsAOT: true})
}
func Benchmark_Wasmedge_AOT_NoOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadTailFib, Input: fibonacciTailInput, IsAOT: true})
}
func Benchmark_Wasmedge_AOT_NoOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadStateful, Input: hostFnsInput, IsAOT: true, AddTestColl: true})
}

// --- AOT WithOpts ---
func Benchmark_Wasmedge_AOT_WithOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadPrime, Input: primeNumsInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wasmedge_AOT_WithOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadFib, Input: fibonacciInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wasmedge_AOT_WithOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadLight, Input: lightweightInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wasmedge_AOT_WithOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadTailFib, Input: fibonacciTailInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wasmedge_AOT_WithOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmedge, Workload: WorkloadStateful, Input: hostFnsInput, IsAOT: true, WithOpts: true, AddTestColl: true})
}

// =========================================================================================
// WASMTIME SUITES
// =========================================================================================

// --- JIT NoOpts ---
func Benchmark_Wasmtime_JIT_NoOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadPrime, Input: primeNumsInput})
}
func Benchmark_Wasmtime_JIT_NoOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadFib, Input: fibonacciInput})
}
func Benchmark_Wasmtime_JIT_NoOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadLight, Input: lightweightInput})
}
func Benchmark_Wasmtime_JIT_NoOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadTailFib, Input: fibonacciTailInput})
}
func Benchmark_Wasmtime_JIT_NoOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadStateful, Input: hostFnsInput, AddTestColl: true})
}

// --- JIT WithOpts ---
func Benchmark_Wasmtime_JIT_WithOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadPrime, Input: primeNumsInput, WithOpts: true})
}
func Benchmark_Wasmtime_JIT_WithOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadFib, Input: fibonacciInput, WithOpts: true})
}
func Benchmark_Wasmtime_JIT_WithOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadLight, Input: lightweightInput, WithOpts: true})
}
func Benchmark_Wasmtime_JIT_WithOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadTailFib, Input: fibonacciTailInput, WithOpts: true})
}
func Benchmark_Wasmtime_JIT_WithOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadStateful, Input: hostFnsInput, WithOpts: true, AddTestColl: true})
}

// --- AOT NoOpts ---
func Benchmark_Wasmtime_AOT_NoOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadPrime, Input: primeNumsInput, IsAOT: true})
}
func Benchmark_Wasmtime_AOT_NoOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadFib, Input: fibonacciInput, IsAOT: true})
}
func Benchmark_Wasmtime_AOT_NoOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadLight, Input: lightweightInput, IsAOT: true})
}
func Benchmark_Wasmtime_AOT_NoOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadTailFib, Input: fibonacciTailInput, IsAOT: true})
}
func Benchmark_Wasmtime_AOT_NoOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadStateful, Input: hostFnsInput, IsAOT: true, AddTestColl: true})
}

// --- AOT WithOpts ---
func Benchmark_Wasmtime_AOT_WithOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadPrime, Input: primeNumsInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wasmtime_AOT_WithOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadFib, Input: fibonacciInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wasmtime_AOT_WithOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadLight, Input: lightweightInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wasmtime_AOT_WithOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadTailFib, Input: fibonacciTailInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wasmtime_AOT_WithOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWasmtime, Workload: WorkloadStateful, Input: hostFnsInput, IsAOT: true, WithOpts: true, AddTestColl: true})
}

// =========================================================================================
// WAZERO SUITES
// =========================================================================================

// --- AOT NoOpts ---
func Benchmark_Wazero_AOT_NoOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadPrime, Input: primeNumsInput, IsAOT: true})
}
func Benchmark_Wazero_AOT_NoOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadFib, Input: fibonacciInput, IsAOT: true})
}
func Benchmark_Wazero_AOT_NoOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadLight, Input: lightweightInput, IsAOT: true})
}
func Benchmark_Wazero_AOT_NoOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadTailFib, Input: fibonacciTailInput, IsAOT: true})
}
func Benchmark_Wazero_AOT_NoOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadStateful, Input: hostFnsInput, IsAOT: true, AddTestColl: true})
}

// --- AOT WithOpts ---
func Benchmark_Wazero_AOT_WithOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadPrime, Input: primeNumsInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wazero_AOT_WithOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadFib, Input: fibonacciInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wazero_AOT_WithOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadLight, Input: lightweightInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wazero_AOT_WithOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadTailFib, Input: fibonacciTailInput, IsAOT: true, WithOpts: true})
}
func Benchmark_Wazero_AOT_WithOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadStateful, Input: hostFnsInput, IsAOT: true, WithOpts: true, AddTestColl: true})
}

// --- Interpreter NoOpts ---
func Benchmark_Wazero_Interpreter_NoOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadPrime, Input: primeNumsInput})
}
func Benchmark_Wazero_Interpreter_NoOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadFib, Input: fibonacciInput})
}
func Benchmark_Wazero_Interpreter_NoOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadLight, Input: lightweightInput})
}
func Benchmark_Wazero_Interpreter_NoOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadTailFib, Input: fibonacciTailInput})
}
func Benchmark_Wazero_Interpreter_NoOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadStateful, Input: hostFnsInput, AddTestColl: true})
}

// --- Interpreter WithOpts ---
func Benchmark_Wazero_Interpreter_WithOpts_PrimeNumbers(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadPrime, Input: primeNumsInput, WithOpts: true})
}
func Benchmark_Wazero_Interpreter_WithOpts_Fibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadFib, Input: fibonacciInput, WithOpts: true})
}
func Benchmark_Wazero_Interpreter_WithOpts_Lightweight(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadLight, Input: lightweightInput, WithOpts: true})
}
func Benchmark_Wazero_Interpreter_WithOpts_TailFibonacci(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadTailFib, Input: fibonacciTailInput, WithOpts: true})
}
func Benchmark_Wazero_Interpreter_WithOpts_Stateful(b *testing.B) {
	runBenchSuite(b, BenchConfig{Runtime: RuntimeWazero, Workload: WorkloadStateful, Input: hostFnsInput, WithOpts: true, AddTestColl: true})
}
