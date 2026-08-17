#!/usr/bin/env python3
"""Compatibility wrapper for the Application SOP review gates.

The gate state lives in application_sop.py. This entry point prevents agents
from treating a free-form local checker as a replacement for the private MCP.
"""
from pathlib import Path
import runpy
import sys

target = Path(__file__).with_name("application_sop.py")
allowed = {
    "review-cv",
    "review-cover",
    "review-interview-prep",
    "review-writing",
    "record-ats-cv",
    "finalize-cv",
    "finalize-cover-letter",
    "finalize-interview-prep",
    "finalize-writing",
}
if len(sys.argv) < 2 or sys.argv[1] not in allowed:
    raise SystemExit("Use application_quality_loop.py review-cv|review-cover|review-interview-prep|review-writing|record-ats-cv|finalize-cv|finalize-cover-letter|finalize-interview-prep|finalize-writing with Application SOP arguments.")
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")
