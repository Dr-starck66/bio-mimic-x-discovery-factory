#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/"factory"/"brick_registry.json").read_text(encoding="utf-8"))
active=reg["active"]
errors=[]

required={"id","name","stage","purpose","entrypoint","inputs","outputs","metric"}
for b in active:
    miss=required-set(b)
    if miss: errors.append(f"{b.get('id')}: missing {sorted(miss)}")
    if len(b.get("purpose",""))<30: errors.append(f"{b.get('id')}: purpose too vague")
    if not b.get("inputs"): errors.append(f"{b.get('id')}: no inputs")
    if not b.get("outputs"): errors.append(f"{b.get('id')}: no outputs")
    if not b.get("metric"): errors.append(f"{b.get('id')}: no metric")

ids=[b["id"] for b in active]
if len(ids)!=len(set(ids)): errors.append("duplicate brick ids")

# Static integration proof: every active brick must be explicitly referenced by the control plane
# or be an upstream executable whose output the control plane explicitly records.
code=(ROOT/"factory"/"control_plane.py").read_text(encoding="utf-8")
for bid in ids:
    if f'"{bid}"' not in code:
        errors.append(f"{bid}: not referenced by control plane")

if errors:
    print("FAIL")
    print("\n".join(errors))
    raise SystemExit(1)

print(f"PASS — {len(active)} active bricks have purpose/input/output/metric/integration reference")
print(f"Excluded bricks documented: {len(reg.get('excluded',[]))}")
