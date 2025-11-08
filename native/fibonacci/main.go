package main

import (
	"empty_binary/common"
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
