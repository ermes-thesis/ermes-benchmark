package wasm_benchmark

import (
	"context"
	"encoding/json"
	"fmt"
	datamanager_mock "mocks/dataManager"
	metadataManager_mock "mocks/metadataManager"
	"os"
	"scheduler"
	"server"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

// --- Configuration ---

var concurrencyLevels = []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 20, 25, 50, 75, 100} // Utenti simultanei
var poolSizes = []int{1, 2, 4, 8, 16, 32, 64, 128}                                        // Dimensioni pool

const requestsPerWorker = 50

// Runtime supportati
var runtimesToTest = []string{"Wasmtime_AOT"}

// Struttura output JSON aggiornata con Runtime
type ScalabilityResult struct {
	Runtime     string  `json:"runtime"`
	Workload    string  `json:"workload"`
	PoolSize    int     `json:"pool_size"`
	Concurrency int     `json:"concurrency"`
	RPS         float64 `json:"rps"`
	AvgLatency  float64 `json:"avg_latency_ms"`
	Errors      int64   `json:"errors"`
}

// --- Helpers ---

func createScaleLogger(t testing.TB) logger.Logger {
	log, err := logger.NewLogger(logger.Config{
		Level:     logger.ErrorLevel, // Solo Errori per ridurre rumore performance
		Format:    "text",
		AddSource: false,
		Muted:     true,
	})
	require.NoError(t, err)
	return log
}

// createScaleHostFns configura i mock per le funzioni stateful
func createScaleHostFns(t testing.TB, log logger.Logger) *scheduler.HostFunctions {
	dataManager := datamanager_mock.NewDataManager(t)
	// Mock generici per permettere qualsiasi chiamata standard dalle funzioni stateful
	dataManager.EXPECT().GetRecord(mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return("72", nil).Maybe()
	dataManager.EXPECT().SetCollectionAndPropagate(mock.Anything, mock.Anything, mock.Anything, mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(nil).Maybe()
	dataManager.EXPECT().GetRecords(mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return([]any{"val1"}, nil).Maybe()

	metadataManager := metadataManager_mock.NewMetadataManager(t)
	metadataManager.EXPECT().CreateMetadata(mock.Anything, mock.Anything, mock.Anything).Return(nil).Maybe()

	serverInfo := server.ServerInfo{
		HostName: "hostname", Address: "address", Port: "port",
		MetadataDomain: "domain", Secret: "secret", ClientSecret: "clientSecret",
		ExistingDomains: map[string]struct{}{"IT": {}},
	}
	return scheduler.NewHostFunctions(dataManager, metadataManager, &serverInfo, log)
}

func getScaleWasmPath(workload string, wasmedgeAot bool, wasmtimeAot bool) string {
	baseDir := "_WASM_BINARIES/"
	var path string
	switch workload {
	case "PrimeNumbers":
		path = baseDir + "cpuIntensive/primeNums/primeNums_wOpts.wasm"
	case "Lightweight":
		path = baseDir + "lightweight/lightweight_wOpts.wasm"
	case "Stateful":
		path = baseDir + "stateful/statefulFunction_wOpts.wasm"
	default:
		panic("Unknown workload: " + workload)
	}

	if wasmedgeAot {
		path = strings.ReplaceAll(path, ".wasm", "_AOTwasmedge.wasm")
	}
	if wasmtimeAot {
		path = strings.ReplaceAll(path, ".wasm", "_AOTwasmtime.wasm")
	}

	return path
}

func getScaleReqAndCtx(workload string, nVal int) ([]byte, []byte) {
	req := fmt.Sprintf(`{"prova": "ciao", "n": "%d"}`, nVal)

	testColl := ""
	if workload == "Stateful" {
		timestamp, _ := time.Now().MarshalJSON()
		testColl = `"test_collection": [{"Id": "doc1", "Metadata": {"consistency": 1, "name": "dati", "createdAt": ` + string(timestamp) + `}}]`
	}

	ctx := fmt.Sprintf(`{"userId": "scaleUser", "groupList": ["test"], "collections": {%s}}`, testColl)
	return []byte(req), []byte(ctx)
}

// --- Core Scalability Engine ---

func runScalabilityScenario(t *testing.T, runtime string, workload string, inputVal int) {
	log := createScaleLogger(t)
	path := getScaleWasmPath(workload, runtime == "Wasmedge", runtime == "Wasmtime_AOT")
	binary, err := os.ReadFile(path)
	require.NoError(t, err)

	isAOT := runtime == "Wazero" || runtime == "Wasmedge" || strings.HasSuffix(runtime, "AOT")
	runtime = strings.Split(runtime, "_")[0]

	fmt.Printf("\n=== Scalability Test: Runtime=%s | Workload=%s | AOT=%v ===\n", runtime, workload, isAOT)

	f, err := os.OpenFile("scalability_results.json", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	require.NoError(t, err)
	defer f.Close()

	for _, pSize := range poolSizes {
		fmt.Printf("   > Pool Size: %d... ", pSize)

		// Configurazione Pool
		poolConfig := wasm.Config{
			PoolSize:  pSize,
			WithCache: wasm.CacheHybrid,
			CacheSize: 2,
			IsAot:     isAOT,
		}

		// Istanziazione del Pool specifico per Runtime
		var pool wasm.ExecutorPool
		var hostFns *scheduler.HostFunctions

		if workload == "Stateful" {
			hostFns = createScaleHostFns(t, log)
		}

		switch runtime {
		case "Wasmedge":
			p := wasm.NewWasmedgeExecutorPool(poolConfig, log)
			if workload == "Stateful" {
				err = hostFns.RegisterWasmedgeHostFns(p)
			}
			pool = p
		case "Wasmtime":
			p := wasm.NewWasmtimeExecutorPool(poolConfig, log)
			if workload == "Stateful" {
				err = hostFns.RegisterWasmtimeHostFns(p)
			}
			pool = p
		case "Wazero":
			p := wasm.NewWazeroExecutorPool(poolConfig, context.Background(), log)
			if workload == "Stateful" {
				err = hostFns.RegisterWazeroHostFns(p)
			}
			pool = p
		default:
			t.Fatalf("Unknown runtime: %s", runtime)
		}
		require.NoError(t, err)

		// Warmup
		req, ctx := getScaleReqAndCtx(workload, inputVal)
		resp := pool.Invoke("fun", binary, "entry", req, ctx)
		if resp.HttpCode != 200 {
			t.Fatalf("Warmup failed: %s", resp.Response)
		}

		// Concurrency Loop
		for _, workers := range concurrencyLevels {
			var wg sync.WaitGroup
			var errorCount int64
			var totalDuration int64

			wg.Add(workers)
			totalRequests := workers * requestsPerWorker
			startTotal := time.Now()

			for i := 0; i < workers; i++ {
				go func() {
					defer wg.Done()
					for j := 0; j < requestsPerWorker; j++ {
						startReq := time.Now()
						response := pool.Invoke("fun", binary, "entry", req, ctx)
						dur := time.Since(startReq).Nanoseconds()
						atomic.AddInt64(&totalDuration, dur)
						if response.HttpCode != 200 {
							atomic.AddInt64(&errorCount, 1)
						}
					}
				}()
			}

			wg.Wait()
			elapsedTotal := time.Since(startTotal)

			rps := float64(totalRequests) / elapsedTotal.Seconds()
			avgLatencyMs := (float64(totalDuration) / float64(totalRequests)) / 1e6

			// Salvataggio
			res := ScalabilityResult{
				Runtime:     runtime,
				Workload:    workload,
				PoolSize:    pSize,
				Concurrency: workers,
				RPS:         rps,
				AvgLatency:  avgLatencyMs,
				Errors:      errorCount,
			}
			jsonBytes, _ := json.Marshal(res)
			f.WriteString(string(jsonBytes) + "\n")
		}
		pool.Close()
		fmt.Println("Done.")
	}
}

// --- Entry Points ---

// Esegue tutti i test per tutti i runtime
func TestScalability_All(t *testing.T) {
	_ = os.Remove("scalability_results.json")

	for _, rt := range runtimesToTest {
		// 1. Lightweight (Test overhead puro)
		runScalabilityScenario(t, rt, "Lightweight", 20000)

		// 2. CPU Intensive (PrimeNums)
		runScalabilityScenario(t, rt, "PrimeNumbers", 200000)

		// 3. Stateful (Test host functions & I/O simulation)
		runScalabilityScenario(t, rt, "Stateful", 0)
	}
}
