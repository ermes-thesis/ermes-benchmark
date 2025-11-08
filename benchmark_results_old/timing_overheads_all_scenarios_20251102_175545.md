# Combined Overhead Timing Results - All Scenarios
Generated: Sun Nov  2 19:15:59 CET 2025

Warmup Runs: 10 | Benchmark Runs: 20

---

## Scenario: PrimeNumbers

|:---|---:|---:|---:|---:|
| `./bin/overheads_wasmedge_interpreter_noopts_PrimeNumbers` | 161.3 ± 95.0 | 80.3 | 319.8 | 1.85 ± 1.10 |
| `./bin/overheads_wasmedge_interpreter_wopts_PrimeNumbers` | 87.2 ± 7.8 | 80.0 | 118.7 | 1.00 |
| `./bin/overheads_wasmedge_aot_noopts_PrimeNumbers` | 91.1 ± 20.8 | 79.9 | 177.7 | 1.04 ± 0.26 |
| `./bin/overheads_wasmedge_aot_wopts_PrimeNumbers` | 87.6 ± 10.5 | 78.8 | 128.7 | 1.00 ± 0.15 |
| `./bin/overheads_wasmtime_jit_noopts_PrimeNumbers` | 180.9 ± 56.1 | 135.7 | 364.3 | 2.07 ± 0.67 |
| `./bin/overheads_wasmtime_jit_wopts_PrimeNumbers` | 152.2 ± 9.4 | 130.7 | 173.2 | 1.74 ± 0.19 |
| `./bin/overheads_wazero_aot_noopts_PrimeNumbers` | 111.5 ± 5.5 | 101.0 | 126.5 | 1.28 ± 0.13 |
| `./bin/overheads_wazero_aot_wopts_PrimeNumbers` | 110.5 ± 5.5 | 95.9 | 120.2 | 1.27 ± 0.13 |
| `./bin/overheads_wazero_interpreter_noopts_PrimeNumbers` | 116.6 ± 5.9 | 104.8 | 123.0 | 1.34 ± 0.14 |
| `./bin/overheads_wazero_interpreter_wopts_PrimeNumbers` | 114.8 ± 13.0 | 94.9 | 154.4 | 1.32 ± 0.19 |

---

## Scenario: Fibonacci

|:---|---:|---:|---:|---:|
| `./bin/overheads_wasmedge_interpreter_noopts_Fibonacci` | 89.8 ± 20.1 | 78.6 | 173.7 | 1.04 ± 0.26 |
| `./bin/overheads_wasmedge_interpreter_wopts_Fibonacci` | 86.6 ± 9.7 | 76.0 | 117.4 | 1.00 |
| `./bin/overheads_wasmedge_aot_noopts_Fibonacci` | 92.9 ± 7.9 | 85.0 | 119.0 | 1.07 ± 0.15 |
| `./bin/overheads_wasmedge_aot_wopts_Fibonacci` | 88.9 ± 5.7 | 75.6 | 103.1 | 1.03 ± 0.13 |
| `./bin/overheads_wasmtime_jit_noopts_Fibonacci` | 149.0 ± 10.8 | 130.7 | 172.9 | 1.72 ± 0.23 |
| `./bin/overheads_wasmtime_jit_wopts_Fibonacci` | 154.4 ± 10.4 | 133.8 | 170.8 | 1.78 ± 0.23 |
| `./bin/overheads_wazero_aot_noopts_Fibonacci` | 110.7 ± 6.2 | 95.6 | 130.8 | 1.28 ± 0.16 |
| `./bin/overheads_wazero_aot_wopts_Fibonacci` | 112.5 ± 9.5 | 98.2 | 140.8 | 1.30 ± 0.18 |
| `./bin/overheads_wazero_interpreter_noopts_Fibonacci` | 113.8 ± 6.7 | 104.7 | 122.5 | 1.31 ± 0.17 |
| `./bin/overheads_wazero_interpreter_wopts_Fibonacci` | 98.9 ± 5.9 | 85.8 | 108.9 | 1.14 ± 0.14 |

---

## Scenario: Lightweight

|:---|---:|---:|---:|---:|
| `./bin/overheads_wasmedge_interpreter_noopts_Lightweight` | 79.8 ± 6.2 | 68.0 | 94.9 | 1.04 ± 0.13 |
| `./bin/overheads_wasmedge_interpreter_wopts_Lightweight` | 80.1 ± 14.3 | 68.8 | 134.3 | 1.04 ± 0.21 |
| `./bin/overheads_wasmedge_aot_noopts_Lightweight` | 82.6 ± 9.2 | 70.1 | 106.7 | 1.08 ± 0.16 |
| `./bin/overheads_wasmedge_aot_wopts_Lightweight` | 76.8 ± 7.3 | 68.3 | 100.7 | 1.00 |
| `./bin/overheads_wasmtime_jit_noopts_Lightweight` | 136.0 ± 8.0 | 119.8 | 151.6 | 1.77 ± 0.20 |
| `./bin/overheads_wasmtime_jit_wopts_Lightweight` | 138.7 ± 6.3 | 123.0 | 150.1 | 1.81 ± 0.19 |
| `./bin/overheads_wazero_aot_noopts_Lightweight` | 102.8 ± 9.7 | 90.7 | 138.8 | 1.34 ± 0.18 |
| `./bin/overheads_wazero_aot_wopts_Lightweight` | 101.2 ± 7.3 | 89.1 | 113.1 | 1.32 ± 0.16 |
| `./bin/overheads_wazero_interpreter_noopts_Lightweight` | 102.4 ± 11.6 | 87.3 | 141.0 | 1.33 ± 0.20 |
| `./bin/overheads_wazero_interpreter_wopts_Lightweight` | 101.0 ± 10.3 | 85.9 | 129.5 | 1.32 ± 0.18 |

---

## Scenario: TailFibonacci

|:---|---:|---:|---:|---:|
| `./bin/overheads_wasmedge_interpreter_noopts_TailFibonacci` | 132.4 ± 104.3 | 79.5 | 529.5 | 1.54 ± 1.21 |
| `./bin/overheads_wasmedge_interpreter_wopts_TailFibonacci` | 87.7 ± 6.9 | 78.0 | 113.2 | 1.02 ± 0.09 |
| `./bin/overheads_wasmedge_aot_noopts_TailFibonacci` | 86.5 ± 4.5 | 76.5 | 92.2 | 1.01 ± 0.07 |
| `./bin/overheads_wasmedge_aot_wopts_TailFibonacci` | 86.0 ± 4.1 | 76.2 | 94.1 | 1.00 |
| `./bin/overheads_wasmtime_jit_noopts_TailFibonacci` | 151.1 ± 8.4 | 132.1 | 166.0 | 1.76 ± 0.13 |
| `./bin/overheads_wasmtime_jit_wopts_TailFibonacci` | 153.7 ± 4.3 | 144.6 | 167.6 | 1.79 ± 0.10 |
| `./bin/overheads_wazero_aot_noopts_TailFibonacci` | 110.5 ± 9.0 | 97.4 | 138.5 | 1.29 ± 0.12 |
| `./bin/overheads_wazero_aot_wopts_TailFibonacci` | 112.4 ± 8.9 | 100.9 | 146.3 | 1.31 ± 0.12 |
| `./bin/overheads_wazero_interpreter_noopts_TailFibonacci` | 106.9 ± 4.3 | 95.9 | 112.7 | 1.24 ± 0.08 |
| `./bin/overheads_wazero_interpreter_wopts_TailFibonacci` | 106.2 ± 4.8 | 96.0 | 116.9 | 1.24 ± 0.08 |

---

