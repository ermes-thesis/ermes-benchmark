| Command | Mean [ms] | Min [ms] | Max [ms] | Relative |
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
