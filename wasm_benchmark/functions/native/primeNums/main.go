package main

import (
	"wasm_benchmark/_old_scripts/common"
)

func main() {
	count := 0
	for i := 2; i <= common.PrimeNumsInput; i++ {
		isPrime := true
		for j := 2; j*j <= i; j++ {
			if i%j == 0 {
				isPrime = false
				break
			}
		}
		if isPrime {
			count++
		}
	}
}
