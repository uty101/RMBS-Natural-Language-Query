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
