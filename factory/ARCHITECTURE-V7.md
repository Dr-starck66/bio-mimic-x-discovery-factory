# BIO-MIMIC X V7 — Brick Utility Architecture

## Non-negotiable rule
**NO DECORATIVE BRICKS.**

A brick may be marked ACTIVE only if it has:
1. a precise purpose,
2. defined inputs,
3. persistent/observable outputs,
4. a metric,
5. an executable integration point,
6. a test or runtime proof.

The daily workflow fails validation if an ACTIVE brick is not present in the runtime usage ledger.

## Why this matters
Previous versions could mention a subsystem without proving it materially affected the run.
V7 makes subsystem usage an auditable artifact.

## Exclusion policy
Historical bricks that do not improve this biomedical research loop are *not* forced into the product.
They are documented under `factory/brick_registry.json -> excluded` with an explicit reason.

This protects the architecture from feature bloat and fake moat.

## Active V7 stack
Ω-OS, Research Director/Scientific Planner, AION-NEXUS, Data Fusion, AgentShield,
Novel Species Hunter, Evidence Network, Ω-MEMORY, Human Bridge, DUALITY-X,
Morpheus, Ω-CAUSAL/Uncertainty, Negative Knowledge Graph, Experiment Forge/Ω-EXPERIMENT,
BENCHMARK-X10, Ω-FOUNDRY/MAP-Elites, Model Immune System/Self-Improvement Gate,
Ω-TELEMETRY, deterministic Decision Engine/Scientific Investment Committee, DEVOPS-X.

## Self-improvement boundary
Ω-FOUNDRY mutates **research policy configuration**, not source code.
The Model Immune System only accepts a policy candidate after measured improvement and false-positive checks.
This avoids uncontrolled self-modifying code while preserving daily learning.
