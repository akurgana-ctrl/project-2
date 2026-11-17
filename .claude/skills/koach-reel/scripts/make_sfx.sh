#!/usr/bin/env bash
# Builds the standard sound kit for a Koach Hitarvut reel into <project>/assets/.
# Synthesized sounds need nothing; the rest are resolved through media-use
# (bundled or CC0 from Openverse - check .media/manifest.jsonl for the license).
# Usage: bash make_sfx.sh <hyperframes-project-dir>
set -euo pipefail
P="${1:?project dir}"
A="$P/assets"; mkdir -p "$A"
cd "$P"

q() { ffmpeg -y -loglevel error "$@"; }

# --- synthesized (no license needed) ---
# pop: pitch drop 1200->320 Hz, 0.2 s
q -f lavfi -i "aevalsrc='0.9*sin(2*PI*(320*t+900*0.02*(1-exp(-t/0.02))))*exp(-t/0.04)':s=48000:d=0.2" \
  -af "afade=t=in:d=0.002,afade=t=out:st=0.14:d=0.06" "$A/pop.mp3"
# like: two rising high notes E6 -> A6
q -f lavfi -i "aevalsrc='(0.6*sin(2*PI*1319*t)+0.25*sin(2*PI*2638*t))*exp(-t/0.06)*lt(t,0.09) + (0.6*sin(2*PI*1760*(t-0.09))+0.25*sin(2*PI*3520*(t-0.09)))*exp(-(t-0.09)/0.12)*gte(t,0.09)':s=48000:d=0.5" \
  -af "afade=t=out:st=0.38:d=0.12,volume=0.9" "$A/like.mp3"
# send tone (mixed with a swipe below to make "share")
q -f lavfi -i "aevalsrc='0.5*sin(2*PI*(400*t+1800*t*t))*exp(-pow((t-0.12)/0.08,2)) + 0.25*sin(2*PI*1200*t)*exp(-(t-0.2)/0.05)*gte(t,0.2)':s=48000:d=0.45" \
  -af "afade=t=out:st=0.33:d=0.12" "$A/sendtone.mp3"
# alarm: alternating 988/740 Hz beeps
q -f lavfi -i "aevalsrc='0.45*(sin(2*PI*if(lt(mod(t,0.3),0.15),988,740)*t)+0.3*sin(2*PI*3*if(lt(mod(t,0.3),0.15),988,740)*t))*lt(mod(t,0.15),0.12)':s=48000:d=0.9" \
  -af "afade=t=out:st=0.75:d=0.15" "$A/alarm.mp3"

# --- resolved (bundled / CC0) ---
res() { npx hyperframes media-use resolve --type sfx --intent "$1" --project . 2>&1 | tail -1 | sed -E 's/.*→ ([^ ]+) .*/\1/'; }
cp "$(res 'whoosh')" "$A/whoosh.mp3"                               # bundled cinematic whoosh
cp "$(res 'heavy cinematic impact hit boom')" "$A/impact.mp3"     # bundled bass impact
cp "$(res 'glitch transition')" "$A/glitch.mp3"                   # CC0 "Digital Glitch_v1"
cp "$(res 'swipe transition swoosh short')" "$A/swipe.mp3"         # bundled short whoosh
cp "$(res 'marker highlight swipe')" "$A/sparkle.mp3"             # bundled sparkle
ding_src="$(res 'notification ding bell')"; q -i "$ding_src" -t 1.2 -af "afade=t=out:st=0.7:d=0.5" "$A/ding.mp3"
shut_src="$(res 'camera shutter click')";  q -ss 0.65 -t 0.65 -i "$shut_src" -af "afade=t=out:st=0.5:d=0.15" "$A/shutter.mp3"
riser_src="$(res 'riser sweep')";          q -ss 2.0 -t 1.9 -i "$riser_src" -af "afade=t=in:d=0.5,afade=t=out:st=1.75:d=0.15" "$A/riser.mp3"
app_src="$(res 'audience applause short')"; q -ss 0.5 -t 3.0 -i "$app_src" -af "afade=t=in:d=0.25,afade=t=out:st=2.0:d=1.0" "$A/applause.mp3"
q -i "$A/swipe.mp3" -i "$A/sendtone.mp3" -filter_complex "[0][1]amix=inputs=2:normalize=0,volume=0.9" "$A/share.mp3"

# The cut points above (shutter 0.65 s, riser 2.0 s) fit the files media-use returned in Nov 2026.
# If a different file comes back, find its loud part first:
#   ffmpeg -i f.mp3 -af "asetnsamples=n=4410,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.Peak_level" -f null - 2>&1 | grep Peak_level
echo "--- licenses (must be cc0 or bundled) ---"
python3 -I -c "
import json
for l in open('.media/manifest.jsonl'):
    d = json.loads(l)
    if d.get('type') == 'sfx':
        print(d['id'], d.get('source'), (d.get('provenance') or {}).get('license'), '|', d.get('description', '')[:50])
"
for f in "$A"/*.mp3; do printf '%-14s %s\n' "$(basename "$f")" "$(ffmpeg -i "$f" -af volumedetect -f null - 2>&1 | grep -o 'max_volume: .*')"; done
