module main

go 1.25.4

replace ermes_client_library => ../../../../ermes-client-library/lib

replace (
	github.com/ermes-thesis/ermes-common/logger => ../../../../ermes-common/logger
	github.com/ermes-thesis/ermes-common/model => ../../../../ermes-common/model
	github.com/ermes-thesis/ermes-common/utils => ../../../../ermes-common/utils
)

require (
	ermes_client_library v0.0.0-00010101000000-000000000000
	github.com/ermes-thesis/ermes-common/logger v0.0.0-00010101000000-000000000000
)

require (
	github.com/ermes-thesis/ermes-common/model v0.0.0-00010101000000-000000000000 // indirect
	github.com/ermes-thesis/ermes-common/utils v0.0.0-00010101000000-000000000000 // indirect
	github.com/mattn/go-colorable v0.1.14 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	github.com/mitchellh/hashstructure/v2 v2.0.2 // indirect
	github.com/rs/zerolog v1.34.0 // indirect
	golang.org/x/sys v0.40.0 // indirect
	gopkg.in/natefinch/lumberjack.v2 v2.2.1 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)
