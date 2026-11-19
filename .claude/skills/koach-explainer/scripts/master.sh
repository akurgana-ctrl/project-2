#!/bin/sh
# Mux the rendered picture with the mix, two-pass loudnorm to -14 LUFS / -1.5 dBTP (works with ffmpeg 6.1).
# usage: sh master.sh <project dir> <out name>.mp4
set -e
cd "$1"; OUT=${2:-film.mp4}
J=$(ffmpeg -hide_banner -i out/mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
g() { echo "$J" | sed -n "s/.*\"$1\" : \"\(.*\)\".*/\1/p"; }
ffmpeg -y -v error -i out/video.mp4 -i out/mix.wav -map 0:v -map 1:a -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):linear=true,aresample=48000" \
  -c:a aac -b:a 192k -movflags +faststart -shortest "$OUT"
ffmpeg -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tail -2
