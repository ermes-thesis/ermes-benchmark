package wasm_bench

import (
	"log"
	"strconv"

	"github.com/ermes-thesis/ermes-sdk-go"
)

func Fib(n int64) int64 {
	if n <= 1 {
		return n
	}
	return Fib(n-1) + Fib(n-2)
}

//ermes:export
func fibonacci(req map[string]string, ctx ermes.Context) (int, any) {
	nInt, err := strconv.ParseInt(req["n"], 10, 32)
	if err != nil {
		log.Fatal(err)
	}

	return 200, Fib(nInt)
}
