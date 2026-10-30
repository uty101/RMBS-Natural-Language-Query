"""Command line entry point: rmbsq ask (instruction 04 H). Step 4.6.

    rmbsq ask "<question>" [--live] [--show-sql] [--db PATH]

Replay is the default and reads only `data/llm_cache/`; `--live` uses record mode, the
only path that may call the API. Prints the text, then the display table, then with
`--show-sql` the Oracle SQL. A cache miss in replay exits with code 2.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rmbsq.config import load_config
from rmbsq.db import connect_readonly
from rmbsq.llm.answer import answer
from rmbsq.llm.client import CacheMiss, LLMClient
from rmbsq.semantic.catalog import ROOT, load_catalog

DEFAULT_DB = Path("data/canonical/rmbs.duckdb")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rmbsq")
    sub = ap.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="answer a question from the canonical database")
    ask.add_argument("question")
    ask.add_argument("--live", action="store_true", help="record mode: call the API on a cache miss")
    ask.add_argument("--show-sql", action="store_true", help="print the Oracle SQL")
    ask.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / "config.toml")
    catalog = load_catalog(db=args.db)
    client = LLMClient(cfg, mode="record" if args.live else "replay")
    con = connect_readonly(args.db)
    try:
        result = answer(args.question, client, con, catalog, cfg)
    except CacheMiss:
        print("not in the cache; run with --live", file=sys.stderr)
        return 2
    finally:
        con.close()

    print(result.text)
    if result.display is not None:
        print()
        print(result.display.to_string(index=False))
    if args.show_sql and result.sql_oracle is not None:
        print()
        print(result.sql_oracle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
