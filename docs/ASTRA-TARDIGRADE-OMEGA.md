# ASTRA TARDIGRADE Ω

## Purpose

ASTRA TARDIGRADE Ω is a fail-closed resilience brick for autonomous agents, services and robots. It translates experimentally supported tardigrade survival mechanisms into **engineering analogies**, not biological equivalence claims.

The brick has three layers:

1. **TARDI-SHIELD** — integrity protection using cryptographic checkpoints, read/write restrictions and increased verification under stress.
2. **TARDI-DORMANCY** — a minimal survival mode that freezes nonessential work when energy, network or thermal conditions are unsafe.
3. **TARDI-RECOVERY** — a gated restore path that refuses to resume normal work unless checkpoint integrity and all configured recovery conditions pass.

## Evidence boundary

The design is inspired by:

- Hashimoto et al. (2016), *Nature Communications*, DOI `10.1038/ncomms12808`: Dsup improved radiotolerance in cultured human cells and reduced DNA damage.
- Lim et al. (2024), *Communications Biology*, DOI `10.1038/s42003-024-06336-w`: tardigrade SAHS proteins protected selected biological structures/cells during desiccation.
- Kirtane et al. (2025), *Nature Biomedical Engineering*, DOI `10.1038/s41551-025-01360-5`: local transient Dsup mRNA expression reduced radiation-induced damage in mouse oral/rectal tissues while preserving radiotherapy efficacy in the reported model.

These papers support the **biological mechanisms**. They do not prove that the software state machine below is biologically equivalent or intrinsically superior to other resilience architectures.

## Runtime states

- `ACTIVE` / `PASS`: every configured gate passes.
- `SHIELDED` / `PARTIAL`: dependency/failure budget degraded; destructive or nonessential work is blocked.
- `DORMANT` / `PARTIAL`: energy, thermal or required-network condition is unsafe; state is checkpointed and workload minimized.
- `RECOVERY` / `PARTIAL`: checkpoint is valid, but one or more resume gates still fail.
- `QUARANTINED` / `FAIL`: integrity corruption or a corrupted checkpoint was detected.

## Quick use

```bash
python factory/tardigrade_omega.py --scenario healthy
python factory/tardigrade_omega.py --scenario low-energy
python factory/tardigrade_omega.py --scenario integrity-failure
python factory/tardigrade_omega.py --evidence
python factory/tardigrade_omega.py --emit reports/tardigrade-omega
```

## Integration contract

Call `decide(Signals(...))` before nonessential or destructive work. Persist state using `make_checkpoint(...)`. Before restoring from dormancy or failure, call `recovery_gate(checkpoint, signals)` and require `status == PASS`.

Never convert `PARTIAL`, `FAIL` or `UNVERIFIED` to PASS in a caller.

## Anti-false-PASS invariants

- A single integrity error above the configured threshold forces `QUARANTINED/FAIL`.
- A modified checkpoint cannot be restored.
- Low energy enters dormancy at or below the dormancy threshold.
- Recovery uses a higher resume threshold to avoid rapid oscillation.
- Required network failure blocks network-dependent execution.
- Dependency failure blocks nonessential work.
- PASS requires all configured recovery gates.
- Every biology→engineering mapping carries an explicit analogy boundary.

## Intended reuse

This brick is suitable as a resilience layer beneath BIO-MIMIC X, ASTRA HARNESS, ANT Robotics and future autonomous systems. Physical robot actuation must remain separately permissioned and safety-gated; this brick does not authorize commands to real hardware.
