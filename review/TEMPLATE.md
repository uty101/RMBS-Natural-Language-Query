# Review: Section N, <section title>

Follow this template exactly. Every number below must be backed by raw rows or raw
output printed in full in this file (CLAUDE.md rule 10). No paraphrased results.

## 1. Outcome

- Instruction file: `instructions/NN_<name>.md`
- Outcome: complete | stopped
- Last step reached: X.Y
- Stop reason (if stopped): <the stop condition from CLAUDE.md rule 4, and the measured value>

## 2. Commits

Output of `git log --oneline` for this section's commits, oldest last, pasted verbatim.

```
<paste>
```

## 3. Steps

One subsection per step, in order.

### Step X.Y: <title>

- Files: <paths created or changed>
- Signatures implemented: <as in PLAN.md>
- Tests: <test ids>, result <passed/failed>
- Outputs: <paths, with row counts>
- Evidence (as listed for this step in PLAN.md or the instruction file):

```
<raw rows, tables or command output, printed in full>
```

- Deviations from PLAN.md or the instruction file: none | <each, with reason>

## 4. Full test suite

Command and its complete output (offline, `--disable-socket`).

```
<paste>
```

## 5. Determinism

The outputs regenerated twice and compared byte for byte (SHA-256 of each file, both runs).

```
<paste>
```

## 6. Fresh-clone check

Clone into a short temp path, `uv venv --python 3.12`, `uv pip sync requirements-lock.txt`,
run the suite. Paste the commands and the complete output.

```
<paste>
```

## 7. Open questions for the reviewer

Numbered. Each one names the step, what is unspecified, and 2 concrete options.
Same list as `decisions/OPEN.md` and the status file. "None" if empty.
