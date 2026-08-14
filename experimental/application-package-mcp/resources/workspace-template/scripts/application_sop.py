#!/usr/bin/env python3
"""Launch the locally installed public application-kit SOP.

The complete SOP lives in application-kit/scripts after the user downloads the
public kit. This wrapper keeps the workspace contract small and contains no
private checker implementation.
"""
from pathlib import Path
import runpy
import sys

target = Path(__file__).resolve().parent.parent / "application-kit" / "scripts" / "application_sop.py"
if not target.exists():
    raise SystemExit("Install/update application-kit first; application_sop.py is missing.")
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")
