# Combined Timing Results - All Scenarios
Generated: Tue Nov  4 15:29:13 CET 2025

Warmup Runs: 15 | Benchmark Runs: 20

---

## Scenario: PrimeNumbers

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_PrimeNumbers` | 470.2 ± 3.9 | 461.4 | 476.8 | 1.42 ± 0.04 |
| `./bin/wasmedge_interpreter_noopts_PrimeNumbers` | 18804.1 ± 483.4 | 18013.6 | 19679.8 | 56.66 ± 2.15 |
| `./bin/wasmedge_interpreter_wopts_PrimeNumbers` | 10323.3 ± 242.8 | 10040.4 | 10935.4 | 31.11 ± 1.14 |
| `./bin/wasmedge_aot_noopts_PrimeNumbers` | 332.8 ± 5.3 | 321.4 | 342.8 | 1.00 ± 0.03 |
| `./bin/wasmedge_aot_wopts_PrimeNumbers` | 331.8 ± 9.3 | 315.7 | 352.8 | 1.00 |
| `./bin/wasmtime_jit_noopts_PrimeNumbers` | 567.7 ± 11.9 | 548.5 | 611.1 | 1.71 ± 0.06 |
| `./bin/wasmtime_jit_wopts_PrimeNumbers` | 569.7 ± 13.2 | 549.1 | 615.5 | 1.72 ± 0.06 |
| `./bin/wazero_aot_noopts_PrimeNumbers` | 750.5 ± 7.0 | 737.4 | 761.6 | 2.26 ± 0.07 |
| `./bin/wazero_aot_wopts_PrimeNumbers` | 611.4 ± 9.8 | 599.0 | 642.9 | 1.84 ± 0.06 |
| `./bin/wazero_interpreter_noopts_PrimeNumbers` | 21224.3 ± 286.6 | 20739.4 | 21674.9 | 63.96 ± 1.99 |
| `./bin/wazero_interpreter_wopts_PrimeNumbers` | 12233.3 ± 126.8 | 11997.9 | 12476.0 | 36.86 ± 1.10 |

---

## Scenario: Fibonacci

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_Fibonacci` | 484.6 ± 4.4 | 480.2 | 499.9 | 1.53 ± 0.04 |
| `./bin/wasmedge_interpreter_noopts_Fibonacci` | 16749.7 ± 595.1 | 16059.4 | 18792.4 | 52.81 ± 2.22 |
| `./bin/wasmedge_interpreter_wopts_Fibonacci` | 16604.8 ± 199.8 | 16296.3 | 16999.8 | 52.35 ± 1.33 |
| `./bin/wasmedge_aot_noopts_Fibonacci` | 401.6 ± 91.0 | 351.0 | 712.1 | 1.27 ± 0.29 |
| `./bin/wasmedge_aot_wopts_Fibonacci` | 317.2 ± 7.1 | 308.1 | 337.4 | 1.00 |
| `./bin/wasmtime_jit_noopts_Fibonacci` | 447.3 ± 8.6 | 426.7 | 459.9 | 1.41 ± 0.04 |
| `./bin/wasmtime_jit_wopts_Fibonacci` | 466.6 ± 4.3 | 455.0 | 473.7 | 1.47 ± 0.04 |
| `./bin/wazero_aot_noopts_Fibonacci` | 638.4 ± 10.3 | 620.9 | 659.5 | 2.01 ± 0.06 |
| `./bin/wazero_aot_wopts_Fibonacci` | 640.2 ± 64.2 | 608.1 | 849.5 | 2.02 ± 0.21 |
| `./bin/wazero_interpreter_noopts_Fibonacci` | 19475.6 ± 251.2 | 18950.3 | 19928.9 | 61.40 ± 1.58 |
| `./bin/wazero_interpreter_wopts_Fibonacci` | 20443.9 ± 271.9 | 20002.4 | 20969.6 | 64.45 ± 1.67 |

---

## Scenario: Lightweight

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_Lightweight` | 18.7 ± 5.9 | 16.6 | 43.5 | 1.00 |
| `./bin/wasmedge_interpreter_noopts_Lightweight` | 127.9 ± 4.2 | 120.3 | 140.7 | 6.85 ± 2.18 |
| `./bin/wasmedge_interpreter_wopts_Lightweight` | 124.9 ± 99.9 | 80.7 | 383.8 | 6.69 ± 5.75 |
| `./bin/wasmedge_aot_noopts_Lightweight` | 92.6 ± 36.4 | 70.0 | 196.6 | 4.96 ± 2.50 |
| `./bin/wasmedge_aot_wopts_Lightweight` | 89.2 ± 32.7 | 69.6 | 219.9 | 4.78 ± 2.32 |
| `./bin/wasmtime_jit_noopts_Lightweight` | 166.6 ± 6.8 | 152.2 | 186.4 | 8.92 ± 2.85 |
| `./bin/wasmtime_jit_wopts_Lightweight` | 169.3 ± 15.5 | 142.5 | 198.6 | 9.07 ± 2.99 |
| `./bin/wazero_aot_noopts_Lightweight` | 341.1 ± 10.8 | 326.1 | 376.3 | 18.26 ± 5.82 |
| `./bin/wazero_aot_wopts_Lightweight` | 205.8 ± 8.4 | 182.3 | 218.2 | 11.02 ± 3.52 |
| `./bin/wazero_interpreter_noopts_Lightweight` | 168.2 ± 6.1 | 155.6 | 186.3 | 9.00 ± 2.87 |
| `./bin/wazero_interpreter_wopts_Lightweight` | 118.2 ± 6.8 | 111.6 | 144.0 | 6.33 ± 2.04 |

---

## Scenario: TailFibonacci

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_TailFibonacci` | 19.8 ± 1.1 | 17.0 | 20.7 | 1.00 |
| `./bin/wasmedge_interpreter_noopts_TailFibonacci` | 141.0 ± 8.6 | 125.1 | 167.1 | 7.13 ± 0.58 |
| `./bin/wasmedge_interpreter_wopts_TailFibonacci` | 102.1 ± 8.2 | 87.2 | 116.8 | 5.16 ± 0.50 |
| `./bin/wasmedge_aot_noopts_TailFibonacci` | 87.2 ± 4.5 | 78.2 | 91.3 | 4.41 ± 0.33 |
| `./bin/wasmedge_aot_wopts_TailFibonacci` | 84.8 ± 4.9 | 75.0 | 94.8 | 4.29 ± 0.34 |
| `./bin/wasmtime_jit_noopts_TailFibonacci` | 195.8 ± 19.0 | 172.2 | 264.9 | 9.90 ± 1.10 |
| `./bin/wasmtime_jit_wopts_TailFibonacci` | 180.3 ± 12.4 | 161.4 | 213.9 | 9.12 ± 0.80 |
| `./bin/wazero_aot_noopts_TailFibonacci` | 359.4 ± 12.9 | 342.1 | 393.6 | 18.18 ± 1.19 |
| `./bin/wazero_aot_wopts_TailFibonacci` | 227.3 ± 11.5 | 201.4 | 253.0 | 11.50 ± 0.86 |
| `./bin/wazero_interpreter_noopts_TailFibonacci` | 168.0 ± 9.7 | 152.4 | 204.0 | 8.50 ± 0.67 |
| `./bin/wazero_interpreter_wopts_TailFibonacci` | 117.4 ± 6.2 | 106.4 | 133.7 | 5.94 ± 0.45 |

---


================================================================================
# NET EXECUTION TIME (Total - Overhead)
================================================================================

This section shows the pure execution time after subtracting WASM runtime overhead.
Formula: NET Time = Total Execution Time - Overhead Time

## Scenario: PrimeNumbers

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.47015786564999995 |               N/A |          N/A |
| Wasmedge_Interpreter_NoOpts                             |      18.804050 |          0.081666 |    18.722384 |
| Wasmedge_Interpreter_WithOpts                           |      10.323291 |          0.078942 |    10.244349 |
| Wasmedge_AOT_NoOpts                                     |       0.332783 |          0.085466 |     0.247316 |
| Wasmedge_AOT_WithOpts                                   |       0.331847 |          0.080294 |     0.251554 |
| Wasmtime_JIT_NoOpts                                     |       0.567655 |          0.140204 |     0.427451 |
| Wasmtime_JIT_WithOpts                                   |       0.569682 |          0.143119 |     0.426564 |
| Wazero_AOT_NoOpts                                       |       0.750529 |          0.103078 |     0.647451 |
| Wazero_AOT_WithOpts                                     |       0.611390 |          0.106250 |     0.505140 |
| Wazero_Interpreter_NoOpts                               |      21.224347 |          0.099758 |    21.124589 |
| Wazero_Interpreter_WithOpts                             |      12.233330 |          0.106261 |    12.127069 |

---

## Scenario: Fibonacci

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.48463182195000004 |               N/A |          N/A |
| Wasmedge_Interpreter_NoOpts                             |      16.749657 |          0.077394 |    16.672263 |
| Wasmedge_Interpreter_WithOpts                           |      16.604843 |          0.072350 |    16.532492 |
| Wasmedge_AOT_NoOpts                                     |       0.401640 |          0.073273 |     0.328367 |
| Wasmedge_AOT_WithOpts                                   |       0.317187 |          0.071902 |     0.245285 |
| Wasmtime_JIT_NoOpts                                     |       0.447344 |          0.127065 |     0.320279 |
| Wasmtime_JIT_WithOpts                                   |       0.466567 |          0.124807 |     0.341760 |
| Wazero_AOT_NoOpts                                       |       0.638450 |          0.098172 |     0.540278 |
| Wazero_AOT_WithOpts                                     |       0.640162 |          0.094048 |     0.546114 |
| Wazero_Interpreter_NoOpts                               |      19.475560 |          0.093108 |    19.382453 |
| Wazero_Interpreter_WithOpts                             |      20.443941 |          0.117126 |    20.326815 |

---

## Scenario: Lightweight

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.01867845554 |               N/A |          N/A |
| Wasmedge_Interpreter_NoOpts                             |       0.127946 |          0.088758 |     0.039188 |
| Wasmedge_Interpreter_WithOpts                           |       0.124868 |          0.077123 |     0.047745 |
| Wasmedge_AOT_NoOpts                                     |       0.092617 |          0.082009 |     0.010608 |
| Wasmedge_AOT_WithOpts                                   |       0.089205 |          0.081775 |     0.007430 |
| Wasmtime_JIT_NoOpts                                     |       0.166649 |          0.144012 |     0.022637 |
| Wasmtime_JIT_WithOpts                                   |       0.169328 |          0.157258 |     0.012071 |
| Wazero_AOT_NoOpts                                       |       0.341105 |          0.099264 |     0.241841 |
| Wazero_AOT_WithOpts                                     |       0.205811 |          0.175521 |     0.030290 |
| Wazero_Interpreter_NoOpts                               |       0.168158 |          0.094355 |     0.073803 |
| Wazero_Interpreter_WithOpts                             |       0.118183 |          0.095799 |     0.022383 |

---

## Scenario: TailFibonacci

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.01977318778 |               N/A |          N/A |
| Wasmedge_Interpreter_NoOpts                             |       0.140961 |          0.084510 |     0.056451 |
| Wasmedge_Interpreter_WithOpts                           |       0.102054 |          0.081289 |     0.020765 |
| Wasmedge_AOT_NoOpts                                     |       0.087155 |          0.084049 |     0.003106 |
| Wasmedge_AOT_WithOpts                                   |       0.084796 |          0.099822 |    -0.015025 |
| Wasmtime_JIT_NoOpts                                     |       0.195824 |          0.154679 |     0.041145 |
| Wasmtime_JIT_WithOpts                                   |       0.180287 |          0.137746 |     0.042541 |
| Wazero_AOT_NoOpts                                       |       0.359396 |          0.136130 |     0.223266 |
| Wazero_AOT_WithOpts                                     |       0.227312 |          0.097189 |     0.130123 |
| Wazero_Interpreter_NoOpts                               |       0.167974 |          0.097047 |     0.070928 |
| Wazero_Interpreter_WithOpts                             |       0.117444 |          0.094824 |     0.022620 |

---

