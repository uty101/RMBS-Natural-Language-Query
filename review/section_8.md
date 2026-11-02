# Review: Section 8, Record the eval

## 1. Outcome

- Instruction file: `instructions/08_record_eval.md`
- Outcome: stopped
- Last step reached: 8.1 (the first call failed before anything was sent)
- Stop reason: 2 of the CLAUDE.md rule 4 stop conditions.
  - A result needs a design choice.
  - A step would need a file outside the section.
  - Details:
    - The pinned SDK, `anthropic==2.3.0` (`requirements-lock.txt`), has no `temperature`
      parameter on `Messages.create()`.
    - The request that kickoff 6.8 and instruction 04 C.1 specify always carries
      `temperature`, so the first call of the record run raised a `TypeError` in the SDK.
    - The fix needs a change to `rmbsq/llm/client.py` and a choice between 2 options
      (O-46).
  - This is not an API failure after the C.4 retries: no request left the machine.

## 2. Commits

```
<this section's only commit holds this file, decisions/OPEN.md and the status file>
```

## 3. Steps

### Step A: key check

- `ANTHROPIC_API_KEY` was present for the record run only, in the environment of a single
  process. It was removed when that process ended.
- No key was written to any file.
- Check output (length and first 7 characters only, A.1):

```
key len=106 prefix=sk-ant-
```

### Step 8.1: Record

- Files: none created. `data/llm_cache/` does not exist, and no `outputs/eval_*` file was
  written.
- Command: `python scripts/run_eval.py --mode record`
- Evidence, the complete output:

```
Traceback (most recent call last):
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\scripts\run_eval.py", line 45, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\scripts\run_eval.py", line 35, in main
    scored = run_eval(items, args.db, args.cache, args.outputs, load_config(ROOT / "config.toml"), args.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\rmbsq\eval\run.py", line 142, in run_eval
    _run(items, LLMClient(cfg, mode="record", cache_dir=cache_dir), db, catalog)
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\rmbsq\eval\run.py", line 129, in _run
    results = pd.concat([run_system(items, client, con, catalog), run_baseline(items, client, con)],
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\rmbsq\eval\run.py", line 85, in run_system
    ans = answer(item.question, client, con, catalog, client.cfg)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\rmbsq\llm\answer.py", line 42, in answer
    spec_raw, spec_valid = question_to_spec(question, client, catalog)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\rmbsq\llm\spec_agent.py", line 93, in question_to_spec
    response = client.call(render_spec_prompt(catalog, client.cfg), [{"role": "user", "content": question}],
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\rmbsq\llm\client.py", line 79, in call
    entry = self._record(key, request)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\rmbsq\llm\client.py", line 99, in _record
    message = self._sdk.messages.create(**kwargs)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Utkarsh\10. Quant Projects\14) RMBS Natural Language Query\.venv\Lib\site-packages\anthropic\_utils\_utils.py", line 294, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
TypeError: Messages.create() got an unexpected keyword argument 'temperature'
exit=1 wall_s=19
```

- The SDK version, and the parameters its `Messages.create` accepts:

```
anthropic==2.3.0
2.3.0
['self', 'max_tokens', 'messages', 'model', 'cache_control', 'container', 'diagnostics', 'inference_geo', 'metadata', 'output_config', 'service_tier', 'speed', 'stop_sequences', 'stream', 'system', 'thinking', 'tool_choice', 'tools', 'user_profile_id', 'workspace_id', 'extra_headers', 'extra_query', 'extra_body', 'timeout']
```

- API calls made: 0. Input tokens: 0. Output tokens: 0. Wall time: 19 s, almost all of it
  setup before the first call.
- Deviations: none. Steps 8.2 to 8.6 were not run.

## 4. Full test suite

Not run. No file under test changed in this session.

## 5. Determinism

Not applicable: nothing was generated.

## 6. Fresh-clone check

Not run: the section stopped at 8.1.

## 7. Open questions for the reviewer

1. **O-46 (step 8.1): the pinned SDK rejects `temperature`.** Details and the 2 options are
   in `decisions/OPEN.md`.
