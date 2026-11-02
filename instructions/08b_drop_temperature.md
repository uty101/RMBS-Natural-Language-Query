# 08b Drop temperature, then record the eval

Session 8b instructions for Claude Code. Remove `temperature` from the LLM request, then carry out instruction 08 from step 8.1 to the end, unchanged. This file beats `PLAN.md`, `08_record_eval.md` and the kickoff (rule 13). Status file: `instructions/08b_drop_temperature.status.md`.

`ANTHROPIC_API_KEY` must be set in the environment, under the same rules as instruction 08 A.

---

## A. O-46: (b)

Option (a) wouldn't work. Current Claude models reject `temperature` at the API itself, with HTTP 400 "temperature is deprecated". This has been reported for every Claude 4.7 and later model, including the 5.x family this repo uses. The SDK removing the parameter follows the API. Sending it through `extra_body` would move the error from the SDK to the server.

So `temperature` leaves the request and the cache key. That amends:

- kickoff 6.8 and item 10;
- instruction 04 C.1;
- `docs/CONVENTIONS_RESOLVED.md` N2.

The run is no longer pinned to a sampling temperature. The recorded cache is what makes it reproducible, and both documents now say so.

---

## B. Steps

**8b.1 Remove temperature.**

- `config.toml`: delete `temperature = 0` from `[llm]`.
- `rmbsq/config.py`: delete the `temperature` field.
- `rmbsq/llm/client.py`: the request dict becomes `{model, max_tokens, system, messages, tools, tool_choice}`.
- Fix any test that builds a request or a config by hand. No test tolerance changes.
- `PLAN.md` step 4.1 and `docs/CONVENTIONS_RESOLVED.md` N2: remove temperature.
- `decisions/OPEN.md`: mark O-46 decided (b).
- Copy `instructions/06_templates/README.md.tmpl` and `instructions/06_templates/DESIGN_RESPONSE.md.tmpl` again, byte for byte, to `templates/`. Chat Claude changed 1 limitation line in each from "run once at temperature 0" to say that current models take no temperature and the cache makes the run reproducible.
- Run `python scripts/build_writeup.py`. It is still in the pending state, so this re-renders the README, the design response and both PDFs with the new line.
- Run both pytest commands, which must pass with the usual 1 skip.
- Commit as `step 8b.1: drop temperature from the LLM request (O-46 b)`, with `PLAN.md` included.

**8b.2 Record.** Carry out instruction 08 B, from 8.1 to 8.6, exactly as written. The commit messages and review evidence are as instruction 08 says, but write the review as `review/section_8.md`, replacing the stopped version, and end with this status file rather than `08_record_eval.status.md`.
