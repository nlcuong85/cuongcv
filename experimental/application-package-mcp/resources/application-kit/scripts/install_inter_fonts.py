#!/usr/bin/env python3
"""Install the exact Inter font files required by the local cover-letter gate."""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

FONTS = {
    "Inter-Regular.ttf": ("https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfMZg.ttf", "1b08e7fc267a5c7e1d614100f604b83e7e8a0be241f0f288faa2b3ac93a683ba"),
    "Inter-Bold.ttf": ("https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuFuYMZg.ttf", "b37284b5701b6b168dfc770aa1a4ac492106422fd3ba76bc7641e37434e8019c"),
}

root = Path(__file__).resolve().parents[1] / "fonts"
root.mkdir(parents=True, exist_ok=True)
for name, (url, expected) in FONTS.items():
    data = urllib.request.urlopen(url, timeout=30).read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise SystemExit(f"Refusing unexpected Inter asset: {name}")
    (root / name).write_bytes(data)
print("Inter font assets verified.")
