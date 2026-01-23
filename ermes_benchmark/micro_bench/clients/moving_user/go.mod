module main

go 1.25.4

replace ermes_client_library => ../../../../../ermes-client-library/lib

replace (
	github.com/ermes-thesis/ermes-common/model => ../../../../../ermes-common/model
	github.com/ermes-thesis/ermes-common/utils => ../../../../../ermes-common/utils
)

require ermes_client_library v0.0.0-00010101000000-000000000000

require (
	github.com/ermes-thesis/ermes-common/model v0.0.0-00010101000000-000000000000 // indirect
	github.com/ermes-thesis/ermes-common/utils v0.0.0-00010101000000-000000000000 // indirect
	github.com/kr/pretty v0.3.1 // indirect
	github.com/mitchellh/hashstructure/v2 v2.0.2 // indirect
	github.com/rogpeppe/go-internal v1.10.0 // indirect
	gopkg.in/check.v1 v1.0.0-20201130134442-10cb98267c6c // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)
