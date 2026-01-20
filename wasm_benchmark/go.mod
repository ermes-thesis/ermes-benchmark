module wasm_benchmark

go 1.24.4

replace (
	github.com/ermes-thesis/ermes-common/logger => ./../../ermes-common/logger
	github.com/ermes-thesis/ermes-common/model => ./../../ermes-common/model
	github.com/ermes-thesis/ermes-common/utils => ./../../ermes-common/utils
	github.com/ermes-thesis/ermes-common/wasm-pool => ./../../ermes-common/wasm-pool
	github.com/ermes-thesis/ermes-sdk-go => ./../../ermes-sdk-go
)

replace (
	caches => ./../../ermes-generic-node/caches
	config => ./../../ermes-generic-node/config
	dataManager => ./../../ermes-generic-node/dataManager
	db => ./../../ermes-generic-node/db
	github.com/ermes-thesis/ermes-common/caches => ./../../ermes-common/caches
	metadataManager => ./../../ermes-generic-node/metadataManager
	mocks => ./../../ermes-generic-node/mocks
	scheduler => ./../../ermes-generic-node/scheduler
	server => ./../../ermes-generic-node/server
	tokenDecoder => ./../../ermes-generic-node/tokenDecoder
)

require github.com/ermes-thesis/ermes-sdk-go v0.0.0-00010101000000-000000000000

require (
	db v0.0.0-00010101000000-000000000000
	github.com/ermes-thesis/ermes-common/logger v0.0.0-00010101000000-000000000000
	github.com/ermes-thesis/ermes-common/wasm-pool v0.0.0-00010101000000-000000000000
	github.com/stretchr/testify v1.11.1
	metadataManager v0.0.0-00010101000000-000000000000
	mocks v0.0.0-00010101000000-000000000000
	scheduler v0.0.0-00010101000000-000000000000
	server v0.0.0-00010101000000-000000000000
)

require (
	caches v0.0.0-00010101000000-000000000000 // indirect
	config v0.0.0-00010101000000-000000000000 // indirect
	dataManager v0.0.0-00010101000000-000000000000 // indirect
	github.com/bytecodealliance/wasmtime-go/v40 v40.0.0 // indirect
	github.com/cespare/xxhash/v2 v2.3.0 // indirect
	github.com/davecgh/go-spew v1.1.2-0.20180830191138-d8f796af33cc // indirect
	github.com/dgryski/go-rendezvous v0.0.0-20200823014737-9f7001d12a5f // indirect
	github.com/ermes-thesis/ermes-common/caches v0.0.0-00010101000000-000000000000 // indirect
	github.com/ermes-thesis/ermes-common/model v0.0.0 // indirect
	github.com/ermes-thesis/ermes-common/utils v0.0.0 // indirect
	github.com/golang-jwt/jwt/v5 v5.3.0 // indirect
	github.com/google/uuid v1.6.0 // indirect
	github.com/hashicorp/golang-lru/v2 v2.0.7 // indirect
	github.com/mattn/go-colorable v0.1.14 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	github.com/mitchellh/hashstructure/v2 v2.0.2 // indirect
	github.com/pmezard/go-difflib v1.0.1-0.20181226105442-5d4384ee4fb2 // indirect
	github.com/redis/go-redis/v9 v9.17.2 // indirect
	github.com/rs/xid v1.6.0 // indirect
	github.com/rs/zerolog v1.34.0 // indirect
	github.com/second-state/WasmEdge-go v0.14.0 // indirect
	github.com/stretchr/objx v0.5.3 // indirect
	github.com/tetratelabs/wazero v1.11.0 // indirect
	golang.org/x/sync v0.19.0 // indirect
	golang.org/x/sys v0.40.0 // indirect
	gopkg.in/natefinch/lumberjack.v2 v2.2.1 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
	tokenDecoder v0.0.0-00010101000000-000000000000 // indirect
)
