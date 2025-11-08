| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
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
