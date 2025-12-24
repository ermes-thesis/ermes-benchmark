package wasm_integration

import (
	"bufio"
	"context"
	"db"
	"fmt"
	"metadataManager/propagation"
	datamanager_mock "mocks/dataManager"
	metadataManager_mock "mocks/metadataManager"
	"os"
	"scheduler"
	"server"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/stretchr/testify/mock"
)

func createHostFns(t *testing.T, log logger.Logger) *scheduler.HostFunctions {
	dataManager := datamanager_mock.NewDataManager(t)
	dataManager.EXPECT().GetRecord("255ef4af-3a49-4382-a90d-6524bdee5ad1", []string{"test"}, "userId", "battiti").Return("72", nil).Maybe()
	dataManager.EXPECT().SetCollectionAndPropagate(mock.Anything, "nuova_collection", map[string]db.RecordValue{}, []string{"test", "pippo"}, "userId", false, false).Return(nil).Maybe()
	dataManager.EXPECT().SetCollectionAndPropagate(mock.Anything, "multiple_get_coll", map[string]db.RecordValue{}, []string{"test", "fake"}, "userId", false, false).Return(nil).Maybe()
	dataManager.EXPECT().GetRecords(mock.AnythingOfType("string"), []string{"test"}, "userId", []string{"testMGET", "testMGET2"}).Return([]any{"val1", "val2"}, nil).Maybe()
	dataManager.EXPECT().GetRecords(mock.AnythingOfType("string"), []string{"test"}, "userId", []string{"cicico"}).Return([]any{"val1"}, nil).Maybe()
	metadataManager := metadataManager_mock.NewMetadataManager(t)
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
		ExistingDomains:            map[string]struct{}{"IT": {}, "IT/Milan": {}},
		GroupTokenProviderHostName: "hostnameGTP",
		Stateful:                   false,
		IsCentralStorage:           false,
	}
	return scheduler.NewHostFunctions(dataManager, metadataManager, &serverInfo, log)
}

func TestMemoryGeneric(t *testing.T) {
	fileToRead := os.Args[3]
	runtimeToUse := os.Args[4]
	isAOT, err := strconv.ParseBool(os.Args[5])
	if err != nil {
		panic(err)
	}
	registerHostFn, err := strconv.ParseBool(os.Args[6])
	if err != nil {
		panic(err)
	}
	functionInput, err := strconv.Atoi(os.Args[7])
	if err != nil {
		panic(err)
	}
	callInvoke, err := strconv.ParseBool(os.Args[8])
	if err != nil {
		panic(err)
	}

	hostFn, err := os.ReadFile(fileToRead)
	if err != nil {
		panic(err)
	}
	log, err := logger.NewLogger(logger.Config{
		Level:         logger.FatalLevel,
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

	cfg := wasm.Config{
		PoolSize:  1,
		WithCache: wasm.CacheHybrid,
		CacheSize: 20,
		IsAot:     isAOT,
	}
	var pool wasm.ExecutorPool
	switch runtimeToUse {
	case "wasmedge":
		poolImpl := wasm.NewWasmedgeExecutorPool(cfg, log)
		if registerHostFn {
			err = createHostFns(t, log).RegisterWasmedgeHostFns(poolImpl)
			if err != nil {
				panic(err)
			}
		}
		pool = poolImpl
	case "wasmtime":
		poolImpl := wasm.NewWasmtimeExecutorPool(cfg, log)
		if registerHostFn {
			err = createHostFns(t, log).RegisterWasmtimeHostFns(poolImpl)
			if err != nil {
				panic(err)
			}
		}
		pool = poolImpl
	case "wazero":
		poolImpl := wasm.NewWazeroExecutorPool(cfg, context.Background(), log)
		if registerHostFn {
			err = createHostFns(t, log).RegisterWazeroHostFns(poolImpl)
			if err != nil {
				panic(err)
			}
		}
		pool = poolImpl
	default:
		panic("runtime not supported")
	}
	defer pool.Close()

	req, ctx := getTestReqAndCtx("userId", functionInput)
	if callInvoke {
		fmt.Println(pool.Invoke("", hostFn, "entry", req, ctx))
	}
}

func TestMemoryTimeline(t *testing.T) {
	// Args: [0]... [3]=configuration(Runtime_AOT) [4]=cacheType(Hybrid|Standard)
	if len(os.Args) < 5 {
		panic("Not enough arguments. Usage: ... Runtime_AOT CacheType")
	}
	configuration := os.Args[3]
	cacheTypeStr := os.Args[4]

	parts := strings.Split(configuration, "_")
	runtime := parts[0]
	isAot := parts[1] == "AOT"

	// Parse Cache Type
	var cacheType wasm.CacheType
	switch cacheTypeStr {
	case "Hybrid":
		cacheType = wasm.CacheHybrid
	case "Standard":
		cacheType = wasm.CacheStandard
	default:
		panic("Invalid cache type: " + cacheTypeStr + " (must be Hybrid or Standard)")
	}

	log, err := logger.NewLogger(logger.Config{
		Level:         logger.FatalLevel,
		Format:        "text",
		Output:        nil,
		StdoutEnabled: false,
		Muted:         true,
	})
	if err != nil {
		panic(err)
	}

	binaries := []string{
		"_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm",
		"_WASM_BINARIES/cpuIntensive/primeNums/primeNums_wOpts.wasm",
		"_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts.wasm",
		"_WASM_BINARIES/stateful/statefulFunction_wOpts.wasm",
		"_WASM_BINARIES/lightweight/lightweight_wOpts.wasm",
		"_WASM_BINARIES/others/fun1_wOpts.wasm",
		"_WASM_BINARIES/others/fun2_wOpts.wasm",
		"_WASM_BINARIES/others/fun3_wOpts.wasm",
		"_WASM_BINARIES/others/fun4_wOpts.wasm",
		"_WASM_BINARIES/others/fun5_wOpts.wasm",
		"_WASM_BINARIES/others/fun6_wOpts.wasm",
		"_WASM_BINARIES/others/fun7_wOpts.wasm",
		"_WASM_BINARIES/others/fun8_wOpts.wasm",
		"_WASM_BINARIES/others/fun9_wOpts.wasm",
		"_WASM_BINARIES/others/fun10_wOpts.wasm",
		"_WASM_BINARIES/others/fun11_wOpts.wasm",
		"_WASM_BINARIES/others/fun12_wOpts.wasm",
		"_WASM_BINARIES/others/fun13_wOpts.wasm",
		"_WASM_BINARIES/others/fun14_wOpts.wasm",
		"_WASM_BINARIES/others/fun15_wOpts.wasm",
	}
	inputs := []int{
		10,
		100000,
		20000,
		0,
		20000,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
		0,
	}

	// Create Config with dynamic Cache Type
	poolConfig := wasm.Config{
		PoolSize:  1,
		WithCache: cacheType, // Dynamic
		CacheSize: 10,
		IsAot:     isAot,
	}

	var pool wasm.ExecutorPool
	switch runtime {
	case "WasmEdge":
		if isAot {
			for i, file := range binaries {
				if !strings.HasSuffix(file, "_wOpts.wasm") {
					binaries[i] = strings.ReplaceAll(file, ".wasm", "_noOpts_AOTwasmedge.wasm")
				} else {
					binaries[i] = strings.ReplaceAll(file, ".wasm", "_AOTwasmedge.wasm")
				}
			}
		}
		poolImpl := wasm.NewWasmedgeExecutorPool(poolConfig, log)
		err = createHostFns(t, log).RegisterWasmedgeHostFns(poolImpl)
		if err != nil {
			panic(err)
		}
		pool = poolImpl
	case "Wasmtime":
		if isAot {
			for i, file := range binaries {
				if !strings.HasSuffix(file, "_wOpts.wasm") {
					binaries[i] = strings.ReplaceAll(file, ".wasm", "_noOpts_AOTwasmtime.wasm")
				} else {
					binaries[i] = strings.ReplaceAll(file, ".wasm", "_AOTwasmtime.wasm")
				}
			}
		}
		poolImpl := wasm.NewWasmtimeExecutorPool(poolConfig, log)
		err = createHostFns(t, log).RegisterWasmtimeHostFns(poolImpl)
		if err != nil {
			panic(err)
		}
		pool = poolImpl
	case "Wazero":
		poolImpl := wasm.NewWazeroExecutorPool(poolConfig, context.Background(), log)
		err = createHostFns(t, log).RegisterWazeroHostFns(poolImpl)
		if err != nil {
			panic(err)
		}
		pool = poolImpl
	default:
		panic("runtime not supported")
	}
	defer pool.Close()

	stdinReader := bufio.NewReader(os.Stdin)

	for i, fileToRead := range binaries {
		input := inputs[i]
		wasmBuffer, err := os.ReadFile(fileToRead)
		if err != nil {
			panic(err)
		}
		req, ctx := getTestReqAndCtx("userId", input)

		for j := 0; j < 50; j++ {
			res := pool.Invoke(fileToRead, wasmBuffer, "entry", req, ctx)
			if res.HttpCode != 200 {
				fmt.Fprintf(os.Stderr, "Error on %s: %+v\n", fileToRead, res)
			}

			//runtime.GC()
			fmt.Println("SYNC_POINT")
			os.Stdout.Sync()

			_, err = stdinReader.ReadString('\n')
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error on %s: %+v\n", fileToRead, res)
				break
			}
		}
	}
	fmt.Fprintln(os.Stderr, "Test Go completato.")
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
