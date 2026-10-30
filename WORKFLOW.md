# Project workflow: chat Claude plans and reviews, Claude Code builds, GitHub holds everything

Paste this whole file at the start of a new project, both into a new chat with Claude and into Claude Code (Claude Code saves it into the repo as `WORKFLOW.md` in session 0). Each side reads the part addressed to it, and both read the rest.

## The cast

- **Me (Utkarsh):** I upload the project outline doc, say yes or no to commits, and paste 1-line prompts into Claude Code. I don't copy and paste instructions or reports between chats.
- **Chat Claude (planner and reviewer):** turns the outline doc into detailed instruction files, publishes them to GitHub, and reviews every finished section by cloning the repo and checking the work itself.
- **Claude Code (builder):** reads one instruction file from the repo, builds exactly that section, pushes, writes a status file, and stops.
- **GitHub:** the only place anything lives. Instructions, code, outputs, reviews, decisions and status are all committed. If it isn't on GitHub, it didn't happen.

---

## Part 1: from outline doc to instructions (the planning chain)

The idea is that detail increases at each stage, so by the time Claude Code writes code there is nothing left for it to decide.

### Stage A: stress-test the outline doc (chat Claude)

Before writing anything, chat Claude reads the outline doc and looks for what's missing or wrong:

- Undefined inputs. For example, "mean-variance" with no definition of where expected returns come from.
- Counts or lists that don't add up.
- Wrong library assumptions. For example, "use sklearn's Ledoit-Wolf" when sklearn shrinks to a different target than the one the doc names.
- Parameter values that don't fit the data frequency.
- Look-ahead traps, such as trading at the same close the decision used.
- Data that isn't point-in-time.
- Constraints that can become infeasible.

Each problem gets a fixed decision. The decisions are listed in the kickoff under "Corrections to the source doc", and the kickoff wins over the outline doc wherever they differ.

### Stage B: the kickoff file (`instructions/00_kickoff.md`), written by chat Claude

This is the spec. It contains:

1. **How the repo is run.** The standing rules (Part 4 below), session numbering, and the status file.
2. **What the project answers.** The research questions, numbered.
3. **Corrections to the source doc.**
4. **Universe, data and sample.** Exact tickers or series, sources, date ranges, and calendar rules.
5. **Conventions.** Timing, units, costs, how returns are computed, and edge-case rules (first period, ruin, missing data).
6. **Methods.** Every formula and parameter value, written out.
7. **Signatures and schemas.** Every function signature and every output table's columns, fixed.
8. **The config file's contents.** Every key and value. No number lives in code.
9. **The section list.** The sections, each split into numbered steps, each step naming its file, its tests and its outputs.
10. **What session 0 must produce.**

### Stage C: session 0 (Claude Code writes `PLAN.md`)

Claude Code expands the section list into `PLAN.md`: one paragraph per step, with the file, the signatures it implements, the tests by name, the outputs, and the review evidence. It adds or removes no step. Anything the kickoff left unspecified gets marked open and raised as a question in the status file, not decided. It also writes:

- `CLAUDE.md`
- `config.toml`
- the review template
- `decisions/`
- `docs/CONVENTIONS_RESOLVED.md`
- the package skeleton
- a placeholder test

It writes no real code in session 0.

### Stage D: per-section instruction files (even more detail, written by chat Claude)

Before each section, chat Claude writes `instructions/NN_section_N.md`. It holds:

- **Approval of the previous section,** saying what chat Claude independently verified and to what tolerance.
- **Decisions** on every open question Claude Code raised, each with its reason.
- **Amendments to the steps** in that section, adding the detail that would otherwise get guessed:
  - exact formulas and edge cases;
  - which data and dates a test uses;
  - the RNG seed and the order of random draws;
  - file formats (float format, line endings);
  - tie-breaking rules;
  - what counts as pass or fail.
- **Measured tolerances.** Before fixing a test tolerance, chat Claude runs the calculation itself on the real data to confirm the tolerance can actually be met. For example, solver accuracy at default settings failed a 1e-7 test, so the instruction set a tighter solver tolerance and recorded the measurement.
- **The review evidence list:** exactly which raw rows, tables and outputs to print in the review file.
- The status file name.

**Rule of thumb:** if two reasonable people could implement a sentence differently, it isn't detailed enough yet.

---

## Part 2: the loop for every section

1. **Chat Claude writes the instruction file** and shows it to me with its file name and commit message.
2. **I say yes.**
3. **Chat Claude publishes it to GitHub,** through my logged-in Chrome tab:
   - It opens `github.com/<user>/<repo>/upload/main/instructions`.
   - It builds the file in the page, then checks its SHA-256 against the local copy before attaching it.
   - It sets the commit message, commits directly to `main`, then clones the repo and checks the committed file byte for byte.
   - One yes covers one commit.
   - If the browser hangs, I bring the GitHub tab to the front and say "retry". If it hangs again, I upload the file myself by drag and drop.
4. **I paste one line into Claude Code:**
   ```
   Pull main, then read instructions/NN_<name>.md from the repo and execute it exactly as written.
   ```
5. **Claude Code builds the whole section,** all steps, without pausing:
   - one commit per step, message `step X.Y: …`;
   - a review file `review/section_N.md`;
   - a fresh-clone test run;
   - a push;
   - the status file `instructions/NN_<name>.status.md`, then a second push, then it stops.
6. **I say "check".**
7. **Chat Claude reviews** (Part 3) and either:
   - **approves:** the next instruction file carries the approval, the decisions, and the next section's detailed steps, all in one file;
   - **sends fixes:** a short follow-up file such as `01b_section_1_completion.md`, with exact fixes and nothing new.
8. Repeat until the last section, then a close-out file for final wording fixes and checks.

Notes:

- Claude Code pushes only at the end of a section, so mid-session work isn't visible on GitHub. Use `git log --oneline -8` locally to see progress.
- If Claude Code hits a gap or a failing test it can't fix within the rules, it stops, writes 2 concrete options into `decisions/OPEN.md` and the status file, and pushes. Chat Claude picks one in the next file.

---

## Part 3: how chat Claude reviews (never trust the summary)

For each section:

1. **Pull the repo and read the status file first,** including the stop reason, if any, and the open questions.
2. **Run the full test suite on a different machine** (Linux, while I'm on Windows), with sockets disabled, installing from the lock file.
3. **Recompute the key numbers independently,** with its own code from the raw data, not by calling the project's functions:
   - weights from its own optimiser;
   - returns from its own backtest loop;
   - intervals from its own bootstrap replay;
   - a hand-worked example for anything tricky.
4. **Look at every chart.** Check that labels are readable, that nothing is misleading (for example, a positive return shown for a fund that went to zero), and that the axes make sense.
5. **Stress-test the claims.** Does a result have an interval that includes zero? Then it can't be called a result. Is a ratio reported at 1 date when it reverses at another?
6. **Check the reviewer's own earlier specs for bugs too.** Twice in project 3 the bug was in chat Claude's instruction, not in Claude Code's work, and the fix was said plainly.
7. **Decide every open question** with a reason and write it into the next instruction file.

---

## Part 4: standing rules for Claude Code (copied into `CLAUDE.md` in session 0)

1. **No design choices.** Every parameter, definition, signature, schema and path comes from the kickoff, `PLAN.md` or an instruction file. If something is unspecified, write 2 options in `decisions/OPEN.md`, finish everything that doesn't depend on it, and report it.
2. **Commits.** One commit per step, message `step X.Y: <one line>`, on `main`. Push at the end of the section. Never force push, rewrite history or amend a pushed commit. Stage files by explicit path, never `git add -A`.
3. **One review file per section,** following `review/TEMPLATE.md` exactly.
4. **Stop conditions:**
   - a data pull fails;
   - an earlier test breaks;
   - a cross-check against a reference library misses its tolerance;
   - a result needs a design choice;
   - a step would need a file outside the section.

   On any of these: write the review and status files, push, stop. Don't work around it.
5. **Tests are fixed.** Never loosen a tolerance, skip, xfail or rewrite a test to pass. If a test seems wrong, stop and say why.
6. **Config is fixed.** Every number lives in `config.toml`. The only exception is constants written inside a formula in an instruction file, which may be literals with a comment citing where the formula is written.
7. **Tests build what they read,** from committed raw data or synthetic data. The suite runs offline with sockets disabled.
8. **No network** outside the one data-pull script. Raw data is pulled once and committed with a manifest of hashes.
9. **Determinism.** Seeds come from config, and running twice gives byte-identical CSVs. LF line endings are enforced by `.gitattributes`, and dependencies are pinned in `requirements-lock.txt`.
10. **Evidence, not summaries.** Every number in a review file is backed by raw rows printed in full.
11. **Instructions and status live in the repo.**
    - Read the named instruction file and never edit it.
    - End every session, including stopped ones, with `instructions/NN_<name>.status.md`, holding: the outcome, the last step reached, any stop reason, every question for the reviewer, and the last 3 commits on origin.
    - Push it, then wait.
12. **Fresh-clone check** at the end of every section: clone into a short temp path, install from the lock file, run the suite, and paste the output.
13. **Precedence.** An instruction file beats `PLAN.md`, which beats the kickoff, which beats the outline doc.
14. **Don't stage `CLAUDE.md` or `PLAN.md`** unless an instruction file says to. Claude Code's own safety check may refuse to edit `CLAUDE.md`; if so, report it, and I'll commit that file myself.

---

## Part 5: repo layout this produces

```
instructions/   00_kickoff.md, NN_<name>.md and NN_<name>.status.md for every session
PLAN.md         the expanded step list
CLAUDE.md       standing rules (+ an "Amendments" section that grows)
config.toml     every parameter
decisions/      OPEN.md (normally empty) and section_N_review.md, the decisions with reasons
docs/           CONVENTIONS_RESOLVED.md, METHODS.md, DESIGN_NOTE.md
review/         TEMPLATE.md and section_N.md, Claude Code's evidence per section
data/raw/       pulled once, committed, with MANIFEST.json hashes
outputs/        tables, figures, results (committed)
scripts/        pull_data.py (the only network code) and run_all.py (regenerates everything)
tests/          fixed tests
```

---

## Part 6: lessons from project 3 (bake these in from day 1)

- **Windows.** Add `.gitattributes` with `* text=auto eol=lf` in session 0, or hashes and byte-identical checks break across machines.
- **Environment.** Python may not be on PATH. Build the venv with `uv`, and commit `requirements-lock.txt` early.
- **Dates.** Month windows must use calendar-month periods. `DateOffset(months=…)` from a last trading day silently drops or adds days.
- **External APIs.** yfinance's `end` date is exclusive. Check every external API's boundary rules.
- **Reference cross-checks.** Read the reference library's source before setting the tolerance, because libraries mix conventions. For example, PyPortfolioOpt's Ledoit-Wolf uses ddof 1 in one place and divides by T in another.
- **Solver tolerances.** Measure them on real inputs before fixing a test.
- **Look-ahead tests.** Separate "information used to decide" from "realised P&L after the decision", or the test will flag legitimate behaviour.
- **Failed outcomes.** Ruined or failed strategies get blank Sharpe ratios, never a flattering number.
- **Small samples.** Bootstrap anything that looks like a finding before writing it up. In project 3 a 126 bp "gain" had an interval from −88 to +329.
- **The write-up.**
  - README tables are generated from the CSVs, with a test that the README matches them.
  - Every prose number is traced to a source row.
  - The instruction lists claims the README must and mustn't make.
- **Browser publishing.** It works best with the GitHub tab in front. Always verify the commit with a fresh clone.

---

## Part 7: how to start a new project

1. Create an empty GitHub repo.
2. In a new chat with Claude: paste this file, upload the project outline doc, and give the repo URL. Ask for the kickoff.
3. Chat Claude stress-tests the doc, writes `instructions/00_kickoff.md`, and asks for a yes to publish it.
4. In Claude Code, paste this file plus:
   ```
   Clone <repo URL>. Save the workflow text above as WORKFLOW.md. Then read instructions/00_kickoff.md from the repo and execute session 0 exactly as written.
   ```
5. Say "check" in the chat when it has pushed. From then on it's the Part 2 loop.
