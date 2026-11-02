# Open decisions

Raised in session 7 (`instructions/07_section_7.md`). Evidence is in
`review/section_7.md`. O-43 and O-44 were both confirmed as (a) by instruction 07 A.

## O-45. Step 7.4: the neutrality test reads `data/raw/`

Instruction 07 E says `test_no_banned_words` reads every text file from `git ls-files`
outside `instructions/` and `.github/`. That includes the committed raw CSVs under
`data/raw/`. CLAUDE.md rule 8 (kickoff 1.4) says tests never read the full raw data,
except the tests marked `full`.

The instruction file has precedence (rule 13), so the test follows E as written. It is not
marked `full`, so it runs in the default suite. It takes about 1 s locally.

- (a) Keep it as written: the default-suite test reads `data/raw/` as text for the phrase
  search only. **This is what is done.**
- (b) Skip `data/raw/` in the default test, and search it in a second test marked `full`.

## O-46. Step 8.1: the pinned SDK rejects `temperature`

**Decided: (b), by instruction 08b A.** Current Claude models reject `temperature` at the
API itself, so (a) would only move the error to the server. `temperature` is removed from
`[llm]`, the request and the cache key in step 8b.1.

Raised in session 8 (`instructions/08_record_eval.md`). Evidence is in
`review/section_8.md`.

- The pinned `anthropic==2.3.0` SDK's `Messages.create()` has no `temperature` parameter.
- Kickoff 6.8 (cache key) and instruction 04 C.1 (request dict) both put `temperature` in
  every request, with the value 0 from `config.toml`.
- `LLMClient._record` passes the request as keyword arguments, so the first record-mode
  call raises a `TypeError` before anything is sent.
- No API call was made.

- (a) In `rmbsq/llm/client.py` `_record`, send `temperature` through `extra_body`. The C.1
  request dict, the cache key and the cache file format stay unchanged.
  - Risk: the API itself may reject `temperature` for `claude-sonnet-5-5`. That would show
    up as a 400 on the first call, and would lead to (b).
- (b) Drop `temperature` from the request and the cache key.
  - This amends kickoff 6.8, kickoff item 10 ("temperature 0") and instruction 04 C.1.
  - It also changes the cache-key tests and the write-up's statement of the eval settings.
