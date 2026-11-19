#!/bin/sh
# Download the 320 CC0 sound files of wyzowl/sfx-kit (67 MB) outside the repo; prints the folder.
set -e
DIR=${SFX_KIT_HOME:-$HOME/sfx-kit}
[ -d "$DIR/sounds" ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/wyzowl/sfx-kit "$DIR"
echo "SFX_KIT=$DIR"
