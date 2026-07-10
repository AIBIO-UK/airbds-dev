#!/usr/bin/env bash
#
# Render every D2 diagram source (*.d2) to an SVG beside it.
#
# Run this locally to preview your changes, or let CI do it
# (.github/workflows/render-diagrams.yml runs this exact script and commits the
# result back). Mermaid *.mmd diagrams render natively on GitHub and are not
# handled here.
#
# Needs the d2 CLI — pin v0.7.1 to match CI:
#   go install oss.terrastruct.com/d2@v0.7.1     (https://d2lang.com)
set -euo pipefail
cd "$(dirname "$0")/.."

shopt -s globstar nullglob
found=0
for src in **/*.d2; do
  case "$src" in */node_modules/*) continue ;; esac
  found=1
  out="${src%.d2}.svg"
  echo "d2: $src -> $out"
  d2 "$src" "$out"
done
[ "$found" = 1 ] || echo "No .d2 sources found."
