package wasm_bench

import (
	"github.com/ermes-thesis/ermes-sdk-go"
)

//ermes:export
func fun10(req map[string]string, ctx ermes.Context) (int, any) {
	return 200, "ok10"
}
