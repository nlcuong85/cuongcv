#!/usr/bin/env python3
from pathlib import Path
import runpy
import sys

target = Path(__file__).resolve().parent.parent / "application-kit" / "scripts" / "ats_text_extract.py"
if not target.exists():
    raise SystemExit("Install/update application-kit first; ats_text_extract.py is missing.")
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")
