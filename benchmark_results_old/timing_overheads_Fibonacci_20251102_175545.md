| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
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
