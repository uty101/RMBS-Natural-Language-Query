# Status: session 8b (08b_drop_temperature)

## Outcome

Stopped at step 8.1. Step 8b.1 is complete. Evidence is in `review/section_8.md`, which
replaces the earlier stopped version.

- 8b.1 is done and committed as `5f309fd`.
  - `temperature` is gone from `[llm]`, `Llm`, the request and the cache key.
  - `PLAN.md` step 4.1 and `CONVENTIONS_RESOLVED.md` N2 are updated, and O-46 is marked
    decided (b).
  - Both templates were recopied, and the README, the design response and its PDF were
    re-rendered (still pending).
  - `pytest -q`: 240 passed. `pytest -q -m full`: 57 passed, 1 skipped.
- Last step reached: 8.1.
- Stop reason: instruction 08 8.1, a call failed and C.4 does not retry it. It also needs
  a design choice (O-47) in files outside the section.
  - The API returned HTTP 400:
    `tool_choice: type "tool" and "any" are not supported for this model.`
  - Both the spec call and the baseline force their tool, as kickoff 6.8 and instruction
    04 D.2 require.
- Key: present for the record run.
- API calls made: 1 (rejected). Tokens: 0 in, 0 out. Wall time: 17.6 s.
- Nothing was cached and no `outputs/eval_*` file was written. Steps 8.2 to 8.6 were not
  run.

## Questions for the reviewer

1. **O-47 (step 8.1): the model rejects a forced `tool_choice`.**
   - (a) Use `tool_choice={"type": "auto"}` with the same single tool, and tell the model
     in each system prompt to answer only through it.
     - A missing tool block already scores as `unsupported` or as the baseline's empty SQL.
     - This amends kickoff 6.8, instruction 04 D.2 and the baseline's tool line, and the
       prompts.
   - (b) Replace the forced tool with structured output (`output_config` with the
     `QuerySpec` and `{sql}` schemas), and parse the JSON text.
     - This changes C.1, the cache key, both agents' parsing and their tests.

Once one is chosen, 8.1 can be rerun with the key set.

## Last 3 commits on origin (before this session's push)

```
1ac22d5 instruction 08b: drop temperature from the LLM request, then record the eval
444cd1c section 8: stopped at 8.1, the pinned SDK rejects temperature (O-46)
4c2e235 instruction 08: record the eval once and regenerate the write-up
```
