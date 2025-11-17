#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all_excels.py
-----------------
Find all Excel files under a given directory and run
`01_xlsx_to_json_2020년모두제외.py` on each, storing outputs in an outdir.

Usage:
  python preprocess_model/run_all_excels.py --input-dir "/Users/mac/Downloads/21대 소위원회" --outdir "/Users/mac/vscode/K-Legisight/preprocess_model/output"

This script calls the existing converter script as a subprocess for each Excel file.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import shlex
from pathlib import Path
from typing import Iterator, List, Tuple


DEFAULT_INPUT_DIR = "/Users/mac/Downloads/21대 소위원회"
THIS_DIR = Path(__file__).resolve().parent
DEFAULT_SCRIPT = THIS_DIR / "01_xlsx_to_json_2020년모두제외.py"
DEFAULT_OUTDIR = THIS_DIR / "output"


def find_excel_files(root: Path) -> Iterator[Path]:
    """Yield Excel files (.xlsx, .xls, .xlsm) under root (recursively)."""
    exts = {".xlsx", ".xls", ".xlsm"}
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def run_converter(script: Path, excel: Path, outdir: Path, python_exe: str = sys.executable) -> Tuple[int, str]:
    """Run the converter script on a single excel file.

    Returns (returncode, combined_stdout_stderr).
    """
    cmd = [python_exe, str(script), "--excel", str(excel), "--outdir", str(outdir)]
    print("Running:", " ".join(shlex.quote(x) for x in cmd))
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return completed.returncode, completed.stdout


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run converter over all Excel files in a directory")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR, help="Root directory to search for Excel files")
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR), help="Directory where converter writes JSON outputs")
    parser.add_argument("--script", default=str(DEFAULT_SCRIPT), help="Path to converter script (01_xlsx_to_json_2020년모두제외.py)")
    parser.add_argument("--python", default=sys.executable, help="Python executable to run the converter script")
    args = parser.parse_args(argv)

    input_root = Path(args.input_dir).expanduser()
    script = Path(args.script).expanduser()
    outdir = Path(args.outdir).expanduser()

    if not input_root.exists():
        print(f"Input directory not found: {input_root}")
        return 2
    if not script.exists():
        print(f"Converter script not found: {script}")
        return 3

    outdir.mkdir(parents=True, exist_ok=True)

    files = list(find_excel_files(input_root))
    if not files:
        print(f"No Excel files found under: {input_root}")
        return 0

    summary: List[Tuple[Path, int]] = []

    for excel in files:
        rc, out = run_converter(script, excel, outdir, python_exe=args.python)
        print(out)
        summary.append((excel, rc))

    print("\nSummary:")
    for p, rc in summary:
        status = "OK" if rc == 0 else f"FAIL({rc})"
        print(f"  {p} -> {status}")

    # exit code: 0 if all OK, otherwise 1
    if all(rc == 0 for _, rc in summary):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
