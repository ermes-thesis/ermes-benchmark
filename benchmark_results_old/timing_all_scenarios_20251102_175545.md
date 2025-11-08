# Combined Timing Results - All Scenarios
Generated: Sun Nov  2 19:15:59 CET 2025

Warmup Runs: 10 | Benchmark Runs: 20

---

## Scenario: PrimeNumbers

|:---|---:|---:|---:|---:|
| `./bin/native_PrimeNumbers` | 511.3 ± 6.0 | 502.5 | 526.7 | 1.44 ± 0.03 |
| `./bin/wasmedge_interpreter_noopts_PrimeNumbers` | 20075.8 ± 394.8 | 19577.1 | 20989.7 | 56.69 ± 1.54 |
| `./bin/wasmedge_interpreter_wopts_PrimeNumbers` | 10930.3 ± 233.2 | 10684.3 | 11355.8 | 30.87 ± 0.87 |
| `./bin/wasmedge_aot_noopts_PrimeNumbers` | 354.8 ± 6.1 | 344.6 | 371.7 | 1.00 ± 0.03 |
| `./bin/wasmedge_aot_wopts_PrimeNumbers` | 354.1 ± 6.6 | 341.5 | 365.8 | 1.00 |
| `./bin/wasmtime_jit_noopts_PrimeNumbers` | 650.8 ± 23.8 | 619.2 | 740.1 | 1.84 ± 0.08 |
| `./bin/wasmtime_jit_wopts_PrimeNumbers` | 633.8 ± 19.7 | 606.0 | 697.8 | 1.79 ± 0.06 |
| `./bin/wazero_aot_noopts_PrimeNumbers` | 827.6 ± 12.1 | 800.5 | 852.1 | 2.34 ± 0.06 |
| `./bin/wazero_aot_wopts_PrimeNumbers` | 671.5 ± 7.6 | 654.9 | 684.0 | 1.90 ± 0.04 |
| `./bin/wazero_interpreter_noopts_PrimeNumbers` | 22534.1 ± 193.3 | 22180.0 | 22847.9 | 63.63 ± 1.30 |
| `./bin/wazero_interpreter_wopts_PrimeNumbers` | 12939.4 ± 135.4 | 12713.8 | 13162.5 | 36.54 ± 0.78 |

---

## Scenario: Fibonacci

|:---|---:|---:|---:|---:|
| `./bin/native_Fibonacci` | 518.2 ± 2.2 | 515.9 | 525.9 | 1.54 ± 0.02 |
| `./bin/wasmedge_interpreter_noopts_Fibonacci` | 17687.3 ± 324.9 | 17256.8 | 18357.5 | 52.56 ± 1.25 |
| `./bin/wasmedge_interpreter_wopts_Fibonacci` | 17708.0 ± 226.5 | 17374.9 | 18189.9 | 52.62 ± 1.04 |
| `./bin/wasmedge_aot_noopts_Fibonacci` | 392.2 ± 9.4 | 380.4 | 424.6 | 1.17 ± 0.03 |
| `./bin/wasmedge_aot_wopts_Fibonacci` | 336.5 ± 5.1 | 326.2 | 344.3 | 1.00 |
| `./bin/wasmtime_jit_noopts_Fibonacci` | 478.0 ± 7.0 | 464.1 | 486.8 | 1.42 ± 0.03 |
| `./bin/wasmtime_jit_wopts_Fibonacci` | 495.9 ± 12.9 | 473.3 | 537.2 | 1.47 ± 0.04 |
| `./bin/wazero_aot_noopts_Fibonacci` | 676.5 ± 9.3 | 654.8 | 698.7 | 2.01 ± 0.04 |
| `./bin/wazero_aot_wopts_Fibonacci` | 655.8 ± 9.3 | 638.8 | 672.0 | 1.95 ± 0.04 |
| `./bin/wazero_interpreter_noopts_Fibonacci` | 20691.7 ± 165.1 | 20421.7 | 21015.4 | 61.48 ± 1.05 |
| `./bin/wazero_interpreter_wopts_Fibonacci` | 21739.9 ± 263.6 | 21381.5 | 22307.1 | 64.60 ± 1.26 |

---

## Scenario: Lightweight

|:---|---:|---:|---:|---:|
| `./bin/native_Lightweight` | 19.5 ± 3.1 | 15.0 | 26.3 | 1.00 |
| `./bin/wasmedge_interpreter_noopts_Lightweight` | 137.4 ± 3.9 | 127.7 | 143.1 | 7.05 ± 1.16 |
| `./bin/wasmedge_interpreter_wopts_Lightweight` | 90.6 ± 6.6 | 79.1 | 105.1 | 4.65 ± 0.83 |
| `./bin/wasmedge_aot_noopts_Lightweight` | 83.7 ± 6.0 | 77.7 | 105.3 | 4.30 ± 0.76 |
| `./bin/wasmedge_aot_wopts_Lightweight` | 81.9 ± 8.9 | 72.0 | 116.1 | 4.20 ± 0.82 |
| `./bin/wasmtime_jit_noopts_Lightweight` | 179.2 ± 9.5 | 157.6 | 200.0 | 9.20 ± 1.57 |
| `./bin/wasmtime_jit_wopts_Lightweight` | 172.0 ± 14.6 | 149.0 | 218.9 | 8.83 ± 1.61 |
| `./bin/wazero_aot_noopts_Lightweight` | 364.1 ± 22.4 | 337.7 | 421.5 | 18.70 ± 3.24 |
| `./bin/wazero_aot_wopts_Lightweight` | 222.3 ± 5.5 | 213.3 | 230.7 | 11.41 ± 1.87 |
| `./bin/wazero_interpreter_noopts_Lightweight` | 264.4 ± 134.4 | 159.4 | 547.5 | 13.58 ± 7.24 |
| `./bin/wazero_interpreter_wopts_Lightweight` | 137.8 ± 52.3 | 107.8 | 314.0 | 7.07 ± 2.92 |

---

## Scenario: TailFibonacci

|:---|---:|---:|---:|---:|
| `./bin/native_TailFibonacci` | 20.7 ± 3.7 | 15.5 | 27.5 | 1.00 |
| `./bin/wasmedge_interpreter_noopts_TailFibonacci` | 141.5 ± 6.1 | 133.2 | 154.1 | 6.83 ± 1.27 |
| `./bin/wasmedge_interpreter_wopts_TailFibonacci` | 95.6 ± 7.1 | 85.8 | 119.2 | 4.61 ± 0.90 |
| `./bin/wasmedge_aot_noopts_TailFibonacci` | 89.7 ± 3.0 | 79.7 | 93.6 | 4.33 ± 0.80 |
| `./bin/wasmedge_aot_wopts_TailFibonacci` | 87.2 ± 7.6 | 76.3 | 113.7 | 4.21 ± 0.85 |
| `./bin/wasmtime_jit_noopts_TailFibonacci` | 189.8 ± 9.3 | 169.7 | 203.5 | 9.17 ± 1.72 |
| `./bin/wasmtime_jit_wopts_TailFibonacci` | 185.8 ± 8.6 | 162.5 | 201.6 | 8.97 ± 1.68 |
| `./bin/wazero_aot_noopts_TailFibonacci` | 372.5 ± 14.2 | 347.1 | 404.8 | 17.99 ± 3.33 |
| `./bin/wazero_aot_wopts_TailFibonacci` | 238.3 ± 16.0 | 215.7 | 295.4 | 11.51 ± 2.22 |
| `./bin/wazero_interpreter_noopts_TailFibonacci` | 185.9 ± 7.6 | 168.4 | 202.2 | 8.97 ± 1.66 |
| `./bin/wazero_interpreter_wopts_TailFibonacci` | 126.2 ± 7.3 | 112.3 | 137.6 | 6.09 ± 1.16 |

---

