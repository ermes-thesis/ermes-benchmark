# Combined Timing Results - All Scenarios
Generated: Mon Nov  3 13:56:54 CET 2025

Warmup Runs: 15 | Benchmark Runs: 20

---

## Scenario: PrimeNumbers

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_PrimeNumbers` | 496.5 ± 7.9 | 479.4 | 506.7 | 1.48 ± 0.03 |
| `./bin/wasmedge_interpreter_noopts_PrimeNumbers` | 19651.6 ± 392.6 | 19022.7 | 20256.7 | 58.78 ± 1.55 |
| `./bin/wasmedge_interpreter_wopts_PrimeNumbers` | 10825.7 ± 267.1 | 10366.3 | 11372.4 | 32.38 ± 0.98 |
| `./bin/wasmedge_aot_noopts_PrimeNumbers` | 346.1 ± 6.4 | 332.7 | 359.0 | 1.04 ± 0.03 |
| `./bin/wasmedge_aot_wopts_PrimeNumbers` | 334.3 ± 5.8 | 323.7 | 346.4 | 1.00 |
| `./bin/wasmtime_jit_noopts_PrimeNumbers` | 599.1 ± 12.4 | 582.2 | 643.7 | 1.79 ± 0.05 |
| `./bin/wasmtime_jit_wopts_PrimeNumbers` | 599.0 ± 7.8 | 576.7 | 611.2 | 1.79 ± 0.04 |
| `./bin/wazero_aot_noopts_PrimeNumbers` | 795.6 ± 18.8 | 766.8 | 826.3 | 2.38 ± 0.07 |
| `./bin/wazero_aot_wopts_PrimeNumbers` | 637.5 ± 5.8 | 621.6 | 644.2 | 1.91 ± 0.04 |
| `./bin/wazero_interpreter_noopts_PrimeNumbers` | 22200.2 ± 269.3 | 21691.2 | 22592.8 | 66.40 ± 1.40 |
| `./bin/wazero_interpreter_wopts_PrimeNumbers` | 12673.6 ± 156.8 | 12368.6 | 12894.4 | 37.91 ± 0.81 |

---

## Scenario: Fibonacci

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_Fibonacci` | 499.4 ± 4.2 | 493.8 | 509.2 | 1.47 ± 0.05 |
| `./bin/wasmedge_interpreter_noopts_Fibonacci` | 17290.3 ± 285.5 | 16945.2 | 17919.4 | 50.97 ± 1.95 |
| `./bin/wasmedge_interpreter_wopts_Fibonacci` | 17393.3 ± 401.7 | 16902.6 | 18579.7 | 51.27 ± 2.13 |
| `./bin/wasmedge_aot_noopts_Fibonacci` | 374.9 ± 6.3 | 364.7 | 386.0 | 1.11 ± 0.04 |
| `./bin/wasmedge_aot_wopts_Fibonacci` | 339.2 ± 11.7 | 328.1 | 382.7 | 1.00 |
| `./bin/wasmtime_jit_noopts_Fibonacci` | 462.6 ± 9.7 | 442.6 | 475.5 | 1.36 ± 0.06 |
| `./bin/wasmtime_jit_wopts_Fibonacci` | 489.9 ± 16.0 | 463.2 | 542.2 | 1.44 ± 0.07 |
| `./bin/wazero_aot_noopts_Fibonacci` | 672.3 ± 11.4 | 644.8 | 692.6 | 1.98 ± 0.08 |
| `./bin/wazero_aot_wopts_Fibonacci` | 644.2 ± 11.1 | 623.4 | 663.0 | 1.90 ± 0.07 |
| `./bin/wazero_interpreter_noopts_Fibonacci` | 20402.9 ± 190.3 | 20094.6 | 20679.8 | 60.15 ± 2.15 |
| `./bin/wazero_interpreter_wopts_Fibonacci` | 21259.9 ± 150.4 | 20824.4 | 21568.4 | 62.67 ± 2.21 |

---

## Scenario: Lightweight

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_Lightweight` | 20.1 ± 3.5 | 17.5 | 28.4 | 1.00 |
| `./bin/wasmedge_interpreter_noopts_Lightweight` | 135.4 ± 4.6 | 126.2 | 144.7 | 6.74 ± 1.19 |
| `./bin/wasmedge_interpreter_wopts_Lightweight` | 88.2 ± 4.0 | 81.1 | 98.9 | 4.39 ± 0.78 |
| `./bin/wasmedge_aot_noopts_Lightweight` | 81.1 ± 4.4 | 72.1 | 88.4 | 4.04 ± 0.73 |
| `./bin/wasmedge_aot_wopts_Lightweight` | 77.9 ± 3.9 | 69.9 | 85.8 | 3.88 ± 0.70 |
| `./bin/wasmtime_jit_noopts_Lightweight` | 176.0 ± 14.5 | 155.5 | 219.3 | 8.77 ± 1.68 |
| `./bin/wasmtime_jit_wopts_Lightweight` | 172.6 ± 20.2 | 149.4 | 241.4 | 8.60 ± 1.80 |
| `./bin/wazero_aot_noopts_Lightweight` | 363.1 ± 9.2 | 347.9 | 385.5 | 18.09 ± 3.16 |
| `./bin/wazero_aot_wopts_Lightweight` | 217.9 ± 10.0 | 199.3 | 235.0 | 10.85 ± 1.94 |
| `./bin/wazero_interpreter_noopts_Lightweight` | 172.9 ± 15.6 | 156.5 | 217.7 | 8.61 ± 1.68 |
| `./bin/wazero_interpreter_wopts_Lightweight` | 119.0 ± 12.3 | 103.8 | 162.0 | 5.93 ± 1.19 |

---

## Scenario: TailFibonacci

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_TailFibonacci` | 19.5 ± 3.3 | 16.7 | 33.0 | 1.00 |
| `./bin/wasmedge_interpreter_noopts_TailFibonacci` | 145.3 ± 7.3 | 132.2 | 168.8 | 7.44 ± 1.32 |
| `./bin/wasmedge_interpreter_wopts_TailFibonacci` | 95.0 ± 4.2 | 84.1 | 100.2 | 4.86 ± 0.85 |
| `./bin/wasmedge_aot_noopts_TailFibonacci` | 90.3 ± 4.9 | 81.7 | 102.7 | 4.63 ± 0.83 |
| `./bin/wasmedge_aot_wopts_TailFibonacci` | 85.2 ± 3.9 | 78.4 | 90.8 | 4.36 ± 0.77 |
| `./bin/wasmtime_jit_noopts_TailFibonacci` | 188.7 ± 11.3 | 166.6 | 219.2 | 9.67 ± 1.74 |
| `./bin/wasmtime_jit_wopts_TailFibonacci` | 190.0 ± 6.3 | 175.6 | 205.5 | 9.73 ± 1.68 |
| `./bin/wazero_aot_noopts_TailFibonacci` | 370.9 ± 12.6 | 353.6 | 404.5 | 18.99 ± 3.29 |
| `./bin/wazero_aot_wopts_TailFibonacci` | 233.3 ± 9.0 | 210.7 | 247.5 | 11.95 ± 2.08 |
| `./bin/wazero_interpreter_noopts_TailFibonacci` | 177.4 ± 6.1 | 163.9 | 193.2 | 9.08 ± 1.57 |
| `./bin/wazero_interpreter_wopts_TailFibonacci` | 129.5 ± 6.5 | 115.7 | 143.7 | 6.63 ± 1.17 |

---


================================================================================
# NET EXECUTION TIME (Total - Overhead)
================================================================================

This section shows the pure execution time after subtracting WASM runtime overhead.
Formula: NET Time = Total Execution Time - Overhead Time

## Scenario: PrimeNumbers

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.49647083727999985 |               N/A |          N/A |
| Wasmedge_Interpreter_NoOpts                             |      19.651584 |          0.083519 |    19.568065 |
| Wasmedge_Interpreter_WithOpts                           |      10.825684 |          0.084311 |    10.741373 |
| Wasmedge_AOT_NoOpts                                     |       0.346124 |          0.088554 |     0.257570 |
| Wasmedge_AOT_WithOpts                                   |       0.334332 |          0.083679 |     0.250653 |
| Wasmtime_JIT_NoOpts                                     |       0.599081 |          0.153082 |     0.445999 |
| Wasmtime_JIT_WithOpts                                   |       0.599014 |          0.150683 |     0.448331 |
| Wazero_AOT_NoOpts                                       |       0.795585 |          0.105452 |     0.690133 |
| Wazero_AOT_WithOpts                                     |       0.637461 |          0.109754 |     0.527707 |
| Wazero_Interpreter_NoOpts                               |      22.200186 |          0.108808 |    22.091378 |
| Wazero_Interpreter_WithOpts                             |      12.673635 |          0.110858 |    12.562777 |

---

## Scenario: Fibonacci

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.4994175371600001 |               N/A |          N/A |
| Wasmedge_Interpreter_NoOpts                             |      17.290303 |          0.130078 |    17.160225 |
| Wasmedge_Interpreter_WithOpts                           |      17.393292 |          0.089707 |    17.303584 |
| Wasmedge_AOT_NoOpts                                     |       0.374863 |          0.081354 |     0.293509 |
| Wasmedge_AOT_WithOpts                                   |       0.339224 |          0.077952 |     0.261272 |
| Wasmtime_JIT_NoOpts                                     |       0.462643 |          0.132099 |     0.330544 |
| Wasmtime_JIT_WithOpts                                   |       0.489861 |          0.131859 |     0.358002 |
| Wazero_AOT_NoOpts                                       |       0.672318 |          0.097504 |     0.574815 |
| Wazero_AOT_WithOpts                                     |       0.644243 |          0.098628 |     0.545615 |
| Wazero_Interpreter_NoOpts                               |      20.402886 |          0.095867 |    20.307019 |
| Wazero_Interpreter_WithOpts                             |      21.259937 |          0.105376 |    21.154561 |

---

## Scenario: Lightweight

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.020078083830000003 |               N/A |          N/A |
| Wasmedge_Interpreter_NoOpts                             |       0.135406 |          0.081859 |     0.053547 |
| Wasmedge_Interpreter_WithOpts                           |       0.088161 |          0.083391 |     0.004770 |
| Wasmedge_AOT_NoOpts                                     |       0.081120 |          0.083030 |    -0.001909 |
| Wasmedge_AOT_WithOpts                                   |       0.077923 |          0.079853 |    -0.001930 |
| Wasmtime_JIT_NoOpts                                     |       0.175992 |          0.140576 |     0.035416 |
| Wasmtime_JIT_WithOpts                                   |       0.172644 |          0.138491 |     0.034153 |
| Wazero_AOT_NoOpts                                       |       0.363125 |          0.105187 |     0.257938 |
| Wazero_AOT_WithOpts                                     |       0.217910 |          0.110204 |     0.107707 |
| Wazero_Interpreter_NoOpts                               |       0.172890 |          0.102819 |     0.070070 |
| Wazero_Interpreter_WithOpts                             |       0.118975 |          0.102159 |     0.016816 |

---

## Scenario: TailFibonacci

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.01952649315 |               N/A |          N/A |
| Wasmedge_Interpreter_NoOpts                             |       0.145328 |          0.084839 |     0.060489 |
| Wasmedge_Interpreter_WithOpts                           |       0.094975 |          0.081432 |     0.013542 |
| Wasmedge_AOT_NoOpts                                     |       0.090313 |          0.083509 |     0.006804 |
| Wasmedge_AOT_WithOpts                                   |       0.085203 |          0.086919 |    -0.001715 |
| Wasmtime_JIT_NoOpts                                     |       0.188745 |          0.145961 |     0.042784 |
| Wasmtime_JIT_WithOpts                                   |       0.190016 |          0.146514 |     0.043502 |
| Wazero_AOT_NoOpts                                       |       0.370851 |          0.112556 |     0.258295 |
| Wazero_AOT_WithOpts                                     |       0.233253 |          0.113562 |     0.119691 |
| Wazero_Interpreter_NoOpts                               |       0.177377 |          0.111279 |     0.066098 |
| Wazero_Interpreter_WithOpts                             |       0.129499 |          0.107591 |     0.021908 |

---

