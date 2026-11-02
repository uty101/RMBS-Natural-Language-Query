# Status: session 8 (08_record_eval)

## Outcome

Stopped at step 8.1. Evidence is in `review/section_8.md`.

- Last step reached: 8.1. Its first call failed before any request was sent.
- Stop reason: 2 of the CLAUDE.md rule 4 stop conditions.
  - A result needs a design choice.
  - A step would need a file outside the section.
  - Details:
    - The pinned SDK, `anthropic==2.3.0`, has no `temperature` parameter on
      `Messages.create()`.
    - The request specified in kickoff 6.8 and instruction 04 C.1 always carries
      `temperature`.
    - So `run_eval.py --mode record` raised
      `TypeError: Messages.create() got an unexpected keyword argument 'temperature'`
      on its first call.
- Key: present for the record run.
- API calls made: 0. Tokens: 0 in, 0 out. Wall time: 19 s.
- Nothing was generated. `data/llm_cache/` does not exist and no `outputs/eval_*` file was
  written.
- Steps 8.2 to 8.6 were not run, and the write-up stays in the pending state.

## Questions for the reviewer

1. **O-46 (step 8.1): the pinned SDK rejects `temperature`.**
   - (a) Send `temperature` through `extra_body` in `LLMClient._record`. The request dict,
     the cache key and the cache files stay as specified.
     - If the API then rejects `temperature` for the model, (b) is needed.
   - (b) Drop `temperature` from the request and the cache key. This amends kickoff 6.8,
     kickoff item 10 and instruction 04 C.1.

Once one is chosen, instruction 08 can be rerun from 8.1 with the key set.

## Last 3 commits on origin (before this session's commit)

```
4c2e235 instruction 08: record the eval once and regenerate the write-up
bac613a MIT licence
6305cf3 section 7: status file
```
