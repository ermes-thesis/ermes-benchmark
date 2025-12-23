package wasm_bench

import (
	"log"
	"strconv"

	"github.com/ermes-thesis/ermes-sdk-go"
)

func TailFib(n, a, b int64) int64 {
	if n == 0 {
		return a
	}
	return TailFib(n-1, b, a+b)
}

//ermes:export
func tailFibonacci(req map[string]string, ctx ermes.Context) (int, any) {
	nInt, err := strconv.ParseInt(req["n"], 10, 32)
	if err != nil {
		log.Fatal(err)
	}

	return 200, TailFib(nInt, 0, 1)
}
