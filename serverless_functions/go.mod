module ermes_benchmark

go 1.24.4

replace (
	github.com/ermes-thesis/ermes-common/model => ./../../ermes-common/model
	github.com/ermes-thesis/ermes-common/utils => ./../../ermes-common/utils
	github.com/ermes-thesis/ermes-sdk-go => ./../../ermes-sdk-go
)

require github.com/ermes-thesis/ermes-sdk-go v0.0.0-00010101000000-000000000000

require (
	github.com/ermes-thesis/ermes-common/model v0.0.0 // indirect
	github.com/ermes-thesis/ermes-common/utils v0.0.0 // indirect
	github.com/mitchellh/hashstructure/v2 v2.0.2 // indirect
)
