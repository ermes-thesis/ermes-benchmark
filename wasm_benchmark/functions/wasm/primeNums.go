package wasm_bench

import (
	"log"
	"strconv"

	"github.com/ermes-thesis/ermes-sdk-go"
)

func ComputePrimes(n int64) int {
	count := 0
	for i := int64(2); i <= n; i++ {
		isPrime := true
		for j := int64(2); j*j <= i; j++ {
			if i%j == 0 {
				isPrime = false
				break
			}
		}
		if isPrime {
			count++
		}
	}
	return count
}

//ermes:export
func primeNums(req map[string]string, ctx ermes.Context) (int, any) {
	nInt, err := strconv.ParseInt(req["n"], 10, 32)
	if err != nil {
		log.Fatal(err)
	}

	res := ComputePrimes(nInt)

	return 200, res
}
