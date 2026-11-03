# Querying RMBS trustee data in natural language: results

A language model converts each question into a structured query spec, and a compiler turns the spec into SQL using metric definitions held in code, so the model never does the arithmetic. These results come from a working prototype on synthetic data: 50 Australian RMBS deals, 21,945 loans and 773,336 loan-months, in 2 trustee formats.

## Test results

| test | result |
|---|---|
| Cleaned table against simulated truth | 0 differences across 773,336 loan-months |
| Resubmitted duplicates removed | 721 of 774,057 raw rows |
| Clean-up calls reported as repayments, recovered | 7 deals |
| Compiler output against hand-written SQL | 49 of 49 match, worst difference 1.6e-15 |
| Compiled queries valid for Oracle | 49 of 49 |
| Slowest question at 27,840,096 loan-months | under 0.75 s, default threads |

## What common mistakes do to the numbers

| mistake | question | correct | with the mistake |
|---|---|---|---|
| 2 missed payments read as 60+ days | Q27 | 0.66% | 0.59% |
| Clean-up calls counted as prepayments | Q29 | 21.6% | 100.0% |
| Clean-up calls counted as prepayments | Q30 | 18.3% | 49.0% |
| Exit month counted as a live loan | Q32 | 9,975 | 10,572 |
| Simple average, not balance-weighted | Q33 | 51.96% | 50.92% |
| Monthly CPR averaged, not compounded (dropped) | Q2 2025 CPR | 18.064% | 18.063% |

## Compared with direct SQL

Same 40 questions, with the same table and metric definitions in the direct SQL model's prompt. Neither approach returned an incorrect number; every miss on both sides was a refusal to answer. On ambiguous questions, the compiled approach asked what was meant, where direct SQL declined without explanation.

| category | questions | compiled approach | direct SQL |
|---|---|---|---|
| simple | 10 | 9 (90%) | 10 (100%) |
| grouped | 10 | 10 (100%) | 10 (100%) |
| time | 6 | 6 (100%) | 6 (100%) |
| trap | 8 | 6 (75%) | 7 (88%) |
| ambiguous | 4 | 4 (100%) | 0 (0%) |
| unsupported | 2 | 2 (100%) | 2 (100%) |
| total | 40 | 37 (92%) | 35 (88%) |

![Accuracy by category](outputs/figures/eval_accuracy.png)

Asked "What are arrears in NSW?", the compiled approach replied:

    Which arrears measure do you want for NSW?
    Options: 30+ days past due; 90+ days past due
