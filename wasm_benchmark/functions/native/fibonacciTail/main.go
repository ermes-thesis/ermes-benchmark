package main

import (
	"wasm_integration_test/_old_scripts/common"
)

func main() {
	fibTailFun(common.FibonacciTailInput, 0, 1)
}

func fibTailFun(n, a, b int) int {
	if n == 0 {
		return a
	}
	return fibTailFun(n-1, b, a+b)
}
