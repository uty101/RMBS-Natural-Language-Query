# Review: Section 4, LLM layer

Follow this template exactly. Every number below must be backed by raw rows or raw
output printed in full in this file (CLAUDE.md rule 10). No paraphrased results.

## 1. Outcome

- Instruction file: `instructions/04_section_4.md`
- Outcome: complete
- Last step reached: 4.7
- Stop reason (if stopped): none

## 2. Commits

Output of `git log --oneline` for this section's commits, oldest last, pasted verbatim.

```
4da0a0b step 4.7: PLAN.md section 4 and conventions for the locked connection, cache key and guard
4939596 step 4.6: answer pipeline and rmbsq ask CLI, replay by default
18514df step 4.5: baseline SQL call and timed run on the locked read-only connection
f3538c5 step 4.4: narration call, number guard and template answer
3b6927c step 4.3: entity resolution with exact, alias, flag and fuzzy rules
d3a7875 step 4.2: spec prompt rendered from the catalogue, submit_spec tool with inlined schema, parsing
cd5d8c4 step 4.1: cached LLM client with replay and record modes, SHA-256 request key
9634ac9 step 4.0: locked read-only connection, strict spec order for metric columns, prompts and fixtures copied
```

## 3. Steps

Evidence item numbers J.1 to J.8 refer to instruction 04 part J. Every evidence block
was printed from the small profile built exactly as the `small_db` fixture builds it.

### Step 4.0: fixtures, prompts, locked connection

- Files: `tests/fixtures/compiler_gold.json` (replaced by `instructions/04_compiler_gold.json`),
  `tests/fixtures/guard_cases.json`, `prompts/spec_system.md`, `prompts/narrate_system.md`,
  `prompts/baseline_system.md` (all byte for byte, checked with `cmp`); new `rmbsq/db.py`;
  changed `rmbsq/semantic/compiler.py` (strict spec order), `rmbsq/semantic/catalog.py`,
  `scripts/build_canonical.py`, and the read connections in `tests/test_canonical_build.py`,
  `tests/test_canonical_truth.py`, `tests/test_catalog.py`, `tests/test_compiler.py`,
  `tests/test_routing.py`; new `tests/test_db.py`.
- Signatures implemented: `connect_readonly(path: Path) -> DuckDBPyConnection`.
- Tests: `test_fifteen_specs_match_hand_sql[S01..S15]`, `test_full_fifteen_specs_match_hand_sql[S01..S15]`
  (full), `test_readonly_blocks`; result passed.
- Outputs: none. `outputs/` is unchanged (`git status --short outputs` prints nothing).
- Evidence: J.6 below also shows what the locked connection refuses. The same blocks run
  in `test_readonly_blocks`:

```
timeout 1 s: BaselineError after 1.028 s: INTERRUPT Error: Interrupted!
after interrupt, SELECT 1 -> (1,)
COPY ... TO: BaselineError: Permission Error: Cannot access file "<tmp>/ev/out.csv" - file system operations are disabled by configuration
file created: False
CREATE TABLE t (a INTEGER) -> InvalidInputException: Invalid Input Error: Cannot execute statement of type "CREATE" on database "small" which is attached in read-only mode!
SELECT * FROM read_csv('<tmp>/ev/r.csv') -> PermissionException: Permission Error: Cannot access file "<tmp>/ev/r.csv" - file system operations are disabled by configuration

LINE 1: SELECT * FROM read_csv('<tmp>/ev/r.csv')...
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
SET threads = 4 -> InvalidInputException: Invalid Input Error: Cannot change configuration option ""threads"" - the configuration has been locked
INSTALL httpfs -> PermissionException: Permission Error: Cannot access directory "<home>\.duckdb\extensions\v2.0.0\windows_amd64" - file system operations are disabled by configuration
```

- Deviations from PLAN.md or the instruction file: none. `rmbsq/canonical/build.py` keeps
  its write connection, as B says. No other `duckdb.connect` remains in `rmbsq/`,
  `scripts/` or `tests/`.

### Step 4.1: cached client

- Files: `rmbsq/llm/client.py`, `tests/llm_helpers.py`, `tests/test_llm_client.py`,
  `tests/fixtures/llm_responses/text_hello.json`.
- Signatures implemented: `LLMClient(cfg, mode="replay", cache_dir=Path("data/llm_cache"))`,
  `.build_request(system, messages, tools, tool_choice) -> dict`,
  `.call(system, messages, tools, tool_choice) -> dict`, `request_key(request) -> str`,
  `write_entry(path, entry)`, `CacheMiss(key)`, `MissingApiKey`.
- Tests: `test_key_stable`, `test_replay_hit`, `test_replay_miss_raises`,
  `test_record_hit_does_not_call_api`, `test_missing_key_raises`, `test_cache_file_format`;
  result passed.
- Outputs: none.
- Evidence (J.7): 1 fixture cache file in full, as `tests/llm_helpers.py::seed` writes it
  for `test_parse_fixture_answer` (the spec call for "What is the balance and loan count
  by originator?" with fixture `spec_answer`). Its file name is its key.

```
[a6a53e2565cb3784e2e39cf0646a302dd9abe592ecc7988f3c08f0d04068e9f6.json]
{
 "key": "a6a53e2565cb3784e2e39cf0646a302dd9abe592ecc7988f3c08f0d04068e9f6",
 "latency_s": 1.234,
 "request": {
  "max_tokens": 1024,
  "messages": [
   {
    "content": "What is the balance and loan count by originator?",
    "role": "user"
   }
  ],
  "model": "claude-sonnet-5-5",
  "system": "You translate questions about a pool of Australian residential mortgage-backed securities (RMBS) into a query spec. You never calculate anything yourself. You call the tool `submit_spec` exactly once, and a compiler turns your spec into SQL over governed metric definitions.\n\n# The data\n\nMonthly loan-level trustee data for 10 deals, from 2021-10 to 2026-09. \"Latest\", \"current\" and \"now\" mean 2026-09. Months are written YYYY-MM.\n\n# Metrics (use these names exactly)\n\n| name | kind | definition |\n|---|---|---|\n| loan_count | stock | Number of loans with a positive balance at month end. |\n| balance_total | stock | Total outstanding balance in AUD at month end. |\n| arrears_30p_bal | stock | Share of outstanding balance that is 30 or more days past due, excluding loans in hardship, weighted by balance. |\n| arrears_90p_bal | stock | Share of outstanding balance that is 90 or more days past due, excluding loans in hardship, weighted by balance. |\n| arrears_90p_cnt | stock | Share of loans by count that are 90 or more days past due, excluding loans in hardship. |\n| hardship_share_bal | stock | Share of outstanding balance on a hardship arrangement. |\n| wa_orig_ltv | stock | Balance-weighted average loan-to-value ratio at origination. |\n| wa_indexed_ltv | stock | Balance-weighted average current loan-to-value ratio, with property values indexed to suburb house prices. |\n| wa_rate | stock | Balance-weighted average interest rate. |\n| smm_vol | flow | Monthly voluntary prepayment rate: full prepayments plus partial curtailments over scheduled balance. Excludes repurchases, defaults and clean-up calls. |\n| cpr | flow | Conditional prepayment rate: smm_vol annualised. Excludes repurchases, defaults and clean-up calls. |\n| cdr | flow | Conditional default rate: defaulted balance over opening balance each month, annualised. |\n\n# Dimensions (for group_by and filters; use these names exactly)\n\n| name | level | definition |\n|---|---|---|\n| deal_id | deal | Deal identifier, for example D004. |\n| deal_name | deal | Deal name: originator code, issue year and series number, for example HARB 2019-1. |\n| originator | deal | Originator code: HARB, KOO, WAT, CST or RED. |\n| trustee_format | deal | Which trustee report format the deal is delivered in. |\n| issue_year | deal | Year the deal was issued. |\n| vintage_year | loan | Year the loan was originated. |\n| city | loan | Capital city region of the property. |\n| state | loan | State of the property. |\n| area | loan | Local area of the property, for example Blacktown. |\n| suburb | loan | Suburb of the property, for example Blacktown North. |\n| rate_type | loan | Current rate type that month; a fixed loan becomes variable at its fixed rate expiry. |\n| io_flag | loan | Whether the loan is interest only that month. |\n| occupancy | loan | Owner occupied or investment property. |\n| lmi_flag | loan | Whether the loan has lenders mortgage insurance (LTV above 80% at origination). |\n| ltv_bucket_orig | loan | Origination LTV band, in percent. |\n| ltv_bucket_indexed | loan | Current indexed LTV band, in percent. |\n| seasoning_bucket | loan | Months since origination. |\n| dpd_bucket | loan | Days past due band. Loans in hardship are current. |\n\n# Allowed values\n\n- deal_id: D001, D002, D003, D004, D005, D006, D007, D008, D009, D010\n- deal_name: CST 2020-1, CST 2023-1, HARB 2019-1, HARB 2021-1, KOO 2019-1, KOO 2022-1, RED 2021-1, RED 2023-1, WAT 2020-1, WAT 2022-1 (aliases such as \"Harbour 19-1\" or \"HARB19-1\" are also accepted)\n- originator: CST, HARB, KOO, RED, WAT\n- trustee_format: A, B\n- issue_year: 2019, 2020, 2021, 2022, 2023\n- vintage_year: 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023\n- city: Adelaide, Brisbane, Melbourne, Perth, Sydney\n- state: NSW, QLD, SA, VIC, WA\n- area: Blacktown, Boroondara, Brisbane Inner, Casey, Charles Sturt, Ipswich, Joondalup, Logan, Moreton Bay, Onkaparinga, Parramatta, Penrith, Playford, Rockingham, Salisbury, Stirling, Sutherland, Wanneroo, Whittlesea, Wyndham\n- suburb: Blacktown Central, Blacktown North, Blacktown South, Boroondara Central, Boroondara North, Boroondara South, Brisbane Inner Central, Brisbane Inner North, Brisbane Inner South, Casey Central, Casey North, Casey South, Charles Sturt North, Charles Sturt South, Ipswich Central, Ipswich North, Ipswich South, Joondalup Central, Joondalup North, Joondalup South, Logan Central, Logan North, Logan South, Moreton Bay Central, Moreton Bay North, Moreton Bay South, Onkaparinga Central, Onkaparinga North, Parramatta Central, Parramatta North, Parramatta South, Penrith Central, Penrith North, Penrith South, Playford Central, Playford North, Playford South, Rockingham Central, Rockingham North, Rockingham South, Salisbury Central, Salisbury North, Salisbury South, Stirling Central, Stirling North, Stirling South, Sutherland Central, Sutherland North, Sutherland South, Wanneroo Central, Wanneroo North, Wanneroo South, Whittlesea Central, Whittlesea North, Whittlesea South, Wyndham Central, Wyndham North, Wyndham South\n- rate_type: fixed, variable\n- io_flag: yes, no\n- occupancy: owner, investor\n- lmi_flag: yes, no\n- ltv_bucket_orig: <=60, 60-70, 70-80, 80-90, >90\n- ltv_bucket_indexed: <=60, 60-70, 70-80, 80-90, >90\n- seasoning_bucket: 0-12, 13-24, 25-36, 37-60, >60\n- dpd_bucket: current, 1-29, 30-59, 60-89, 90+\n\n# How to fill the spec\n\nChoose 1 of 3 intents.\n\n**answer** when every part of the question maps onto the metrics, dimensions and time window above.\n- Pick 1 to 3 metrics and 0 to 2 group_by dimensions.\n- Filters hold the values as the user wrote them (for example \"Harbour 21-1\" or \"blacktown\"). A resolver maps them to stored values afterwards, so don't guess a different value.\n- Time:\n  - With no time in the question, leave `time` out, and the default is the latest month.\n  - \"In 2024\" is start 2024-01, end 2024-12. \"Last 12 months\" is the 12 months ending 2026-09.\n  - A trend (\"over time\", \"by month\", \"how has it moved\") is a series. Use grain month unless the user says quarter or year.\n  - A single figure for a stretch of time (\"CPR over 2025\") is shape point with that start and end.\n- \"Top N\", \"highest\" and \"worst\" need `order` with the metric, direction desc and limit N. \"Lowest\" and \"best\" use asc, with limit 5 when no N is given.\n- Synonyms:\n  - LVR means LTV.\n  - Prepayment speed and prepayments mean cpr.\n  - Defaults and default rate mean cdr.\n  - Interest only and IO mean io_flag.\n  - Investor and investment mean occupancy investor.\n  - Owner occupied means occupancy owner.\n  - Vintage and origination year mean vintage_year.\n  - Deal series and deal mean deal_name.\n- An arrears question that gives a day threshold but doesn't say count or balance uses the balance metric.\n\n**clarify** when the question could reasonably mean different things that would change the number. Give a short question and 2 to 4 options.\n- \"Arrears\" with no day threshold. Options: 30+ days and 90+ days.\n- A term the metrics don't define is carrying the meaning, such as \"performance\", \"risky\", \"quality\" or \"health\".\n- A request that fits 2 metrics equally well.\n\n**unsupported** when the answer needs data the catalogue doesn't hold, or a forecast. State the reason in 1 sentence.\n- Borrower income, credit scores, servicer names, LMI claims or payouts, ratings, tranche or note data, or loss severity by property type.\n- Anything about the future (\"will\", \"next quarter\", \"forecast\", \"expect\").\n- Dates outside 2021-10 to 2026-09.\n\nNever put a number you computed into the spec.\n",
  "temperature": 0,
  "tool_choice": {
   "name": "submit_spec",
   "type": "tool"
  },
  "tools": [
   {
    "description": "Submit the query spec for the question.",
    "input_schema": {
     "properties": {
      "clarify": {
       "anyOf": [
        {
         "properties": {
          "options": {
           "items": {
            "type": "string"
           },
           "maxItems": 4,
           "minItems": 2,
           "type": "array"
          },
          "question": {
           "type": "string"
          }
         },
         "required": [
          "question",
          "options"
         ],
         "type": "object"
        },
        {
         "type": "null"
        }
       ],
       "default": null
      },
      "filters": {
       "additionalProperties": {
        "items": {
         "anyOf": [
          {
           "type": "string"
          },
          {
           "type": "integer"
          }
         ]
        },
        "type": "array"
       },
       "propertyNames": {
        "enum": [
         "deal_id",
         "deal_name",
         "originator",
         "trustee_format",
         "issue_year",
         "vintage_year",
         "city",
         "state",
         "area",
         "suburb",
         "rate_type",
         "io_flag",
         "occupancy",
         "lmi_flag",
         "ltv_bucket_orig",
         "ltv_bucket_indexed",
         "seasoning_bucket",
         "dpd_bucket"
        ]
       },
       "type": "object"
      },
      "group_by": {
       "items": {
        "enum": [
         "deal_id",
         "deal_name",
         "originator",
         "trustee_format",
         "issue_year",
         "vintage_year",
         "city",
         "state",
         "area",
         "suburb",
         "rate_type",
         "io_flag",
         "occupancy",
         "lmi_flag",
         "ltv_bucket_orig",
         "ltv_bucket_indexed",
         "seasoning_bucket",
         "dpd_bucket"
        ],
        "type": "string"
       },
       "maxItems": 2,
       "type": "array"
      },
      "intent": {
       "enum": [
        "answer",
        "clarify",
        "unsupported"
       ],
       "type": "string"
      },
      "metrics": {
       "items": {
        "enum": [
         "loan_count",
         "balance_total",
         "arrears_30p_bal",
         "arrears_90p_bal",
         "arrears_90p_cnt",
         "hardship_share_bal",
         "wa_orig_ltv",
         "wa_indexed_ltv",
         "wa_rate",
         "smm_vol",
         "cpr",
         "cdr"
        ],
        "type": "string"
       },
       "maxItems": 3,
       "type": "array"
      },
      "order": {
       "anyOf": [
        {
         "properties": {
          "direction": {
           "enum": [
            "desc",
            "asc"
           ],
           "type": "string"
          },
          "limit": {
           "maximum": 20,
           "minimum": 1,
           "type": "integer"
          },
          "metric": {
           "enum": [
            "loan_count",
            "balance_total",
            "arrears_30p_bal",
            "arrears_90p_bal",
            "arrears_90p_cnt",
            "hardship_share_bal",
            "wa_orig_ltv",
            "wa_indexed_ltv",
            "wa_rate",
            "smm_vol",
            "cpr",
            "cdr"
           ],
           "type": "string"
          }
         },
         "required": [
          "metric",
          "direction",
          "limit"
         ],
         "type": "object"
        },
        {
         "type": "null"
        }
       ],
       "default": null
      },
      "time": {
       "anyOf": [
        {
         "properties": {
          "end": {
           "pattern": "^\\d{4}-(0[1-9]|1[0-2])$",
           "type": "string"
          },
          "grain": {
           "enum": [
            "month",
            "quarter",
            "year"
           ],
           "type": "string"
          },
          "shape": {
           "enum": [
            "series",
            "point"
           ],
           "type": "string"
          },
          "start": {
           "pattern": "^\\d{4}-(0[1-9]|1[0-2])$",
           "type": "string"
          }
         },
         "required": [
          "grain",
          "start",
          "end",
          "shape"
         ],
         "type": "object"
        },
        {
         "type": "null"
        }
       ],
       "default": null
      },
      "unsupported_reason": {
       "anyOf": [
        {
         "type": "string"
        },
        {
         "type": "null"
        }
       ],
       "default": null
      }
     },
     "required": [
      "intent"
     ],
     "type": "object"
    },
    "name": "submit_spec"
   }
  ]
 },
 "response": {
  "content": [
   {
    "id": "toolu_fixture_spec_answer",
    "input": {
     "group_by": [
      "originator"
     ],
     "intent": "answer",
     "metrics": [
      "balance_total",
      "loan_count"
     ]
    },
    "name": "submit_spec",
    "type": "tool_use"
   }
  ],
  "id": "msg_fixture_spec_answer",
  "model": "claude-sonnet-5-5",
  "role": "assistant",
  "stop_reason": "tool_use",
  "stop_sequence": null,
  "type": "message",
  "usage": {
   "input_tokens": 3100,
   "output_tokens": 60
  }
 }
}
```

- Deviations from PLAN.md or the instruction file:
  - A narration request has no tools. It is keyed with `"tools": []` and
    `"tool_choice": null`, as C.1 builds every request, and in record mode those 2 keys are
    left out of the API call, since the API takes no `tool_choice` without tools.
  - In record mode the SDK client is created with `max_retries=0`, so the C.4 retries
    (3, after 2, 4 and 8 s) are the only ones. `latency_s` times the attempt that
    succeeded.
  - On a hit, `calls` records the stored `latency_s`.

### Step 4.2: spec agent

- Files: `rmbsq/llm/spec_agent.py`, `tests/test_spec_agent.py`,
  `tests/fixtures/llm_responses/spec_{answer,clarify,unsupported,four_metrics,text_only}.json`.
- Signatures implemented: `render_spec_prompt(catalog, cfg) -> str`, `spec_tool() -> dict`,
  `spec_input_schema() -> dict`, `question_to_spec(question, client, catalog) -> tuple[QuerySpec, bool]`.
- Tests: `test_prompt_has_every_name`, `test_tool_schema_inlined`, `test_parse_fixture_answer`,
  `test_parse_fixture_clarify`, `test_parse_fixture_unsupported`, `test_parse_invalid_spec`,
  `test_parse_missing_tool_block`; result passed.
- Outputs: none.
- Evidence (J.1): the rendered spec prompt in full, from `small_db`, and its length.

````
You translate questions about a pool of Australian residential mortgage-backed securities (RMBS) into a query spec. You never calculate anything yourself. You call the tool `submit_spec` exactly once, and a compiler turns your spec into SQL over governed metric definitions.

# The data

Monthly loan-level trustee data for 10 deals, from 2021-10 to 2026-09. "Latest", "current" and "now" mean 2026-09. Months are written YYYY-MM.

# Metrics (use these names exactly)

| name | kind | definition |
|---|---|---|
| loan_count | stock | Number of loans with a positive balance at month end. |
| balance_total | stock | Total outstanding balance in AUD at month end. |
| arrears_30p_bal | stock | Share of outstanding balance that is 30 or more days past due, excluding loans in hardship, weighted by balance. |
| arrears_90p_bal | stock | Share of outstanding balance that is 90 or more days past due, excluding loans in hardship, weighted by balance. |
| arrears_90p_cnt | stock | Share of loans by count that are 90 or more days past due, excluding loans in hardship. |
| hardship_share_bal | stock | Share of outstanding balance on a hardship arrangement. |
| wa_orig_ltv | stock | Balance-weighted average loan-to-value ratio at origination. |
| wa_indexed_ltv | stock | Balance-weighted average current loan-to-value ratio, with property values indexed to suburb house prices. |
| wa_rate | stock | Balance-weighted average interest rate. |
| smm_vol | flow | Monthly voluntary prepayment rate: full prepayments plus partial curtailments over scheduled balance. Excludes repurchases, defaults and clean-up calls. |
| cpr | flow | Conditional prepayment rate: smm_vol annualised. Excludes repurchases, defaults and clean-up calls. |
| cdr | flow | Conditional default rate: defaulted balance over opening balance each month, annualised. |

# Dimensions (for group_by and filters; use these names exactly)

| name | level | definition |
|---|---|---|
| deal_id | deal | Deal identifier, for example D004. |
| deal_name | deal | Deal name: originator code, issue year and series number, for example HARB 2019-1. |
| originator | deal | Originator code: HARB, KOO, WAT, CST or RED. |
| trustee_format | deal | Which trustee report format the deal is delivered in. |
| issue_year | deal | Year the deal was issued. |
| vintage_year | loan | Year the loan was originated. |
| city | loan | Capital city region of the property. |
| state | loan | State of the property. |
| area | loan | Local area of the property, for example Blacktown. |
| suburb | loan | Suburb of the property, for example Blacktown North. |
| rate_type | loan | Current rate type that month; a fixed loan becomes variable at its fixed rate expiry. |
| io_flag | loan | Whether the loan is interest only that month. |
| occupancy | loan | Owner occupied or investment property. |
| lmi_flag | loan | Whether the loan has lenders mortgage insurance (LTV above 80% at origination). |
| ltv_bucket_orig | loan | Origination LTV band, in percent. |
| ltv_bucket_indexed | loan | Current indexed LTV band, in percent. |
| seasoning_bucket | loan | Months since origination. |
| dpd_bucket | loan | Days past due band. Loans in hardship are current. |

# Allowed values

- deal_id: D001, D002, D003, D004, D005, D006, D007, D008, D009, D010
- deal_name: CST 2020-1, CST 2023-1, HARB 2019-1, HARB 2021-1, KOO 2019-1, KOO 2022-1, RED 2021-1, RED 2023-1, WAT 2020-1, WAT 2022-1 (aliases such as "Harbour 19-1" or "HARB19-1" are also accepted)
- originator: CST, HARB, KOO, RED, WAT
- trustee_format: A, B
- issue_year: 2019, 2020, 2021, 2022, 2023
- vintage_year: 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023
- city: Adelaide, Brisbane, Melbourne, Perth, Sydney
- state: NSW, QLD, SA, VIC, WA
- area: Blacktown, Boroondara, Brisbane Inner, Casey, Charles Sturt, Ipswich, Joondalup, Logan, Moreton Bay, Onkaparinga, Parramatta, Penrith, Playford, Rockingham, Salisbury, Stirling, Sutherland, Wanneroo, Whittlesea, Wyndham
- suburb: Blacktown Central, Blacktown North, Blacktown South, Boroondara Central, Boroondara North, Boroondara South, Brisbane Inner Central, Brisbane Inner North, Brisbane Inner South, Casey Central, Casey North, Casey South, Charles Sturt North, Charles Sturt South, Ipswich Central, Ipswich North, Ipswich South, Joondalup Central, Joondalup North, Joondalup South, Logan Central, Logan North, Logan South, Moreton Bay Central, Moreton Bay North, Moreton Bay South, Onkaparinga Central, Onkaparinga North, Parramatta Central, Parramatta North, Parramatta South, Penrith Central, Penrith North, Penrith South, Playford Central, Playford North, Playford South, Rockingham Central, Rockingham North, Rockingham South, Salisbury Central, Salisbury North, Salisbury South, Stirling Central, Stirling North, Stirling South, Sutherland Central, Sutherland North, Sutherland South, Wanneroo Central, Wanneroo North, Wanneroo South, Whittlesea Central, Whittlesea North, Whittlesea South, Wyndham Central, Wyndham North, Wyndham South
- rate_type: fixed, variable
- io_flag: yes, no
- occupancy: owner, investor
- lmi_flag: yes, no
- ltv_bucket_orig: <=60, 60-70, 70-80, 80-90, >90
- ltv_bucket_indexed: <=60, 60-70, 70-80, 80-90, >90
- seasoning_bucket: 0-12, 13-24, 25-36, 37-60, >60
- dpd_bucket: current, 1-29, 30-59, 60-89, 90+

# How to fill the spec

Choose 1 of 3 intents.

**answer** when every part of the question maps onto the metrics, dimensions and time window above.
- Pick 1 to 3 metrics and 0 to 2 group_by dimensions.
- Filters hold the values as the user wrote them (for example "Harbour 21-1" or "blacktown"). A resolver maps them to stored values afterwards, so don't guess a different value.
- Time:
  - With no time in the question, leave `time` out, and the default is the latest month.
  - "In 2024" is start 2024-01, end 2024-12. "Last 12 months" is the 12 months ending 2026-09.
  - A trend ("over time", "by month", "how has it moved") is a series. Use grain month unless the user says quarter or year.
  - A single figure for a stretch of time ("CPR over 2025") is shape point with that start and end.
- "Top N", "highest" and "worst" need `order` with the metric, direction desc and limit N. "Lowest" and "best" use asc, with limit 5 when no N is given.
- Synonyms:
  - LVR means LTV.
  - Prepayment speed and prepayments mean cpr.
  - Defaults and default rate mean cdr.
  - Interest only and IO mean io_flag.
  - Investor and investment mean occupancy investor.
  - Owner occupied means occupancy owner.
  - Vintage and origination year mean vintage_year.
  - Deal series and deal mean deal_name.
- An arrears question that gives a day threshold but doesn't say count or balance uses the balance metric.

**clarify** when the question could reasonably mean different things that would change the number. Give a short question and 2 to 4 options.
- "Arrears" with no day threshold. Options: 30+ days and 90+ days.
- A term the metrics don't define is carrying the meaning, such as "performance", "risky", "quality" or "health".
- A request that fits 2 metrics equally well.

**unsupported** when the answer needs data the catalogue doesn't hold, or a forecast. State the reason in 1 sentence.
- Borrower income, credit scores, servicer names, LMI claims or payouts, ratings, tranche or note data, or loss severity by property type.
- Anything about the future ("will", "next quarter", "forecast", "expect").
- Dates outside 2021-10 to 2026-09.

Never put a number you computed into the spec.


[length: 7500 characters]
````

- Evidence (J.2): the inlined tool schema in full (`spec_tool()["input_schema"]`).

```
{
 "properties": {
  "intent": {
   "enum": [
    "answer",
    "clarify",
    "unsupported"
   ],
   "type": "string"
  },
  "metrics": {
   "items": {
    "enum": [
     "loan_count",
     "balance_total",
     "arrears_30p_bal",
     "arrears_90p_bal",
     "arrears_90p_cnt",
     "hardship_share_bal",
     "wa_orig_ltv",
     "wa_indexed_ltv",
     "wa_rate",
     "smm_vol",
     "cpr",
     "cdr"
    ],
    "type": "string"
   },
   "maxItems": 3,
   "type": "array"
  },
  "group_by": {
   "items": {
    "enum": [
     "deal_id",
     "deal_name",
     "originator",
     "trustee_format",
     "issue_year",
     "vintage_year",
     "city",
     "state",
     "area",
     "suburb",
     "rate_type",
     "io_flag",
     "occupancy",
     "lmi_flag",
     "ltv_bucket_orig",
     "ltv_bucket_indexed",
     "seasoning_bucket",
     "dpd_bucket"
    ],
    "type": "string"
   },
   "maxItems": 2,
   "type": "array"
  },
  "filters": {
   "additionalProperties": {
    "items": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "integer"
      }
     ]
    },
    "type": "array"
   },
   "propertyNames": {
    "enum": [
     "deal_id",
     "deal_name",
     "originator",
     "trustee_format",
     "issue_year",
     "vintage_year",
     "city",
     "state",
     "area",
     "suburb",
     "rate_type",
     "io_flag",
     "occupancy",
     "lmi_flag",
     "ltv_bucket_orig",
     "ltv_bucket_indexed",
     "seasoning_bucket",
     "dpd_bucket"
    ]
   },
   "type": "object"
  },
  "time": {
   "anyOf": [
    {
     "properties": {
      "grain": {
       "enum": [
        "month",
        "quarter",
        "year"
       ],
       "type": "string"
      },
      "start": {
       "pattern": "^\\d{4}-(0[1-9]|1[0-2])$",
       "type": "string"
      },
      "end": {
       "pattern": "^\\d{4}-(0[1-9]|1[0-2])$",
       "type": "string"
      },
      "shape": {
       "enum": [
        "series",
        "point"
       ],
       "type": "string"
      }
     },
     "required": [
      "grain",
      "start",
      "end",
      "shape"
     ],
     "type": "object"
    },
    {
     "type": "null"
    }
   ],
   "default": null
  },
  "order": {
   "anyOf": [
    {
     "properties": {
      "metric": {
       "enum": [
        "loan_count",
        "balance_total",
        "arrears_30p_bal",
        "arrears_90p_bal",
        "arrears_90p_cnt",
        "hardship_share_bal",
        "wa_orig_ltv",
        "wa_indexed_ltv",
        "wa_rate",
        "smm_vol",
        "cpr",
        "cdr"
       ],
       "type": "string"
      },
      "direction": {
       "enum": [
        "desc",
        "asc"
       ],
       "type": "string"
      },
      "limit": {
       "maximum": 20,
       "minimum": 1,
       "type": "integer"
      }
     },
     "required": [
      "metric",
      "direction",
      "limit"
     ],
     "type": "object"
    },
    {
     "type": "null"
    }
   ],
   "default": null
  },
  "clarify": {
   "anyOf": [
    {
     "properties": {
      "question": {
       "type": "string"
      },
      "options": {
       "items": {
        "type": "string"
       },
       "maxItems": 4,
       "minItems": 2,
       "type": "array"
      }
     },
     "required": [
      "question",
      "options"
     ],
     "type": "object"
    },
    {
     "type": "null"
    }
   ],
   "default": null
  },
  "unsupported_reason": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "type": "null"
    }
   ],
   "default": null
  }
 },
 "required": [
  "intent"
 ],
 "type": "object"
}
```

- Deviations from PLAN.md or the instruction file: none. The validation error text is
  `<loc>: <msg>` of pydantic's first error, cut to 200 characters; for the 4-metric
  fixture it is `invalid spec from model: metrics: List should have at most 3 items after
  validation, not 4`.

### Step 4.3: entity resolution

- Files: `rmbsq/llm/resolve.py`, `tests/test_resolve.py`.
- Signatures implemented: `deal_aliases(catalog) -> dict[str, str]`,
  `resolve_entities(spec, catalog, aliases) -> QuerySpec`.
- Tests: `test_exact_case_insensitive`, `test_aliases`, `test_deal_id_to_deal_name`,
  `test_fuzzy_accept`, `test_fuzzy_clarify`, `test_fuzzy_tie_clarifies`,
  `test_unknown_unsupported`, `test_flags_and_years`, `test_first_failure_decides`,
  `test_non_answer_unchanged`; result passed.
- Outputs: none.
- Evidence (J.3): every resolution test input, the `rapidfuzz.fuzz.token_set_ratio`
  scores of the top 3 canonical values for each fuzzy-dimension value (an alias scores
  for its deal_name), and the outcome. Scores are shown for alias and exact inputs too,
  though those are decided before the fuzzy step. The clarify-band value was chosen by
  measuring: `Joondalop` scores 88.89 against Joondalup, inside [75, 90).

alias table for 3 deals:
  HARB 2019-1: ['Harbour 19-1', 'HARB 19-1', 'HARB19-1']
  CST 2020-1: ['Coastline 20-1', 'CST 20-1', 'CST20-1']
  RED 2023-1: ['Redgum 23-1', 'RED 23-1', 'RED23-1']

| test | input filters | top 3 token_set_ratio scores (fuzzy dimensions) | outcome |
|---|---|---|---|
| exact | `{"state": ["nsw"]}` | state 'nsw': NSW 100.00, SA 40.00, WA 40.00 | answer {"state": ["NSW"]} |
| exact | `{"originator": ["harb"], "dpd_bucket": ["90+"]}` | originator 'harb': HARB 100.00, RED 28.57, WAT 28.57 | answer {"originator": ["HARB"], "dpd_bucket": ["90+"]} |
| alias | `{"deal_name": ["Harbour 19-1"]}` | deal_name 'Harbour 19-1': HARB 2019-1 100.00, HARB 2021-1 91.67, KOO 2019-1 66.67 | answer {"deal_name": ["HARB 2019-1"]} |
| alias | `{"deal_name": ["HARB 19-1"]}` | deal_name 'HARB 19-1': HARB 2019-1 100.00, HARB 2021-1 88.89, KOO 2019-1 66.67 | answer {"deal_name": ["HARB 2019-1"]} |
| alias | `{"deal_name": ["HARB19-1"]}` | deal_name 'HARB19-1': HARB 2019-1 100.00, HARB 2021-1 87.50, KOO 2019-1 53.33 | answer {"deal_name": ["HARB 2019-1"]} |
| alias | `{"deal_name": ["harbour 19-1"]}` | deal_name 'harbour 19-1': HARB 2019-1 100.00, HARB 2021-1 91.67, KOO 2019-1 66.67 | answer {"deal_name": ["HARB 2019-1"]} |
| alias | `{"deal_name": ["harb19-1"]}` | deal_name 'harb19-1': HARB 2019-1 100.00, HARB 2021-1 87.50, KOO 2019-1 53.33 | answer {"deal_name": ["HARB 2019-1"]} |
| alias | `{"deal_id": ["d001"]}` | - | answer {"deal_id": ["D001"]} |
| id->name | `{"deal_id": ["HARB 2019-1"]}` | - | answer {"deal_name": ["HARB 2019-1"]} |
| id->name | `{"deal_id": ["D004", "KOO19-1"]}` | - | answer {"deal_id": ["D004"], "deal_name": ["KOO 2019-1"]} |
| fuzzy accept | `{"suburb": ["Blacktwon North"]}` | suburb 'Blacktwon North': Blacktown North 93.33, Blacktown South 80.00, Logan North 69.23 | answer {"suburb": ["Blacktown North"]} |
| fuzzy clarify | `{"area": ["Joondalop"]}` | area 'Joondalop': Joondalup 88.89, Boroondara 52.63, Onkaparinga 40.00 | clarify: Which area did you mean by 'Joondalop'? options ['Joondalup', 'Boroondara', 'Onkaparinga'] |
| fuzzy tie | `{"suburb": ["Blacktown"]}` | suburb 'Blacktown': Blacktown Central 100.00, Blacktown North 100.00, Blacktown South 100.00 | clarify: Which suburb did you mean by 'Blacktown'? options ['Blacktown Central', 'Blacktown North', 'Blacktown South'] |
| unknown | `{"suburb": ["Narnia"]}` | suburb 'Narnia': Onkaparinga North 43.48, Penrith North 42.11, Wyndham North 42.11 | unsupported: unknown suburb value 'Narnia' |
| flags | `{"io_flag": ["Y"], "lmi_flag": ["false"]}` | - | answer {"io_flag": ["yes"], "lmi_flag": ["no"]} |
| years | `{"vintage_year": ["2019"]}` | - | answer {"vintage_year": [2019]} |
| years | `{"vintage_year": [2031]}` | - | unsupported: unknown vintage_year value '2031' |
| dpd | `{"dpd_bucket": ["90 plus"]}` | - | unsupported: unknown dpd_bucket value '90 plus' |
| first failure | `{"suburb": ["Narnia"], "area": ["Joondalop"]}` | suburb 'Narnia': Onkaparinga North 43.48, Penrith North 42.11, Wyndham North 42.11<br>area 'Joondalop': Joondalup 88.89, Boroondara 52.63, Onkaparinga 40.00 | unsupported: unknown suburb value 'Narnia' |
| first failure | `{"area": ["Joondalop"], "suburb": ["Narnia"]}` | area 'Joondalop': Joondalup 88.89, Boroondara 52.63, Onkaparinga 40.00<br>suburb 'Narnia': Onkaparinga North 43.48, Penrith North 42.11, Wyndham North 42.11 | clarify: Which area did you mean by 'Joondalop'? options ['Joondalup', 'Boroondara', 'Onkaparinga'] |
| first failure | `{"area": ["Narnia", "Joondalop"]}` | area 'Narnia': Onkaparinga 58.82, Boroondara 50.00, Penrith 46.15<br>area 'Joondalop': Joondalup 88.89, Boroondara 52.63, Onkaparinga 40.00 | unsupported: unknown area value 'Narnia' |
| first failure | `{"area": ["Joondalop", "Narnia"]}` | area 'Joondalop': Joondalup 88.89, Boroondara 52.63, Onkaparinga 40.00<br>area 'Narnia': Onkaparinga 58.82, Boroondara 50.00, Penrith 46.15 | clarify: Which area did you mean by 'Joondalop'? options ['Joondalup', 'Boroondara', 'Onkaparinga'] |

- Deviations from PLAN.md or the instruction file:
  - `test_fuzzy_tie_clarifies` and `test_non_answer_unchanged` are added to the 8 named
    tests.
  - Ties are counted between distinct canonical values, so an alias and its own
    deal_name both scoring 100 are not a tie.
  - A value that resolves to one already in the filter is not added twice.
  - Filters are processed in the spec's own key order: O-39.

### Step 4.4: narration and number guard

- Files: `rmbsq/llm/guard.py`, `rmbsq/llm/narrate.py`, `tests/test_guard.py`,
  `tests/fixtures/llm_responses/narrate_{pass,trip,truncated}.json`.
- Signatures implemented: `number_guard(text, question, display_table, catalog) -> list[str]`,
  `narrate(question, spec, display_table, client, cfg, catalog) -> tuple[str, bool, list[str]]`,
  `template_answer(spec, display_table) -> str`.
- Tests: `test_guard_cases[G01..G13]`, `test_narrate_passes`, `test_narrate_trips_to_template`
  (offending `["51%"]`), `test_template_formats`, `test_truncation_flag`; result passed.
- Outputs: none.
- Evidence (J.4): every guard case, with the catalogue loaded on `small_db` (it holds the
  deal names HARB 2019-1 and CST 2020-1 of table T3).

```
G01 table T1
  question: Which state had the highest 30+ arrears in June 2024?
  text:     In 2024-06, NSW had the highest 30+ arrears at 1.23%, then VIC at 1.05% and QLD at 0.98%.
  expected: []
  actual:   []
  MATCH
G02 table T1
  question: Which state had the highest 30+ arrears in June 2024?
  text:     NSW was highest at 1.32%.
  expected: ['1.32%']
  actual:   ['1.32%']
  MATCH
G03 table T1
  question: What were 30+ arrears by state?
  text:     NSW loans 30-59 days past due and worse made up 1.23% of balance.
  expected: []
  actual:   []
  MATCH
G04 table T1
  question: Show 30+ arrears for the top 3 states in 2024-06.
  text:     Across the top 3 states, NSW led at 1.23%.
  expected: []
  actual:   []
  MATCH
G05 table T2
  question: Balance by originator?
  text:     HARB holds A$412.3m across 12,345 loans.
  expected: []
  actual:   []
  MATCH
G06 table T2
  question: Balance by originator?
  text:     HARB holds about A$412m.
  expected: ['412m']
  actual:   ['412m']
  MATCH
G07 table T2
  question: Loan count by originator?
  text:     HARB has 12345 loans and KOO has 1,204.
  expected: []
  actual:   []
  MATCH
G08 table T2
  question: Loan count by originator?
  text:     HARB has 12,354 loans.
  expected: ['12354']
  actual:   ['12354']
  MATCH
G09 table T2
  question: Balance by originator?
  text:     Both of the 2 originators hold over A$398.0m.
  expected: ['2']
  actual:   ['2']
  MATCH
G10 table T3
  question: Worst deals by 90+ arrears in 2025?
  text:     In 2025, HARB 2019-1 was worst at 2.10%, ahead of CST 2020-1 at 1.75%.
  expected: []
  actual:   []
  MATCH
G11 table T3
  question: Worst deals by 90+ arrears?
  text:     HARB 2019-1 had 2.10 percent of balance 90+ days past due.
  expected: ['2.10']
  actual:   ['2.10']
  MATCH
G12 table T4
  question: Arrears balances by bucket in Q1 2025?
  text:     In 2025-Q1 the 90+ bucket held A$9.8m against A$4.2m at 30-59 days.
  expected: []
  actual:   []
  MATCH
G13 table T4
  question: Arrears balances by bucket?
  text:     The 90+ bucket held A$9.8m, which is 70% of arrears.
  expected: ['70%']
  actual:   ['70%']
  MATCH
```

- Evidence (J.5): the 3 template outputs (3 rows, 12 rows, 0 rows), as in
  `test_template_formats`.

```
--- 3 rows
Result computed from the data (narration withheld because it cited a number not in the table):
- NSW / 2024-06: arrears_30p_bal 1.23%
- QLD / 2024-06: arrears_30p_bal 0.98%
- VIC / 2024-06: arrears_30p_bal 1.05%
--- 12 rows
Result computed from the data (narration withheld because it cited a number not in the table):
- NSW / 2024-01: arrears_30p_bal 1.00%
- NSW / 2024-02: arrears_30p_bal 2.00%
- NSW / 2024-03: arrears_30p_bal 3.00%
- NSW / 2024-04: arrears_30p_bal 4.00%
- NSW / 2024-05: arrears_30p_bal 5.00%
- NSW / 2024-06: arrears_30p_bal 6.00%
- QLD / 2024-01: arrears_30p_bal 1.01%
- QLD / 2024-02: arrears_30p_bal 2.01%
- QLD / 2024-03: arrears_30p_bal 3.01%
- QLD / 2024-04: arrears_30p_bal 4.01%
- … and 2 more rows.
--- 0 rows
Result computed from the data (narration withheld because it cited a number not in the table):
No loans match the filters and dates in the query.
```

- Deviations from PLAN.md or the instruction file:
  - `narrate` takes the catalogue as a 6th argument, because the guard needs the
    catalogue's deal names: O-38.
  - For an empty table, the template prints line 1, then
    `No loans match the filters and dates in the query.`

### Step 4.5: baseline

- Files: `rmbsq/llm/baseline.py`, `tests/test_baseline.py`,
  `tests/fixtures/llm_responses/baseline_{sql,empty}.json`.
- Signatures implemented: `baseline_sql(question, output_columns, client, cfg) -> str`,
  `run_baseline_sql(sql, con, cfg) -> pd.DataFrame | None`, `BaselineError(message)`.
- Tests: `test_baseline_parse`, `test_baseline_timeout`, `test_baseline_cannot_write`,
  `test_baseline_runs_select`; result passed.
- Outputs: none.
- Evidence (J.6): the measured seconds of the timeout test's query with
  `baseline_timeout_s = 1`, and the exception message from `COPY … TO`, printed by
  running the tests' statements on the small profile. This is the same block as in step
  4.0. The test itself, from `pytest tests/test_baseline.py --durations=5`:
  `1.09s call tests/test_baseline.py::test_baseline_timeout` (limit 3 s).

```
timeout 1 s: BaselineError after 1.028 s: INTERRUPT Error: Interrupted!
after interrupt, SELECT 1 -> (1,)
COPY ... TO: BaselineError: Permission Error: Cannot access file "<tmp>/ev/out.csv" - file system operations are disabled by configuration
file created: False
CREATE TABLE t (a INTEGER) -> InvalidInputException: Invalid Input Error: Cannot execute statement of type "CREATE" on database "small" which is attached in read-only mode!
SELECT * FROM read_csv('<tmp>/ev/r.csv') -> PermissionException: Permission Error: Cannot access file "<tmp>/ev/r.csv" - file system operations are disabled by configuration

LINE 1: SELECT * FROM read_csv('<tmp>/ev/r.csv')...
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
SET threads = 4 -> InvalidInputException: Invalid Input Error: Cannot change configuration option ""threads"" - the configuration has been locked
INSTALL httpfs -> PermissionException: Permission Error: Cannot access directory "<home>\.duckdb\extensions\v2.0.0\windows_amd64" - file system operations are disabled by configuration
```

- Deviations from PLAN.md or the instruction file: the `submit_sql` tool has a name and
  the G input schema only, with no description, because G gives none.

### Step 4.6: pipeline and CLI

- Files: `rmbsq/llm/answer.py`, `rmbsq/cli.py`, `pyproject.toml` (`[project.scripts] rmbsq
  = "rmbsq.cli:main"`, F11), `tests/test_answer.py`,
  `tests/fixtures/llm_responses/narrate_s02.json`.
- Signatures implemented: `answer(question, client, con, catalog, cfg) -> Answer`; `main(argv=None) -> int`.
- Tests: `test_answer_end_to_end_replay` (spec call with S02's spec, then narration; the
  table equals the S02 gold with max scaled difference 0.0, the text equals the
  narration), `test_answer_clarify`, `test_answer_unsupported`, `test_cli_cache_miss_exit_2`;
  result passed.
- Outputs: none.
- Evidence: S02 on `small_db` as the pipeline returns it, the narration fixture text, and
  the CLI on a replay miss (installed with `uv pip install -e . --no-deps`):

```
question: What is the balance and loan count by originator?
spec_valid: True  route: agg  guard_tripped: False  offending: []
spec: {"intent":"answer","metrics":["balance_total","loan_count"],"group_by":["originator"],"filters":{},"time":{"grain":"month","start":"2026-09","end":"2026-09","shape":"point"},"order":null,"clarify":null,"unsupported_reason":null}
table:
originator period_label  balance_total  loan_count
       CST      2026-09    22715782.35          42
       KOO      2026-09     8232420.46          17
       RED      2026-09    17797885.18          37
       WAT      2026-09     9577703.34          20
display:
originator period_label balance_total loan_count
       CST      2026-09       A$22.7m         42
       KOO      2026-09        A$8.2m         17
       RED      2026-09       A$17.8m         37
       WAT      2026-09        A$9.6m         20
text: At 2026-09, CST has the largest balance at A$22.7m across 42 loans, followed by RED at A$17.8m across 37 loans. WAT holds A$9.6m across 20 loans and KOO A$8.2m across 17 loans.
calls:
  {'key': 'a6a53e2565cb3784e2e39cf0646a302dd9abe592ecc7988f3c08f0d04068e9f6', 'hit': True, 'latency_s': 1.234, 'input_tokens': 3100, 'output_tokens': 60}
  {'key': 'ac6e676e0e8e64ac4080b2d130622f924950aaa703dbb47dee95ff85a58dced6', 'hit': True, 'latency_s': 1.234, 'input_tokens': 1100, 'output_tokens': 48}
4-metric fixture: (QuerySpec(intent='unsupported', metrics=[], group_by=[], filters={}, time=None, order=None, clarify=None, unsupported_reason='invalid spec from model: metrics: List should have at most 3 items after validation, not 4'), False)
$ rmbsq ask "What is the balance by originator?" --db <small_db>
not in the cache; run with --live
exit code 2
```

- Deviations from PLAN.md or the instruction file:
  - For clarify, the text is the question, a newline, then `Options: a; b; c`.
  - `test_cli_cache_miss_exit_2` runs with the working directory set to a temp folder,
    so the CLI's relative `data/llm_cache/` is empty and no test reads the repo's cache.
    The miss message goes to stderr.

### Step 4.7: docs

- Files: `PLAN.md` (Section 4 rewritten for steps 4.0 to 4.7, committed as 4.7 says),
  `docs/CONVENTIONS_RESOLVED.md` (new rows N1 locked connection, N2 cache key, N3 cache
  file, N4 guard order, N5 strict metric order), `decisions/OPEN.md` (O-37 closed, O-38
  and O-39 raised).
- Signatures implemented: none.
- Tests: none named.
- Outputs: none.
- Evidence: `git show --stat 4da0a0b`:

```
4da0a0b step 4.7: PLAN.md section 4 and conventions for the locked connection, cache key and guard

 PLAN.md                      | 150 ++++++++++++++++++++++++++-----------------
 decisions/OPEN.md            |  38 ++++++-----
 docs/CONVENTIONS_RESOLVED.md |  13 ++++
 3 files changed, 125 insertions(+), 76 deletions(-)
```

- Deviations from PLAN.md or the instruction file: none.

## 4. Full test suite

Command and its complete output (offline, `--disable-socket`), in the working repo.

```
$ .venv/Scripts/python -m pytest -q
........................................................................ [ 39%]
........................................................................ [ 78%]
.......................................                                  [100%]
183 passed, 20 deselected in 64.54s (0:01:04)
$ .venv/Scripts/python -m pytest -q -m full
....................                                                     [100%]
20 passed, 183 deselected in 69.07s (0:01:09)
```

## 5. Determinism

This section writes no file to `outputs/`, and `git status --short outputs` is empty. The
cache file is the one new written artefact: the same response was recorded twice through
record mode (fake SDK, fixed latency) into 2 empty folders, and the files compared.

```
run1 3e4fe162a3de0e81e01d747c3c0bda2f6dcbacdb5e262d4ca90f83b0283a4e44.json bfc67b85967baf2cc333c584ade0f704163848b634e927673e4c06d925f07ece
run2 3e4fe162a3de0e81e01d747c3c0bda2f6dcbacdb5e262d4ca90f83b0283a4e44.json bfc67b85967baf2cc333c584ade0f704163848b634e927673e4c06d925f07ece
```

## 6. Fresh-clone check

Clone into a short temp path, `uv venv --python 3.12`, `uv pip sync requirements-lock.txt`,
run the suite. Paste the commands and the complete output.

Clone path `C:\s4fc\r`, Windows 11, from origin at `4da0a0b`.

```
$ git clone https://github.com/uty101/RMBS-Natural-Language-Query.git r && cd r
$ git log --oneline -1
4da0a0b step 4.7: PLAN.md section 4 and conventions for the locked connection, cache key and guard
$ uv venv --python 3.12 .venv
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip sync --python .venv requirements-lock.txt
(uv pip sync output, last 3 lines)
 + typing-extensions==4.16.0
 + typing-inspection==0.4.4
 + tzdata==2026.6
$ .venv/Scripts/python --version
Python 3.12.13
$ .venv/Scripts/python -m pytest -q
........................................................................ [ 39%]
........................................................................ [ 78%]
.......................................                                  [100%]
183 passed, 20 deselected in 123.47s (0:02:03)
$ .venv/Scripts/python -m pytest -q -m full
....................                                                     [100%]
20 passed, 183 deselected in 69.87s (0:01:09)
```

## 7. Open questions for the reviewer

1. **O-38 (step 4.4): `narrate` needs the catalogue for the number guard.** F.1 gives
   `narrate(question, spec, display_table, client, cfg)`, but the F.2 guard strips the
   catalogue's deal names, which come from the database.
   - (a) A 6th argument `catalog`, which `answer` already holds. **Built.**
   - (b) Keep F.1's signature; `answer` runs the guard and swaps in the template.
2. **O-39 (step 4.3): "Filters are processed in key order".**
   - (a) The spec's own key order, as the model wrote the filters. **Built.**
   - (b) Sorted dimension names.
