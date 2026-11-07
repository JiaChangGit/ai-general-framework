#!/bin/sh
set -eu
agf_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$agf_dir/agf.py" "$@"
