#!/usr/bin/env bash
# agent-crew setup (macOS/Linux) - builds a Python venv and installs the labs.
# crewai does NOT install on Python 3.14 (no tiktoken/regex wheels yet), so we
# find a 3.10-3.13 interpreter and use THAT for the venv.
set -e
cd "$(dirname "$0")"

PY=""
for v in python3.13 python3.12 python3.11 python3.10; do
    if command -v "$v" >/dev/null 2>&1; then PY="$v"; break; fi
done
if [ -z "$PY" ] && command -v python3 >/dev/null 2>&1; then
    ver="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
    case "$ver" in 3.10|3.11|3.12|3.13) PY=python3;; esac
fi
if [ -z "$PY" ]; then
    echo "ERROR: no compatible Python found (need 3.10-3.13)."
    echo "crewai does NOT build on Python 3.14. Install 3.12 or 3.13 and re-run."
    exit 1
fi

echo "Using $PY to build the venv..."
"$PY" -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

echo
echo "Setup complete. Next:"
echo "    source .venv/bin/activate"
echo "    python m8_0_verify.py        # all 4 gates should PASS (connect WireGuard first)"
echo "    python m8_1_bankbot.py"
