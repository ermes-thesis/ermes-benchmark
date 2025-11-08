| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
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
