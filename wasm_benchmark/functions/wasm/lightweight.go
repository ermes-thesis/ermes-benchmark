package wasm_bench

import (
	"log"
	"strconv"

	"github.com/ermes-thesis/ermes-sdk-go"
)

func simpleFun(n int64) int {
	count := 0
	for i := int64(0); i <= n; i++ {
		count++
	}
	return count
}

//ermes:export
func lightweight(req map[string]string, ctx ermes.Context) (int, any) {
	nInt, err := strconv.ParseInt(req["n"], 10, 32)
	if err != nil {
		log.Fatal(err)
	}

	res := simpleFun(nInt)

	return 200, res
}
