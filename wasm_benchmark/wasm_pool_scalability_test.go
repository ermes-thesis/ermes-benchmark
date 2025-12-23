package wasm_integration_test

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/stretchr/testify/require"
)

// --- Configuration ---

// 1. Livelli di Concorrenza (Utenti simultanei)
var concurrencyLevels = []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 20, 25, 50, 75, 100}

// 2. Dimensioni del Pool da testare
var poolSizes = []int{1, 2, 4, 8, 16, 32, 64, 128}

const requestsPerWorker = 10
const ScalabilityTimeout = 5 * time.Second

// Struttura per l'output JSON
type ScalabilityResult struct {
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
		Level:     logger.WarnLevel,
		Format:    "text",
		AddSource: false,
		Muted:     true,
	})
	require.NoError(t, err)
	return log
}

func getScaleWasmPath(workload string) string {
	baseDir := "_WASM_BINARIES/"
	switch workload {
	case "PrimeNumbers":
		return baseDir + "cpuIntensive/primeNums/primeNums.wasm"
	case "Lightweight":
		return baseDir + "lightweight/lightweight.wasm"
	default:
		panic("Unknown workload: " + workload)
	}
}

func getScaleReqAndCtx(nVal int) ([]byte, []byte) {
	req := fmt.Sprintf(`{"prova": "ciao", "n": "%d"}`, nVal)
	ctx := `{"userId": "scaleUser", "groupList": ["test"], "collections": {}}`
	return []byte(req), []byte(ctx)
}

// --- Core Scalability Engine ---

func runScalabilityScenario(t *testing.T, workload string, inputVal int, isAOT bool) {
	log := createScaleLogger(t)
	path := getScaleWasmPath(workload)
	binary, err := os.ReadFile(path)
	require.NoError(t, err)

	fmt.Printf("\n=== Starting Scalability Matrix for %s (AOT: %v) ===\n", workload, isAOT)

	// File di output
	f, err := os.OpenFile("scalability_results.json", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	require.NoError(t, err)
	defer f.Close()

	// Outer Loop: Pool Size
	for _, pSize := range poolSizes {
		fmt.Printf("\n--- Testing with Pool Size: %d ---\n", pSize)

		// Creiamo un NUOVO pool per ogni dimensione
		poolConfig := wasm.Config{
			PoolSize:  pSize,
			Timeout:   ScalabilityTimeout,
			WithCache: wasm.CacheHybrid,
			CacheSize: 2,
			IsAot:     isAOT,
		}

		// Nota: Usa Wazero o Wasmtime a seconda delle preferenze. Qui uso Wasmtime per default.
		pool := wasm.NewWazeroExecutorPool(poolConfig, context.Background(), log)

		// Warmup iniziale del pool
		req, ctx := getScaleReqAndCtx(inputVal)
		resp := pool.Invoke("fun", binary, "entry", req, ctx)
		if resp.HttpCode != 200 {
			t.Fatalf("Warmup failed: %s", resp.Response)
		}

		// Inner Loop: Concurrency Levels
		for _, workers := range concurrencyLevels {
			var wg sync.WaitGroup
			var errorCount int64
			var totalDuration int64 // nanoseconds

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

			// Calcolo metriche
			rps := float64(totalRequests) / elapsedTotal.Seconds()
			avgLatencyMs := (float64(totalDuration) / float64(totalRequests)) / 1e6

			fmt.Printf("Pool: %3d | Users: %3d | RPS: %8.2f | Lat: %6.2f ms | Errs: %d\n",
				pSize, workers, rps, avgLatencyMs, errorCount)

			// Salvataggio
			res := ScalabilityResult{
				Workload:    fmt.Sprintf("%s (AOT=%v)", workload, isAOT),
				PoolSize:    pSize,
				Concurrency: workers,
				RPS:         rps,
				AvgLatency:  avgLatencyMs,
				Errors:      errorCount,
			}
			jsonBytes, _ := json.Marshal(res)
			f.WriteString(string(jsonBytes) + "\n")
		}

		pool.Close() // Chiudiamo il pool prima di cambiarne la dimensione
	}
}

func TestScalability_Lightweight(t *testing.T) {
	// Pulisce il file risultati precedente se esiste
	_ = os.Remove("scalability_results.json")
	// Test su funzione leggera
	runScalabilityScenario(t, "Lightweight", 20000, true)
}

func TestScalability_PrimeNums(t *testing.T) {
	// Test su funzione pesante
	runScalabilityScenario(t, "PrimeNumbers", 200000, true)
}
