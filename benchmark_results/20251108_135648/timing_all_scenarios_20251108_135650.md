# Combined Timing Results - All Scenarios
Generated: Sat Nov  8 13:57:42 CET 2025

Warmup Runs: 1 | Benchmark Runs: 2

---

## Scenario: PrimeNumbers

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_PrimeNumbers` | 527.3 ± 30.4 | 505.8 | 548.8 | 1.26 ± 0.26 |
| `./bin/wasmedge_aot_noopts_PrimeNumbers` | 419.4 ± 83.5 | 360.3 | 478.5 | 1.00 |
| `./bin/wasmedge_aot_wopts_PrimeNumbers` | 567.9 ± 71.4 | 517.4 | 618.5 | 1.35 ± 0.32 |
| `./bin/wasmtime_jit_noopts_PrimeNumbers` | 804.7 ± 16.0 | 793.4 | 816.0 | 1.92 ± 0.38 |
| `./bin/wasmtime_jit_wopts_PrimeNumbers` | 703.0 ± 34.6 | 678.6 | 727.5 | 1.68 ± 0.34 |
| `./bin/wazero_aot_noopts_PrimeNumbers` | 909.7 ± 54.7 | 870.9 | 948.4 | 2.17 ± 0.45 |
| `./bin/wazero_aot_wopts_PrimeNumbers` | 846.9 ± 117.7 | 763.6 | 930.1 | 2.02 ± 0.49 |

---

## Scenario: Fibonacci

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_Fibonacci` | 548.6 ± 46.4 | 515.8 | 581.4 | 1.40 ± 0.12 |
| `./bin/wasmedge_aot_noopts_Fibonacci` | 391.0 ± 3.9 | 388.3 | 393.7 | 1.00 |
| `./bin/wasmedge_aot_wopts_Fibonacci` | 429.6 ± 134.2 | 334.7 | 524.5 | 1.10 ± 0.34 |
| `./bin/wasmtime_jit_noopts_Fibonacci` | 523.5 ± 21.1 | 508.6 | 538.4 | 1.34 ± 0.06 |
| `./bin/wasmtime_jit_wopts_Fibonacci` | 503.4 ± 7.8 | 497.9 | 508.9 | 1.29 ± 0.02 |
| `./bin/wazero_aot_noopts_Fibonacci` | 686.3 ± 14.2 | 676.3 | 696.4 | 1.76 ± 0.04 |
| `./bin/wazero_aot_wopts_Fibonacci` | 839.9 ± 127.6 | 749.7 | 930.1 | 2.15 ± 0.33 |

---

## Scenario: Lightweight

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_Lightweight` | 66.2 ± 2.8 | 64.2 | 68.1 | 1.00 |
| `./bin/wasmedge_aot_noopts_Lightweight` | 241.9 ± 23.3 | 225.5 | 258.4 | 3.65 ± 0.38 |
| `./bin/wasmedge_aot_wopts_Lightweight` | 294.7 ± 40.6 | 266.0 | 323.3 | 4.45 ± 0.64 |
| `./bin/wasmtime_jit_noopts_Lightweight` | 598.3 ± 31.1 | 576.3 | 620.3 | 9.04 ± 0.60 |
| `./bin/wasmtime_jit_wopts_Lightweight` | 587.3 ± 63.6 | 542.3 | 632.3 | 8.87 ± 1.03 |
| `./bin/wazero_aot_noopts_Lightweight` | 684.3 ± 40.9 | 655.4 | 713.2 | 10.34 ± 0.75 |
| `./bin/wazero_aot_wopts_Lightweight` | 457.7 ± 13.6 | 448.0 | 467.3 | 6.91 ± 0.35 |

---

## Scenario: TailFibonacci

| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
|:---|---:|---:|---:|---:|
| `./bin/native_TailFibonacci` | 19.9 ± 0.7 | 19.5 | 20.4 | 1.00 |
| `./bin/wasmedge_aot_noopts_TailFibonacci` | 127.2 ± 66.7 | 80.0 | 174.3 | 6.37 ± 3.35 |
| `./bin/wasmedge_aot_wopts_TailFibonacci` | 83.1 ± 1.3 | 82.1 | 84.0 | 4.16 ± 0.15 |
| `./bin/wasmtime_jit_noopts_TailFibonacci` | 213.9 ± 36.0 | 188.4 | 239.4 | 10.72 ± 1.84 |
| `./bin/wasmtime_jit_wopts_TailFibonacci` | 200.4 ± 14.8 | 190.0 | 210.9 | 10.05 ± 0.81 |
| `./bin/wazero_aot_noopts_TailFibonacci` | 414.1 ± 59.1 | 372.3 | 455.9 | 20.76 ± 3.04 |
| `./bin/wazero_aot_wopts_TailFibonacci` | 416.7 ± 208.6 | 269.1 | 564.2 | 20.89 ± 10.48 |

---


================================================================================
# NET EXECUTION TIME (Total - Overhead)
================================================================================

This section shows the pure execution time after subtracting WASM runtime overhead.
Formula: NET Time = Total Execution Time - Overhead Time

## Scenario: PrimeNumbers

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.5273341954399999 |               N/A |          N/A |
| Wasmedge_AOT_NoOpts                                     |       0.419422 |          0.089370 |     0.330052 |
| Wasmedge_AOT_WithOpts                                   |       0.567942 |          0.085136 |     0.482806 |
| Wasmtime_JIT_NoOpts                                     |       0.804712 |          0.205816 |     0.598896 |
| Wasmtime_JIT_WithOpts                                   |       0.703028 |          0.148224 |     0.554805 |
| Wazero_AOT_NoOpts                                       |       0.909651 |          0.111377 |     0.798274 |
| Wazero_AOT_WithOpts                                     |       0.846857 |          0.114306 |     0.732550 |

---

## Scenario: Fibonacci

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.54858715164 |               N/A |          N/A |
| Wasmedge_AOT_NoOpts                                     |       0.391009 |          0.087426 |     0.303583 |
| Wasmedge_AOT_WithOpts                                   |       0.429582 |          0.201302 |     0.228280 |
| Wasmtime_JIT_NoOpts                                     |       0.523543 |          0.161548 |     0.361995 |
| Wasmtime_JIT_WithOpts                                   |       0.503402 |          0.157882 |     0.345520 |
| Wazero_AOT_NoOpts                                       |       0.686336 |          0.200304 |     0.486032 |
| Wazero_AOT_WithOpts                                     |       0.839924 |          0.399266 |     0.440658 |

---

## Scenario: Lightweight

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.06619258074 |               N/A |          N/A |
| Wasmedge_AOT_NoOpts                                     |       0.241930 |          0.076642 |     0.165288 |
| Wasmedge_AOT_WithOpts                                   |       0.294662 |          0.079198 |     0.215465 |
| Wasmtime_JIT_NoOpts                                     |       0.598301 |          0.157347 |     0.440954 |
| Wasmtime_JIT_WithOpts                                   |       0.587275 |          0.215763 |     0.371512 |
| Wazero_AOT_NoOpts                                       |       0.684326 |          0.105482 |     0.578844 |
| Wazero_AOT_WithOpts                                     |       0.457658 |          0.148158 |     0.309500 |

---

## Scenario: TailFibonacci

| Runtime | Total Time (s) | Overhead Time (s) | NET Time (s) |
|---------|----------------|-------------------|--------------|
| Native                                                  |  0.01994574424 |               N/A |          N/A |
| Wasmedge_AOT_NoOpts                                     |       0.127154 |          0.192617 |    -0.065463 |
| Wasmedge_AOT_WithOpts                                   |       0.083058 |          0.113208 |    -0.030150 |
| Wasmtime_JIT_NoOpts                                     |       0.213885 |          0.152491 |     0.061394 |
| Wasmtime_JIT_WithOpts                                   |       0.200431 |          0.141389 |     0.059042 |
| Wazero_AOT_NoOpts                                       |       0.414071 |          0.116649 |     0.297422 |
| Wazero_AOT_WithOpts                                     |       0.416661 |          0.095684 |     0.320977 |

---

