# ASTRA Ω — USB read-only interoperability audit (2026-11-28)

## Evidence
Python 3.13.5, independent offline synthetic fixtures; no physical USB access, no spend.
Upstream source: https://github.com/emirmrkaljevic/usb-rea (MIT, Emir Mrkaljević), declared version 0.7.14.
The local source files retrieved from GitHub were reconstructed and matched Git blob hashes exactly:
- src/usb_rea/pcap.py: 79c6806021097ce3fc6116895c6fb882a504f7a0
- src/usb_rea/model.py: 71288fc973565d4997fbc90294f91798b9fe105c

Commands, from this directory with these upstream modules available on PYTHONPATH:
- python -m unittest -v test_usb_rea_parser: 9 tests, 6 OK, 3 failures (0.014 s).
- python -m unittest -v test_astra_usb_guard: 8 tests, all OK (0.007 s).
- Installation/clone of full package: FAIL (DNS resolution for github.com); public trace acquisition: FAIL (binary download blocked); upstream demos and actual physical devices: UNVERIFIED.

Baseline failures:
1. Transfer.key() conflates same device address/endpoint on different buses.
2. find_ids() attributes a synthetic descriptor response on one bus to a request on another bus.
3. usbmon record declaring five captured bytes but carrying one is accepted.
These are robustness counterexamples under deliberately strict industrial acceptance criteria, not established exploitable vulnerabilities. The baseline failures must remain visible.

Guard: rejects mixed-bus captures and USB transfer length/header inconsistencies in tested linktypes 189, 220, 249; delegates decoding to upstream. Normal Linux, Linux MMAPPED and Windows synthetic inputs accepted. Mixed-bus and truncated cases rejected. Policy is intentionally restrictive, not a general PCAP integrity validator; upstream iterator may silently stop or interpret malformed outer containers, USB bus can contain multiple devices or change identity over time, and the guard reads the file twice (immutable offline inputs only). No execution of generated drivers, no automatic writes to hardware, no clinical claims.

## Reuse contract (proposed, NOT integrated)
- BIO-MIMIC X: provenance for measurements (instrument identity, firmware, calibration, units, timing, capture hash); no inference of medical validity from transport.
- NEXUS: read-only anomaly boundary; reject ambiguity and quarantine incomplete traces; not a trained anomaly detector.
- MYTHOS ASTRA: independent held-out fixtures, explicit negative controls, source fingerprints, no promotion of skipped tests to PASS.
- ANT Robotics: approved device-specific adapters, simulation and disconnected tests before physical actuation.
- Ghost Operator: explicit allowlisting and operator approval for commands; no automatic execution of inferred protocols.
- DC ENERGY: independent measurement validation before any control of physical equipment.

Existing BIO-MIMIC X README documents Evidence Network, Negative Knowledge Graph, AgentShield and SHA-256 experiment replay; reuse these when implementing integration. NEXUS and Ghost Operator README inspected, actual integration APIs not established. ANT reference found in publications/README.md. No new standalone repository.

Next experiment: run full upstream demos (fan/lamp/lcd/dial) and public pinned USB captures from tests/test_public_pcaps.py: USB memory stick and USB3 Vision camera. Require actual non-skipped results and hashes. Separate parser acceptance, protocol inference accuracy, generated-driver mock tests, and hardware validation.

## Persistence
Draft branch only, no production changes; three Python files verified on GitHub against local blob hashes:
- astra_usb_guard.py: 3441050b92724b9a103eac933d7f173e80810329
- test_usb_rea_parser.py: 5b4bcbad69ff86e1b8f00cf33b7c37348aa31c89
- test_astra_usb_guard.py: 405b447f9702b0884e33702139bb73a4436fdc69
