#!/bin/sh
# Install earshot (Leonxlnx/earshot) once per session: clone outside the repo, CPU torch, editable install.
# Prints the Python to use (the {{PY}} of the real-sound skill).
set -e
DIR=${EARSHOT_HOME:-$HOME/earshot}
[ -d "$DIR/.git" ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/Leonxlnx/earshot "$DIR"
cd "$DIR"
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/python -c "import earshot" 2>/dev/null || {
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q torch --index-url https://download.pytorch.org/whl/cpu
  .venv/bin/pip install -q -e ".[mcp]"
}
echo "PY=$DIR/.venv/bin/python"
