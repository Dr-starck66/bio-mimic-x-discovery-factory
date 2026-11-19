#!/usr/bin/env bash
# Source-pinned, zero-Actions HAND2 cross-assembly mapping over ALL reference contigs.
# Usage: bash validation/run_hand2_minimap2_parts.sh old_contigs_dir new_contigs_dir old_hand2.fa new_hand2.fa output_dir
set -euo pipefail
if [[ $# -ne 5 ]]; then echo 'Usage: script old_parts new_parts old_query.fa new_query.fa output_dir' >&2; exit 2; fi
old_dir="$1"; new_dir="$2"; old_query="$3"; new_query="$4"; out="$5"
command -v minimap2 >/dev/null || { echo 'FAIL: minimap2 absent' >&2; exit 2; }
command -v node >/dev/null || { echo 'FAIL: node absent' >&2; exit 2; }
command -v sha256sum >/dev/null || { echo 'FAIL: sha256sum absent' >&2; exit 2; }
mkdir -p "$out"
: > "$out/legacy_to_modern.paf"; : > "$out/modern_to_legacy.paf"
: > "$out/references_sha256.txt"
# These FASTA files must be a checked, exhaustive partition of the two NCBI assemblies
# (including unplaced scaffolds), with exactly one sequence per filename. This script
# does not independently certify their completeness.
mapfile -d '' new_parts < <(find "$new_dir" -type f -name '*.fa' -print0 | sort -z)
mapfile -d '' old_parts < <(find "$old_dir" -type f -name '*.fa' -print0 | sort -z)
if [[ ${#new_parts[@]} -eq 0 || ${#old_parts[@]} -eq 0 ]]; then echo 'FAIL: missing FASTA parts' >&2; exit 2; fi
for f in "${new_parts[@]}"; do
 sha256sum "$f" >> "$out/references_sha256.txt"
 minimap2 -x asm5 -c -N 200 -p 0.5 --secondary=yes -t 2 "$f" "$old_query" >> "$out/legacy_to_modern.paf"
done
for f in "${old_parts[@]}"; do
 sha256sum "$f" >> "$out/references_sha256.txt"
 minimap2 -x asm5 -c -N 200 -p 0.5 --secondary=yes -t 2 "$f" "$new_query" >> "$out/modern_to_legacy.paf"
done
sha256sum "$old_query" "$new_query" "$out/"*.paf >> "$out/references_sha256.txt"
node validation/hand2_smith_paf_audit.mjs "$out/legacy_to_modern.paf" "$out/modern_to_legacy.paf" "$out/result.json"
echo "PARTIAL at best: explicit genome completeness and curator checks still required."
