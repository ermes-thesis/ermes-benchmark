module empty_binary

go 1.24.0

toolchain go1.24.4

replace github.com/ermes-thesis/ermes-common/logger => ./../ermes-common/logger

replace github.com/ermes-thesis/ermes-common/wasm-pool => ./../ermes-common/wasm-pool

replace github.com/ermes-thesis/ermes-common/model => ./../ermes-common/model

replace github.com/ermes-thesis/ermes-common/utils => ./../ermes-common/utils

require (
	github.com/ermes-thesis/ermes-common/logger v0.0.0-00010101000000-000000000000
	github.com/ermes-thesis/ermes-common/wasm-pool v0.0.0-00010101000000-000000000000
	github.com/rs/zerolog v1.34.0
	github.com/second-state/WasmEdge-go v0.14.0
)

require (
	github.com/bytecodealliance/wasmtime-go/v37 v37.0.0 // indirect
	github.com/ermes-thesis/ermes-common/model v0.0.0-00010101000000-000000000000 // indirect
	github.com/ermes-thesis/ermes-common/utils v0.0.0-00010101000000-000000000000 // indirect
	github.com/mattn/go-colorable v0.1.14 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	github.com/mitchellh/hashstructure/v2 v2.0.2 // indirect
	github.com/tetratelabs/wazero v1.9.0 // indirect
	golang.org/x/sys v0.37.0 // indirect
	gopkg.in/natefinch/lumberjack.v2 v2.2.1 // indirect
)
