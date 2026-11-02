# Asking RMBS loan data questions in plain English: results

A language model turns each question into a small query spec, and a compiler turns the spec into SQL over governed metric definitions, so the model never does the arithmetic. These results are from a working prototype on synthetic data: 50 Australian RMBS deals, 21,945 loans and 773,336 loan-months in 2 trustee formats.

## What is proved

| check | result |
|---|---|
| Cleaning: canonical table against simulated truth | 0 mismatches over 773,336 loan-months |
| Cleaning: resubmitted duplicates removed | 721 of 774,057 raw rows |
| Cleaning: clean-up calls coded as repayments, recovered | 7 deals |
| Compiler: output against hand-written SQL | 49 of 49 match, worst difference 1.6e-15 |
| Compiler: queries that render to Oracle | 49 of 49 |
| Scale: slowest question at 27,840,096 loan-months | under 0.75 s with default threads |

## The traps a plain SQL writer falls into

| trap | question | correct | naive mistake gives |
|---|---|---|---|
| Arrears units | Q27 | 0.66% | 0.59% |
| Calls as prepayments | Q29 | 21.6% | 100.0% |
| Calls as prepayments | Q30 | 18.3% | 49.0% |
| Exit rows as live loans | Q32 | 9,975 | 10,572 |
| Unweighted average | Q33 | 51.96% | 50.92% |
| Averaging CPR (dropped, gap too small) | Q2 2025 CPR | 18.064% | 18.063% |

## Governed system against plain text-to-SQL

The 40-question eval compares the 2 on the same questions, but it hasn't been recorded in this copy, because a run needs an Anthropic API key and none is stored. It takes 2 commands, and this page then regenerates with the results:

    $env:ANTHROPIC_API_KEY = "<your key>"
    python scripts/run_eval.py --mode record
    python scripts/build_writeup.py

![Query time per question](outputs/figures/scale_benchmark.png)
