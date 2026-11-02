"""Regenerate the write-up for the state the repo is in (step 6.4; instruction 06 H).

    python scripts/build_writeup.py

1. The eval is recorded when `outputs/eval_summary.csv` exists, and pending otherwise.
2. The summary outputs, building the canonical database first if it is missing.
3. The figures, the worked example, and the transcripts if recorded.
4. The claims.
5. README.md and docs/DESIGN_RESPONSE.md.
6. The number check on both documents; any unexplained number fails the run.
7. deliverable/results_summary.md, number-checked the same way (instruction 07 F).
8. deliverable/Design_Response.pdf and deliverable/Results_Summary.pdf. A summary still
   above 1 page at the smallest image height fails the run (instruction 07 D.3).
9. Prints the state, the page counts, the summary image height and the files written.

No network code, and no API key is needed: the transcripts replay from data/llm_cache/.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rmbsq.config import load_config  # noqa: E402
from rmbsq.deliverable.claims import CLAIMS_CSV, build_claims  # noqa: E402
from rmbsq.deliverable.examples import transcripts, worked_example  # noqa: E402
from rmbsq.deliverable.writeup import (  # noqa: E402
    SUMMARY, blocks_for, check_documents, eval_recorded, render_documents, write_documents, write_pdfs)
from rmbsq.eval.run import load_items  # noqa: E402
from scripts import build_canonical, build_summary, make_figures  # noqa: E402

DB = ROOT / "data" / "canonical" / "rmbs.duckdb"
OUTPUTS = ROOT / "outputs"


def main() -> int:
    recorded = eval_recorded(OUTPUTS)
    written = []

    if not DB.exists():
        build_canonical.main(["--raw", str(ROOT / "data" / "raw"), "--db", str(DB)])
        written += [DB, OUTPUTS / "pool_monthly.csv", OUTPUTS / "canonical_row_counts.csv"]
    written += build_summary.main(["--db", str(DB), "--outputs", str(OUTPUTS)])

    items = load_items(ROOT / "eval" / "questions.yaml")
    written += make_figures.main(["--db", str(DB), "--outputs", str(OUTPUTS)])
    written.append(worked_example(items, DB, OUTPUTS))
    written += transcripts(items, DB, OUTPUTS, ROOT / "data" / "llm_cache", load_config(ROOT / "config.toml"),
                           recorded)

    claims = build_claims(recorded, OUTPUTS, CLAIMS_CSV)
    written.append(CLAIMS_CSV)

    blocks = blocks_for(OUTPUTS, recorded)
    docs = render_documents(claims, blocks, recorded)
    written += write_documents(docs, ROOT)

    bad = {doc: nums for doc, nums in check_documents(docs, claims, blocks, recorded).items() if nums}
    if bad:
        for doc, nums in bad.items():
            print(f"UNEXPLAINED NUMBERS in {doc}: {nums}", file=sys.stderr)
        return 1

    summary = render_documents(claims, blocks, recorded, SUMMARY)
    written += write_documents(summary, ROOT)
    bad = {doc: nums for doc, nums in check_documents(summary, claims, blocks, recorded).items() if nums}
    if bad:
        for doc, nums in bad.items():
            print(f"UNEXPLAINED NUMBERS in {doc}: {nums}", file=sys.stderr)
        return 1

    cfg = load_config(ROOT / "config.toml")
    pdfs = write_pdfs(docs | summary, cfg, ROOT)
    written += pdfs["paths"]
    print(f"state: {'recorded' if recorded else 'pending'}")
    print(f"Design_Response.pdf: {pdfs['design_pages']} pages (at most {cfg.deliverable.design_max_pages})")
    print(f"Results_Summary.pdf: {pdfs['summary_pages']} pages (exactly {cfg.deliverable.summary_max_pages}), "
          f"image height {pdfs['summary_image_height_cm']} cm")
    if pdfs["design_pages"] > cfg.deliverable.design_max_pages:
        print(f"STOP: Design_Response.pdf has {pdfs['design_pages']} pages", file=sys.stderr)
        return 1
    if pdfs["summary_pages"] != cfg.deliverable.summary_max_pages:
        print(f"STOP: Results_Summary.pdf has {pdfs['summary_pages']} pages at "
              f"{pdfs['summary_image_height_cm']} cm", file=sys.stderr)
        return 1
    for path in written:
        print(Path(path).resolve().relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
