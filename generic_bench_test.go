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
	"runtime"
	"scheduler"
	"server"
	"strconv"
	"testing"
	"time"

	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
	"github.com/stretchr/testify/mock"
)

func createHostFns(t *testing.T, log logger.Logger) *scheduler.HostFunctions {
	dataManager := datamanager_mock.NewDataManager(t)
	dataManager.EXPECT().SetCollectionAndPropagate(mock.Anything, "testCollection", map[string]db.RecordValue{}, []string{"groupA"}, "userId", false, false).Return(nil)
	dataManager.EXPECT().SetCollectionAndPropagate(mock.Anything, "seqCollection", map[string]db.RecordValue{}, []string{"groupA"}, "userId", true, false).Return(nil)
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
		ExistingDomains:            map[string]struct{}{"IT": {}},
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

	cfg := wasm.Config{
		PoolSize:  1,
		WithCache: true,
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
		fmt.Println(pool.Invoke(hostFn, "entry", req, ctx))
	}
}

func TestMemoryTimeline(t *testing.T) {
	runtimeToUse := os.Args[3]

	log, err := logger.NewLogger(logger.Config{
		Level:         zerolog.FatalLevel,
		Format:        "text",
		Output:        nil,
		StdoutEnabled: false,
		Muted:         true,
	})
	if err != nil {
		panic(err)
	}

	binaries := []string{
		"_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci.wasm",
		"_WASM_BINARIES/cpuIntensive/fibonacci/fibonacci_wOpts.wasm",
		"_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums.wasm",
		"_WASM_BINARIES/cpuIntensive/primeNums/fnPrimeNums_wOpts.wasm",
		"_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci.wasm",
		"_WASM_BINARIES/cpuIntensive/tailFibonacci/tailFibonacci_wOpts.wasm",
		"_WASM_BINARIES/hostFns/functionCreateCollections.wasm",
		"_WASM_BINARIES/hostFns/functionCreateCollections_wOpts.wasm",
		"_WASM_BINARIES/lightweight/lightweight.wasm",
		"_WASM_BINARIES/lightweight/lightweight_wOpts.wasm",
	}
	inputs := []int{
		10,
		10,
		100000,
		100000,
		20000,
		20000,
		0,
		0,
		20000,
		20000,
	}

	var pool wasm.ExecutorPool
	switch runtimeToUse {
	case "wasmedge":
		poolImpl := wasm.NewWasmedgeExecutorPool(wasm.Config{
			PoolSize:  1,
			WithCache: true,
			IsAot:     false,
		}, log)
		err = createHostFns(t, log).RegisterWasmedgeHostFns(poolImpl)
		if err != nil {
			panic(err)
		}
		pool = poolImpl
	case "wasmtime":
		poolImpl := wasm.NewWasmtimeExecutorPool(wasm.Config{
			PoolSize:  1,
			WithCache: true,
			IsAot:     false,
		}, log)
		err = createHostFns(t, log).RegisterWasmtimeHostFns(poolImpl)
		if err != nil {
			panic(err)
		}
		pool = poolImpl
	case "wazero":
		poolImpl := wasm.NewWazeroExecutorPool(wasm.Config{
			PoolSize:  1,
			WithCache: true,
			IsAot:     true,
		}, context.Background(), log)
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
			res := pool.Invoke(wasmBuffer, "entry", req, ctx)
			if res.HttpCode != 200 {
				fmt.Fprintf(os.Stderr, "Error on %s: %+v\n", fileToRead, res)
			}

			runtime.GC()
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
