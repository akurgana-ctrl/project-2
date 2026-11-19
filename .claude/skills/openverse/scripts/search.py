"""Search Openverse (WordPress/openverse, api.openverse.org) for openly licensed audio or images.
usage: python3 -I search.py "tense documentary" [--type audio|images] [--license cc0,by] [--n 10] [--category music|sound_effect] [--min-dur 30]
Prints one JSON line per result: title, creator, license, url (the file), landing page, duration. No key needed (rate-limited)."""
import argparse, json, sys, urllib.parse, urllib.request
ap = argparse.ArgumentParser()
ap.add_argument('q'); ap.add_argument('--type', default='audio'); ap.add_argument('--license', default='cc0,by')
ap.add_argument('--n', type=int, default=10); ap.add_argument('--category'); ap.add_argument('--min-dur', type=float, default=0)
a = ap.parse_args()
p = {'q': a.q, 'license': a.license, 'page_size': min(a.n * 2, 50)}
if a.category: p['category'] = a.category
url = f'https://api.openverse.org/v1/{a.type}/?' + urllib.parse.urlencode(p)
req = urllib.request.Request(url, headers={'User-Agent': 'openverse-skill/1.0'})
data = json.load(urllib.request.urlopen(req, timeout=30))
k = 0
for r in data.get('results', []):
    dur = (r.get('duration') or 0) / 1000
    if a.type == 'audio' and dur and dur < a.min_dur: continue
    print(json.dumps({'title': r.get('title'), 'creator': r.get('creator'), 'license': f"{r.get('license')} {r.get('license_version') or ''}".strip(),
                      'url': r.get('url'), 'landing': r.get('foreign_landing_url'), 'source': r.get('source'), 'duration_s': round(dur, 1),
                      'attribution': r.get('attribution')}, ensure_ascii=False))
    k += 1
    if k >= a.n: break
if not k: print('no results', file=sys.stderr)
