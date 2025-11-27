#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
all_xlsx_to_json_x.py
---------------------
Find all Excel files under `congress_data` and run `xlsx_to_json_x.py` on each,
saving outputs into `model_prep/interim`.

Usage:
  python all_xlsx_to_json_x.py
  python all_xlsx_to_json_x.py --input-dir "C:/pythonproject/k_legisight/congress_data" --outdir "C:/pythonproject/k_legisight/model_prep/committee_output"
"""

from __future__ import annotations
import argparse
import subprocess
import sys
import shlex
from pathlib import Path
from typing import Iterator, List, Tuple

print(">>> Running file:", __file__)

# ===============================
# 🔵 DEFAULT PATHS (YOUR PROJECT)
# ===============================
DEFAULT_INPUT_DIR = Path("C:/pythonproject/k_legisight/congress_data")
DEFAULT_SCRIPT = Path("C:/pythonproject/k_legisight/model_prep/xlsx_to_json_x.py")
DEFAULT_OUTDIR = Path("C:/pythonproject/k_legisight/model_prep/committee_output")


def find_excel_files(root: Path) -> Iterator[Path]:
    """Yield Excel files (.xlsx, .xls, .xlsm) under root recursively."""
    exts = {".xlsx", ".xls", ".xlsm"}
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def run_converter(script: Path, excel: Path, outdir: Path, python_exe: str = sys.executable) -> Tuple[int, str]:
    """Run xlsx_to_json_x.py for the given Excel file."""
    cmd = [python_exe, str(script), "--excel", str(excel), "--outdir", str(outdir)]
    print("Running:", " ".join(shlex.quote(x) for x in cmd))
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return completed.returncode, completed.stdout


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run xlsx_to_json_x.py on all Excel files in a directory")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR), help="Directory containing Excel files")
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR), help="Directory where JSON files will be saved")
    parser.add_argument("--script", default=str(DEFAULT_SCRIPT), help="Path to xlsx_to_json_x.py script")
    parser.add_argument("--python", default=sys.executable, help="Python executable to run converter script")
    args = parser.parse_args(argv)

    input_root = Path(args.input_dir)
    script = Path(args.script)
    outdir = Path(args.outdir)

    if not input_root.exists():
        print(f"❌ Input directory not found: {input_root}")
        return 2
    if not script.exists():
        print(f"❌ Converter script not found: {script}")
        return 3

    outdir.mkdir(parents=True, exist_ok=True)

    files = list(find_excel_files(input_root))
    if not files:
        print(f"⚠ No Excel files found under: {input_root}")
        return 0

    summary: List[Tuple[Path, int]] = []
    for excel in files:
        rc, out = run_converter(script, excel, outdir, python_exe=args.python)
        print(out)
        summary.append((excel, rc))

    print("\n================ SUMMARY ================")
    for p, rc in summary:
        status = "OK" if rc == 0 else f"FAIL({rc})"
        print(f"{p} → {status}")

    return 0 if all(rc == 0 for _, rc in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
