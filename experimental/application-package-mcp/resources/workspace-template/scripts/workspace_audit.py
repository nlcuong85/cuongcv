#!/usr/bin/env python3
from pathlib import Path
import runpy
import sys

target = Path(__file__).resolve().parent.parent / "application-kit" / "scripts" / "workspace_audit.py"
if not target.exists():
    raise SystemExit("Install/update application-kit first; workspace_audit.py is missing.")
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")
