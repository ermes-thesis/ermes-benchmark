module wasm_integration_test

go 1.24.4

replace github.com/ermes-thesis/ermes-common/logger => ./../ermes-common/logger

replace github.com/ermes-thesis/ermes-common/wasm-pool => ./../ermes-common/wasm-pool

replace github.com/ermes-thesis/ermes-common/model => ./../ermes-common/model

replace github.com/ermes-thesis/ermes-common/utils => ./../ermes-common/utils

replace scheduler => ./../ermes-generic-node/scheduler

replace server => ./../ermes-generic-node/server

replace mocks => ./../ermes-generic-node/mocks

replace (
	caches => ./../ermes-generic-node/caches
	config => ./../ermes-generic-node/config
	dataManager => ./../ermes-generic-node/dataManager
	db => ./../ermes-generic-node/db
	github.com/ermes-thesis/ermes-common/caches => ./../ermes-common/caches
	metadataManager => ./../ermes-generic-node/metadataManager
	tokenDecoder => ./../ermes-generic-node/tokenDecoder
)

require (
	db v0.0.0-00010101000000-000000000000
	github.com/bytecodealliance/wasmtime-go/v37 v37.0.0
	github.com/ermes-thesis/ermes-common/logger v0.0.0-00010101000000-000000000000
	github.com/ermes-thesis/ermes-common/wasm-pool v0.0.0-00010101000000-000000000000
	github.com/rs/zerolog v1.34.0
	github.com/second-state/WasmEdge-go v0.14.0
	github.com/stretchr/testify v1.11.1
	github.com/tetratelabs/wazero v1.10.1
	metadataManager v0.0.0-00010101000000-000000000000
	mocks v0.0.0-00010101000000-000000000000
	scheduler v0.0.0-00010101000000-000000000000
	server v0.0.0-00010101000000-000000000000
)

require (
	caches v0.0.0-00010101000000-000000000000 // indirect
	config v0.0.0-00010101000000-000000000000 // indirect
	dataManager v0.0.0-00010101000000-000000000000 // indirect
	github.com/cespare/xxhash/v2 v2.3.0 // indirect
	github.com/davecgh/go-spew v1.1.1 // indirect
	github.com/dgryski/go-rendezvous v0.0.0-20200823014737-9f7001d12a5f // indirect
	github.com/ermes-thesis/ermes-common/caches v0.0.0-00010101000000-000000000000 // indirect
	github.com/ermes-thesis/ermes-common/model v0.0.0-00010101000000-000000000000 // indirect
	github.com/ermes-thesis/ermes-common/utils v0.0.0-00010101000000-000000000000 // indirect
	github.com/golang-jwt/jwt/v5 v5.3.0 // indirect
	github.com/google/uuid v1.6.0 // indirect
	github.com/hashicorp/golang-lru/v2 v2.0.7 // indirect
	github.com/mattn/go-colorable v0.1.14 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	github.com/mitchellh/hashstructure/v2 v2.0.2 // indirect
	github.com/pmezard/go-difflib v1.0.0 // indirect
	github.com/redis/go-redis/v9 v9.14.0 // indirect
	github.com/rs/xid v1.6.0 // indirect
	github.com/stretchr/objx v0.5.2 // indirect
	golang.org/x/sync v0.17.0 // indirect
	golang.org/x/sys v0.38.0 // indirect
	gopkg.in/natefinch/lumberjack.v2 v2.2.1 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
	tokenDecoder v0.0.0-00010101000000-000000000000 // indirect
)

replace github.com/tetratelabs/wazero => ../wazero
