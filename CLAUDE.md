# CLAUDE.md: standing rules for Claude Code in this repo

Project: governed natural language queries over synthetic loan-level RMBS data.
Package `rmbsq`, Python 3.12, venv built with `uv`. The spec is
`instructions/00_kickoff.md`; the step list is `PLAN.md`; the process is `WORKFLOW.md`.

Note: a `CLAUDE.md` in a parent folder (`C:\Utkarsh\CLAUDE.md`) describes a different
project. It does not apply here.

## Environment

```bash
uv venv --python 3.12 .venv
uv pip sync --python .venv requirements-lock.txt
.venv/Scripts/python -m pytest -q          # Linux/macOS: .venv/bin/python
```

`requirements-lock.txt` is generated with
`uv pip compile pyproject.toml --extra test --universal --python-version 3.12 -o requirements-lock.txt --no-header`.
pytest runs with `--disable-socket` and `pythonpath = ["."]` from `pyproject.toml`.

## Standing rules (WORKFLOW.md Part 4, amended by kickoff 1.3, 1.4, 1.6, 1.7 and 1.8)

1. **No design choices.** Every parameter, definition, signature, schema and path comes
   from the kickoff, `PLAN.md` or an instruction file. If something is unspecified, write
   2 options in `decisions/OPEN.md`, finish everything that doesn't depend on it, and
   report it.
2. **Commits.** One commit per step, message `step X.Y: <one line>`, on `main`. Push at
   the end of the section. Never force push, rewrite history or amend a pushed commit.
   Stage files by explicit path, never `git add -A`.
3. **One review file per section,** `review/section_N.md`, following `review/TEMPLATE.md`
   exactly.
4. **Stop conditions:**
   - a data generation run fails (there is no data pull, see rule 8);
   - an earlier test breaks;
   - a cross-check against a reference library misses its tolerance;
   - a result needs a design choice;
   - a step would need a file outside the section.

   On any of these: write the review and status files, push, stop. Don't work around it.
5. **Tests are fixed.** Never loosen a tolerance, skip, xfail or rewrite a test to pass.
   If a test seems wrong, stop and say why.
6. **Config is fixed.** Every number lives in `config.toml` (tables in `config/*.csv`).
   The only exception is constants written inside a formula in an instruction file,
   which may be literals with a comment citing where the formula is written.
7. **Tests build what they read,** from committed raw data or synthetic data. The suite
   runs offline with sockets disabled.
8. **Network and data (kickoff 1.3 and 1.4, replacing WORKFLOW rule 8).**
   - There is no data pull. Data is generated deterministically by
     `scripts/generate_data.py`, which has no network code.
   - The only network code in the repo is `rmbsq/llm/client.py` in `record` mode, called
     only by `scripts/run_eval_live.py` and by `rmbsq ask --live`. Everything else,
     including the whole test suite, runs in `replay` mode from `data/llm_cache/` with
     sockets disabled.
   - Generated raw files are committed under `data/raw/` with `data/raw/MANIFEST.json`
     holding SHA-256 hashes.
   - Tests never read the full raw data. They generate the `small` profile in a temp
     folder (`[profiles.small]`). The exceptions are the tests marked `full` (rule 18).
9. **Determinism.** Seeds come from config, and running twice gives byte-identical CSVs.
   LF line endings are enforced by `.gitattributes`, and dependencies are pinned in
   `requirements-lock.txt`.
10. **Evidence, not summaries.** Every number in a review file is backed by raw rows
    printed in full.
11. **Instructions and status live in the repo.**
    - Read the named instruction file and never edit it.
    - End every session, including stopped ones, with `instructions/NN_<name>.status.md`,
      holding: the outcome, the last step reached, any stop reason, every question for the
      reviewer, and the last 3 commits on origin.
    - Push it, then wait.
12. **Fresh-clone check** at the end of every section: clone into a short temp path,
    install from the lock file, run the suite, and paste the output.
13. **Precedence.** An instruction file beats `PLAN.md`, which beats the kickoff, which
    beats the outline notes.
14. **Don't stage `CLAUDE.md` or `PLAN.md`** unless an instruction file says to. Claude
    Code's own safety check may refuse to edit `CLAUDE.md`; if so, report it, and the
    user commits that file.
15. **No gates (kickoff 1.6).** Do not stop or wait at any gate the kickoff or the
    instruction file doesn't name as a stop condition. Build the whole section.
16. **Neutrality (kickoff 1.7).** The repo and its write-up stay neutral, including
    commit messages. The exact rule is kickoff 1.7; the word list for the check is
    supplied in instruction 07 (step 7.5). Do not quote that word list outside
    `instructions/`.
17. **Two audiences, two outputs (kickoff 1.8).** The repo is the evidence. The send pack
    in `deliverable/` (Section 7) is what a reader opens first: a written design response
    PDF and a 1 page results summary PDF. Every number in either PDF is generated from a
    committed CSV, never typed by hand. Any covering note is drafted outside the repo.
18. **Full-profile tests (instruction 01, O-5).** Tests marked `full` read or regenerate
    the full profile. Run `pytest -m full` in every review and fresh-clone check.

## Sessions

Session N builds all of Section N and nothing else. Session 0 built the plan and
scaffolding only. 7 sections, 8 sessions in all. Session 0's status file is
`instructions/00_kickoff.status.md`.

## Amendments

- Instruction 01 (step 1.0): rule 18 added. The instruction calls it rule 17, but 17 was
  already taken by the kickoff 1.8 rule, so it is numbered 18 and rule 17 is kept. Rule 8
  now refers to the `full` marker, which replaced `calibration` (O-5).
