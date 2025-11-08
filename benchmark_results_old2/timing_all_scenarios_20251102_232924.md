# Combined Timing Results - All Scenarios
Generated: Mon Nov  3 01:32:54 CET 2025

Warmup Runs: 15 | Benchmark Runs: 30

---

## Scenario: PrimeNumbers

|:---|---:|---:|---:|---:|
| `./bin/native_PrimeNumbers` | 491.8 ± 5.1 | 482.3 | 504.0 | 1.48 ± 0.04 |
| `./bin/wasmedge_interpreter_noopts_PrimeNumbers` | 20477.0 ± 873.4 | 19478.7 | 22485.0 | 61.55 ± 2.98 |
| `./bin/wasmedge_interpreter_wopts_PrimeNumbers` | 11009.4 ± 242.2 | 10693.9 | 11666.5 | 33.09 ± 1.05 |
| `./bin/wasmedge_aot_noopts_PrimeNumbers` | 334.1 ± 5.5 | 324.0 | 346.4 | 1.00 ± 0.03 |
| `./bin/wasmedge_aot_wopts_PrimeNumbers` | 332.7 ± 7.7 | 319.7 | 356.6 | 1.00 |
| `./bin/wasmtime_jit_noopts_PrimeNumbers` | 597.4 ± 8.5 | 587.9 | 633.5 | 1.80 ± 0.05 |
| `./bin/wasmtime_jit_wopts_PrimeNumbers` | 596.2 ± 13.1 | 568.2 | 630.8 | 1.79 ± 0.06 |
| `./bin/wazero_aot_noopts_PrimeNumbers` | 802.3 ± 17.0 | 782.8 | 883.3 | 2.41 ± 0.08 |
| `./bin/wazero_aot_wopts_PrimeNumbers` | 653.5 ± 8.9 | 632.0 | 680.1 | 1.96 ± 0.05 |
| `./bin/wazero_interpreter_noopts_PrimeNumbers` | 22745.4 ± 156.1 | 22384.6 | 23066.5 | 68.37 ± 1.64 |
| `./bin/wazero_interpreter_wopts_PrimeNumbers` | 13067.4 ± 126.6 | 12773.6 | 13331.4 | 39.28 ± 0.98 |

---

## Scenario: Fibonacci

|:---|---:|---:|---:|---:|
| `./bin/native_Fibonacci` | 508.8 ± 4.1 | 500.9 | 517.1 | 1.47 ± 0.06 |
| `./bin/wasmedge_interpreter_noopts_Fibonacci` | 17906.1 ± 415.3 | 17246.3 | 18764.0 | 51.78 ± 2.44 |
| `./bin/wasmedge_interpreter_wopts_Fibonacci` | 17926.6 ± 339.6 | 17292.6 | 18584.6 | 51.84 ± 2.34 |
| `./bin/wasmedge_aot_noopts_Fibonacci` | 388.9 ± 9.2 | 369.5 | 405.8 | 1.12 ± 0.05 |
| `./bin/wasmedge_aot_wopts_Fibonacci` | 345.8 ± 14.2 | 327.3 | 391.3 | 1.00 |
| `./bin/wasmtime_jit_noopts_Fibonacci` | 488.8 ± 12.7 | 460.5 | 512.1 | 1.41 ± 0.07 |
| `./bin/wasmtime_jit_wopts_Fibonacci` | 501.4 ± 15.5 | 469.7 | 541.2 | 1.45 ± 0.07 |
| `./bin/wazero_aot_noopts_Fibonacci` | 676.0 ± 9.7 | 651.5 | 703.9 | 1.95 ± 0.08 |
| `./bin/wazero_aot_wopts_Fibonacci` | 657.3 ± 27.9 | 624.1 | 770.9 | 1.90 ± 0.11 |
| `./bin/wazero_interpreter_noopts_Fibonacci` | 20996.6 ± 164.6 | 20628.2 | 21364.4 | 60.71 ± 2.53 |
| `./bin/wazero_interpreter_wopts_Fibonacci` | 21935.5 ± 241.7 | 21537.5 | 22752.1 | 63.43 ± 2.69 |

---

## Scenario: Lightweight

|:---|---:|---:|---:|---:|
| `./bin/native_Lightweight` | 18.7 ± 1.2 | 15.9 | 21.3 | 1.00 |
| `./bin/wasmedge_interpreter_noopts_Lightweight` | 142.8 ± 5.7 | 129.6 | 151.6 | 7.65 ± 0.57 |
| `./bin/wasmedge_interpreter_wopts_Lightweight` | 96.6 ± 7.0 | 82.9 | 116.7 | 5.18 ± 0.49 |
| `./bin/wasmedge_aot_noopts_Lightweight` | 88.2 ± 4.5 | 75.8 | 96.6 | 4.73 ± 0.38 |
| `./bin/wasmedge_aot_wopts_Lightweight` | 86.9 ± 4.4 | 76.4 | 95.5 | 4.66 ± 0.37 |
| `./bin/wasmtime_jit_noopts_Lightweight` | 187.8 ± 18.3 | 158.4 | 252.4 | 10.07 ± 1.16 |
| `./bin/wasmtime_jit_wopts_Lightweight` | 167.3 ± 14.3 | 143.5 | 224.2 | 8.97 ± 0.95 |
| `./bin/wazero_aot_noopts_Lightweight` | 358.9 ± 13.3 | 338.8 | 400.3 | 19.24 ± 1.39 |
| `./bin/wazero_aot_wopts_Lightweight` | 222.8 ± 11.1 | 205.6 | 255.1 | 11.94 ± 0.95 |
| `./bin/wazero_interpreter_noopts_Lightweight` | 172.3 ± 8.7 | 158.5 | 192.3 | 9.24 ± 0.74 |
| `./bin/wazero_interpreter_wopts_Lightweight` | 115.0 ± 8.0 | 102.0 | 144.6 | 6.17 ± 0.58 |

---

## Scenario: TailFibonacci

|:---|---:|---:|---:|---:|
| `./bin/native_TailFibonacci` | 18.8 ± 1.1 | 16.3 | 21.1 | 1.00 |
| `./bin/wasmedge_interpreter_noopts_TailFibonacci` | 145.1 ± 4.0 | 135.8 | 158.1 | 7.70 ± 0.49 |
| `./bin/wasmedge_interpreter_wopts_TailFibonacci` | 92.0 ± 3.9 | 82.2 | 101.9 | 4.88 ± 0.34 |
| `./bin/wasmedge_aot_noopts_TailFibonacci` | 86.2 ± 3.2 | 76.8 | 90.4 | 4.57 ± 0.31 |
| `./bin/wasmedge_aot_wopts_TailFibonacci` | 86.2 ± 10.3 | 75.8 | 136.3 | 4.58 ± 0.60 |
| `./bin/wasmtime_jit_noopts_TailFibonacci` | 195.8 ± 15.0 | 172.6 | 253.2 | 10.40 ± 0.99 |
| `./bin/wasmtime_jit_wopts_TailFibonacci` | 187.2 ± 11.4 | 164.8 | 236.1 | 9.94 ± 0.83 |
| `./bin/wazero_aot_noopts_TailFibonacci` | 397.3 ± 85.7 | 345.3 | 666.7 | 21.09 ± 4.71 |
| `./bin/wazero_aot_wopts_TailFibonacci` | 242.7 ± 27.2 | 219.4 | 326.8 | 12.88 ± 1.62 |
| `./bin/wazero_interpreter_noopts_TailFibonacci` | 184.7 ± 6.5 | 172.2 | 198.8 | 9.81 ± 0.65 |
| `./bin/wazero_interpreter_wopts_TailFibonacci` | 126.5 ± 8.3 | 109.4 | 150.5 | 6.71 ± 0.58 |

---


================================================================================
# NET EXECUTION TIME (Total - Overhead)
================================================================================

This section shows the pure execution time after subtracting WASM runtime overhead.
Formula: NET Time = Total Execution Time - Overhead Time

## Scenario: PrimeNumbers

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  | 0.4917670806400001 |               N/A |          N/A |

---

## Scenario: Fibonacci

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  | 0.5088102176599999 |               N/A |          N/A |

---

## Scenario: Lightweight

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.01865380276 |               N/A |          N/A |

---

## Scenario: TailFibonacci

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  | 0.018837288373333334 |               N/A |          N/A |

---

