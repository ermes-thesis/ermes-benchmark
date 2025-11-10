package wasm_integration

import (
	"context"
	"fmt"

	datamanager_mock "mocks/dataManager"
	metadataManager_mock "mocks/metadataManager"
	"os"
	"scheduler"
	"server"
	"strconv"
	"testing"
	"time"

	"github.com/ermes-thesis/ermes-common/logger"
	"github.com/ermes-thesis/ermes-common/wasm-pool"
	"github.com/rs/zerolog"
)

func TestProva(t *testing.T) {
	fmt.Println(os.Args)
	fileToRead := os.Args[3]
	runtimeToUse := os.Args[4]
	IsAOT, err := strconv.ParseBool(os.Args[5])
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

	dataManagerMock := datamanager_mock.NewDataManager(t)
	metadataManagerMock := metadataManager_mock.NewMetadataManager(t)
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
		ExistingDomains:            nil,
		GroupTokenProviderHostName: "hostnameGTP",
		Stateful:                   false,
		IsCentralStorage:           false,
	}

	var hostFns *scheduler.HostFunctions
	if registerHostFn {
		hostFns = scheduler.NewHostFunctions(dataManagerMock, metadataManagerMock, &serverInfo, log)
	}

	var pool wasm.ExecutorPool
	switch runtimeToUse {
	case "wasmedge":
		poolImpl := wasm.NewWasmedgeExecutorPool(10, log)
		if registerHostFn {
			err := hostFns.RegisterWasmedgeHostFns(poolImpl)
			if err != nil {
				panic(err)
			}
		}
		pool = poolImpl
	case "wasmtime":
		poolImpl := wasm.NewWasmtimeExecutorPool(10, false, IsAOT, log)
		if registerHostFn {
			err := hostFns.RegisterWasmtimeHostFns(poolImpl)
			if err != nil {
				panic(err)
			}
		}
		pool = poolImpl
	case "wazero":
		poolImpl := wasm.NewWazeroExecutorPool(10, !IsAOT, false, context.Background(), log)
		if registerHostFn {
			err := hostFns.RegisterWazeroHostFns(poolImpl)
			if err != nil {
				panic(err)
			}
		}
		pool = poolImpl
	default:
		panic("runtime not supported")
	}
	defer pool.Close()

	executor := pool.Acquire()

	req, ctx := getTestReqAndCtx("userId", functionInput)
	if callInvoke {
		fmt.Println(executor.Invoke(hostFn, "entry", req, ctx))
	}
	executor.Release()
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
