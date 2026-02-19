package wasm_benchmark

import (
	"config"
	"context"
	"dataManager/collectionsDiscoverer"
	"dataManager/lru"
	"dataManager/messages"
	"dataManager/migrationManager"
	"dataManager/migrationManager/penalityFunction"
	dataManagerShared "dataManager/shared"
	"db"
	"encoding/json"
	"fmt"
	"metadataManager/propagation"
	"os"
	"runtime"
	"scheduler"
	"server"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/model"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/stretchr/testify/require"
)

// --- Configuration ---

var concurrencyLevels = []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 20, 30, 40, 50, 60, 70} // Utenti simultanei
var poolSizes = []int{1, 2, 4, 8, 16, 32, 64}                                                // Dimensioni pool

const testRepetitions = 5

// Runtime supportati-
var runtimesToTest = []string{"Wasmtime_JIT", "Wasmtime_AOT", "Wasmedge", "Wazero"}

// Struttura output JSON aggiornata con Runtime e Repetition
type ScalabilityResult struct {
	Runtime     string  `json:"runtime"`
	Workload    string  `json:"workload"`
	PoolSize    int     `json:"pool_size"`
	Concurrency int     `json:"concurrency"`
	Repetition  int     `json:"repetition"`
	RPS         float64 `json:"rps"`
	AvgLatency  float64 `json:"avg_latency_ms"`
	Errors      int32   `json:"errors"`
}

// --- Helpers ---

func createScaleLogger(t testing.TB) logger.Logger {
	log, err := logger.NewLogger(logger.Config{
		Level:         logger.ErrorLevel,
		Format:        "text",
		StdoutEnabled: true,
	})
	require.NoError(t, err)
	return log
}

// createScaleHostFns configura i mock per le funzioni stateful
func createScaleHostFns(log logger.Logger) *scheduler.HostFunctions {

	dataManager := &StubDataManager{}
	metadataManager := &StubMetadataManager{}

	serverInfo := server.ServerInfo{
		HostName: "hostname", Address: "address", Port: "port",
		MetadataDomain: "domain", Secret: "secret", ClientSecret: "clientSecret",
		ExistingDomains: map[string]struct{}{"IT": {}, "IT/Milan": {}},
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

// requestsPerWorker ora è un parametro dinamico
func runScalabilityScenario(t *testing.T, runtimeName string, workload string, inputVal int, requestsPerWorker int) {
	log := createScaleLogger(t)
	path := getScaleWasmPath(workload, runtimeName == "Wasmedge", runtimeName == "Wasmtime_AOT")
	binary, err := os.ReadFile(path)
	require.NoError(t, err)

	isAOT := runtimeName == "Wazero" || runtimeName == "Wasmedge" || strings.HasSuffix(runtimeName, "AOT")
	cleanRuntimeName := strings.Split(runtimeName, "_")[0]

	fmt.Printf("\n=== Scalability Test: Runtime=%s | Workload=%s | AOT=%v | Req/Worker=%d ===\n", cleanRuntimeName, workload, isAOT, requestsPerWorker)

	f, err := os.OpenFile("scalability_results.json", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	require.NoError(t, err)
	defer f.Close()

	for _, pSize := range poolSizes {
		fmt.Printf("   > Pool Size: %d\n", pSize)

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
			hostFns = createScaleHostFns(log)
		}

		switch cleanRuntimeName {
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
			t.Fatalf("Unknown runtime: %s", cleanRuntimeName)
		}
		require.NoError(t, err)

		// --- WARMUP (Una tantum per Pool) ---
		req, ctx := getScaleReqAndCtx(workload, inputVal)
		warmupCount := 10
		for k := 0; k < warmupCount; k++ {
			pool.Invoke("fun", binary, "entry", req, ctx)
		}

		// Concurrency Loop
		for _, workers := range concurrencyLevels {
			fmt.Printf("      > Concurrency level: %d\n", workers)

			// --- REPETITION LOOP ---
			// Ripetiamo il test N volte per avere dati statistici solidi
			for rep := 1; rep <= testRepetitions; rep++ {
				var wg sync.WaitGroup
				var totalDuration atomic.Int64
				var errorCount atomic.Int32

				// Start Gun
				startChan := make(chan struct{})

				totalRequests := workers * requestsPerWorker

				// Forza GC prima di OGNI ripetizione
				runtime.GC()
				time.Sleep(200 * time.Millisecond)

				startTotal := time.Now()

				for i := 0; i < workers; i++ {
					wg.Go(func() {
						var localDur int64
						var localErr int32

						<-startChan

						for j := 0; j < requestsPerWorker; j++ {
							startReq := time.Now()
							response := pool.Invoke("fun", binary, "entry", req, ctx)
							dur := time.Since(startReq).Nanoseconds()

							localDur += dur
							if response.HttpCode != 200 {
								localErr++
							}

						}
						totalDuration.Add(localDur)
						errorCount.Add(localErr)
					})
				}

				close(startChan)
				wg.Wait()
				elapsedTotal := time.Since(startTotal)

				rps := float64(totalRequests) / elapsedTotal.Seconds()
				avgLatencyMs := (float64(totalDuration.Load()) / float64(totalRequests)) / 1e6

				fmt.Printf("         Repetition %d: RPS=%.2f | Avg Latency=%.2f ms | Errors=%d\n", rep, rps, avgLatencyMs, errorCount.Load())

				// Salvataggio con Repetition ID
				res := ScalabilityResult{
					Runtime:     cleanRuntimeName,
					Workload:    workload,
					PoolSize:    pSize,
					Concurrency: workers,
					Repetition:  rep, // <--- ID ripetizione
					RPS:         rps,
					AvgLatency:  avgLatencyMs,
					Errors:      errorCount.Load(),
				}
				jsonBytes, _ := json.Marshal(res)
				f.WriteString(string(jsonBytes) + "\n")
			}
		}
		pool.Close()
		fmt.Println("Done.")
	}
}

// --- Entry Points ---

// Esegue tutti i test per tutti i runtime
func TestScalability_All(t *testing.T) {
	cpuWarmup()

	for _, rt := range runtimesToTest {
		// 1. Lightweight
		runScalabilityScenario(t, rt, "Lightweight", 20000, 5000)

		// 2. CPU Intensive
		runScalabilityScenario(t, rt, "PrimeNumbers", 2000000, 10)

		// 3. Stateful
		runScalabilityScenario(t, rt, "Stateful", 0, 5000)
	}
}

func cpuWarmup() {
	fmt.Println("\n🔥🔥🔥 CPU WARMUP: Burning cycles for 2m to reach steady state... 🔥🔥🔥")
	start := time.Now()
	var wg sync.WaitGroup
	numCPU := runtime.NumCPU()

	for i := 0; i < numCPU; i++ {
		wg.Go(func() {
			for time.Since(start) < 2*time.Minute {
				val := 0
				for j := 0; j < 100000; j++ {
					val += j * j
				}
			}
		})
	}
	wg.Wait()
	fmt.Println("✅ CPU Warmup Complete. Starting Benchmark...")
}

// --- BENCHMARK STUBS ---
// Sostituiscono i Mock di Testify per evitare memory leaks durante benchmark prolungati.
// Implementano le interfacce richieste da scheduler.HostFunctions restituendo valori statici.
type StubDataManager struct{}

func (m *StubDataManager) Init(collections *dataManagerShared.CollectionPartialView, penalityFunc penalityFunction.PenalityFunc, config config.MigrationManagerConfig, lruConfig config.LruConfig, server server.ServerType, serverInfo server.ServerInfo, lruCache *lru.LRUCache[dataManagerShared.Collection], dbInterface db.GenericDB, logger logger.Logger) {
}

func (m *StubDataManager) GetMigrationManager() migrationManager.MigrationManager {
	return nil
}

func (m *StubDataManager) GetCollectionsDiscoverer() collectionsDiscoverer.CollectionsDiscoverer {
	return nil
}

func (m *StubDataManager) GetRecord(collectionId string, groups []string, userId string, recordName string) (string, error) {
	return "72", nil
}

func (m *StubDataManager) GetRecords(collectionId string, groups []string, userId string, recordNames ...string) ([]any, error) {
	return []any{"val1"}, nil
}

func (m *StubDataManager) UpdateCollectionsRecordsAndPropagate(updates []messages.CollectionUpdate, groups []string, userId string) error {
	return nil
}

func (m *StubDataManager) UpdateCollectionsGroupsAndPropagate(updates []messages.CollectionGroupUpdate) error {
	return nil
}

func (m *StubDataManager) SetCollectionAndPropagate(collectionId string, collectionName string, records map[string]db.RecordValue, groups []string, userId string, isStrong bool, skipUniquenessCheck bool) error {
	return nil
}

func (m *StubDataManager) RemoveCollectionAndPropagate(collectionId string, groups []string, userId string) error {
	return nil
}

func (m *StubDataManager) GetCollectionVectorClockValue(collectionId string) (uint64, error) {
	return 0, nil
}

type StubMetadataManager struct{}

func (m *StubMetadataManager) CreateMetadata(collectionId string, metadata model.Metadata, reqOrigin propagation.PropagationOrigin) error {
	return nil
}

func (m *StubMetadataManager) DeleteMetadata(collectionId string, geolocation string, reqOrigin propagation.PropagationOrigin, isCollRecreated bool) error {
	return nil
}

func (m *StubMetadataManager) UpdateGroupsInCollection(collectionId string, userGroups []string, userId string, groupsToAdd []string, groupsToRemove []string) (*propagation.UpdateGroupResponse, error) {
	return nil, nil
}

func (m *StubMetadataManager) SetCollectionGroups(collectionId string, message propagation.UpdateGroupResponse) error {
	return nil
}

func (m *StubMetadataManager) ExecuteQueries(functionName string, functionVersion string, templateParamsMapping string, groups []string, userId string, groupToken string, geolocation string) (map[uint64]model.QueryResult, error) {
	return nil, nil
}
