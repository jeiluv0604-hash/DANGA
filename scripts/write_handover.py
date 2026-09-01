# -*- coding: utf-8 -*-
"""Legacy-safe HANDOVER verifier.

HANDOVER.md is now maintained as the authoritative document.  This script no
longer overwrites it with the former Phase 5 template.
"""
from pathlib import Path


root = Path(__file__).resolve().parents[1]
handover = root / "HANDOVER.md"
content = handover.read_text(encoding="utf-8")

required_markers = (
    "v1.2.0",
    "Phase 6",
    "담가화로구이",
    "SYNTHETIC",
    "UNVERIFIED POLICY",
    "245 PASS",
)
missing = [marker for marker in required_markers if marker not in content]
if missing:
    raise SystemExit(f"HANDOVER.md is incomplete; missing markers: {missing}")

print("HANDOVER.md Phase 6 markers verified; no file was overwritten.")
