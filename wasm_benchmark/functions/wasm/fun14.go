package wasm_bench

import (
	"github.com/ermes-thesis/ermes-sdk-go"
)

//ermes:export
func fun14(req map[string]string, ctx ermes.Context) (int, any) {
	return 200, "ok14"
}
