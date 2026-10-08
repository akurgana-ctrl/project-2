#!/usr/bin/env bash
# Usage: ./build.sh <frames_dir> [voice.wav|mp3]
# Encodes frames + sound design. With a voice file, mixes it in at 1.70s.
set -euo pipefail
cd "$(dirname "$0")"
FRAMES=$1; VO=${2:-}
python3 audio.py sfx.wav
if [ -n "$VO" ]; then
  ffmpeg -y -hide_banner -loglevel error -i sfx.wav -i "$VO" -filter_complex \
   "[1:a]aresample=48000,aformat=channel_layouts=stereo,silenceremove=start_periods=1:start_threshold=-45dB,\
highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,loudnorm=I=-14:TP=-1.5,\
aecho=0.8:0.5:60|110:0.18|0.10,adelay=1700|1700[v];\
[0:a][v]amix=inputs=2:normalize=0,alimiter=limit=0.89,atrim=0:4[a]" \
   -map "[a]" mix.wav
  AUDIO=mix.wav; OUT=outro_with_voice.mp4
else
  AUDIO=sfx.wav; OUT=outro_sfx.mp4
fi
ffmpeg -y -hide_banner -loglevel error -framerate 30 -i "$FRAMES/f%04d.png" -i "$AUDIO" \
  -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 320k -shortest "$OUT"
echo "wrote $OUT"
