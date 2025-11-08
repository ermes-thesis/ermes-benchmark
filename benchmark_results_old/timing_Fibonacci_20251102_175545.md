| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
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
