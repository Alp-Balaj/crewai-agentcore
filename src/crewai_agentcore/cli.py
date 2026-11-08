"""Run the crew locally.

    uv run jobfit examples/posting.md examples/profile.md --days 14
"""

import argparse
from pathlib import Path

from .crew import run


def main() -> None:
    p = argparse.ArgumentParser(description="Analyse a job posting and plan your preparation.")
    p.add_argument("posting", type=Path, help="text/markdown file with the job posting")
    p.add_argument("profile", type=Path, help="text/markdown file describing you")
    p.add_argument("--days", type=int, default=14)
    p.add_argument("-o", "--out", type=Path, help="also write the report to this file")
    args = p.parse_args()

    out = run(args.posting.read_text(), args.profile.read_text(), args.days)
    report = f"# Requirements analysis\n\n{out['analysis']}\n\n# Gap analysis and plan\n\n{out['plan']}\n"
    print(report)
    if args.out:
        args.out.write_text(report)
