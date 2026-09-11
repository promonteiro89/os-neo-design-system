#!/usr/bin/env bash
# Download the ODC portal stylesheets listed in tools/stylesheets.txt into
# reference/raw/. All are public — no authentication needed.
#
# The URLs carry content hashes and change on every ODC release; see the header
# of tools/stylesheets.txt for how to recapture them.
#
# Usage:  ./tools/fetch.sh            fetch everything
#         ./tools/fetch.sh neo        fetch only entries matching "neo"
#
# Then:   python3 tools/build.py && python3 tools/verify.py

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/reference/raw"
LIST="$ROOT/tools/stylesheets.txt"
FILTER="${1:-}"

# The tenant host is configuration, never hardcoded: $ODC_TENANT wins, else the
# gitignored ./odc-tenant file (copy odc-tenant.example to create it).
TENANT="${ODC_TENANT:-$( [ -f "$ROOT/odc-tenant" ] && head -1 "$ROOT/odc-tenant" || true )}"
if [ -z "$TENANT" ]; then
  echo "No tenant configured: set ODC_TENANT or copy odc-tenant.example to odc-tenant" >&2
  exit 1
fi

mkdir -p "$DEST"
changed=0

while IFS='|' read -r name url; do
  case "$name" in ''|\#*) continue ;; esac
  case "$url" in /*) url="https://$TENANT$url" ;; esac  # entries are host-relative
  [ -n "$FILTER" ] && case "$name" in *"$FILTER"*) ;; *) continue ;; esac

  out="$DEST/$name.css"
  [ -f "$out" ] && cp "$out" "$out.prev"

  if ! code=$(curl -fsS -o "$out.tmp" -w '%{http_code}' "$url" 2>/dev/null); then
    printf '%-28s FAILED (url expired? recapture it)\n' "$name"
    rm -f "$out.tmp" "$out.prev"
    continue
  fi
  mv "$out.tmp" "$out"

  size=$(wc -c <"$out" | tr -d ' ')
  if [ -f "$out.prev" ]; then
    if cmp -s "$out" "$out.prev"; then
      printf '%-28s %s  %8s bytes  unchanged\n' "$name" "$code" "$size"
      rm -f "$out.prev"
    else
      printf '%-28s %s  %8s bytes  CHANGED (previous kept as .prev)\n' "$name" "$code" "$size"
      changed=$((changed + 1))
    fi
  else
    printf '%-28s %s  %8s bytes  new\n' "$name" "$code" "$size"
    changed=$((changed + 1))
  fi
done <"$LIST"

# The shell CSS references two logo SVGs relative to its own URL.
if [ -z "$FILTER" ] || case "shell" in *"$FILTER"*) true ;; *) false ;; esac; then
  ASSETS="https://$TENANT/UnifiedExperienceMenuServices/resources/0.1.122/assets"
  mkdir -p "$DEST/assets"
  for a in outsystems-logo--light.svg outsystems-logo--dark.svg; do
    if curl -fsS -o "$DEST/assets/$a" "$ASSETS/$a" 2>/dev/null; then
      printf '%-28s 200  %8s bytes  asset\n' "$a" "$(wc -c <"$DEST/assets/$a" | tr -d ' ')"
    else
      printf '%-28s FAILED (asset)\n' "$a"
    fi
  done
fi

echo
if [ "$changed" -gt 0 ]; then
  echo "$changed file(s) new or changed — run: python3 tools/build.py && python3 tools/verify.py"
else
  echo "nothing changed"
fi
