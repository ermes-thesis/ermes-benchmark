package main

import (
	"wasm_integration_test/old_scripts/common"
)

func main() {
	fibFun(common.FibonacciInput)
}

func fibFun(n int) int {
	if n <= 1 {
		return n
	}
	return fibFun(n-1) + fibFun(n-2)
}
