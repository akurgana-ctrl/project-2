#!/usr/bin/env node
// Postiz publisher for "multi-post" – one job file -> every network.
// No dependencies (Node 20+). Never put keys in files: the repo is public.
//
//   POSTIZ_URL      e.g. https://social.example.org/api   (self-hosted backend, WITH /api)
//   POSTIZ_API_KEY  Postiz -> Settings -> Public API
//
// Commands:
//   node postiz.mjs check                 is the key valid + which org
//   node postiz.mjs channels              list connected channels (id, network, name)
//   node postiz.mjs upload <file|url>     upload one media file, prints {id,path}
//   node postiz.mjs post <job.json>       DRY RUN: prints exactly what would be sent
//   node postiz.mjs post <job.json> --yes really publishes / schedules
//   node postiz.mjs status [days]         posts of the last N days (default 2) with state + link

import { readFile, stat } from 'node:fs/promises';
import { basename, extname, resolve, dirname } from 'node:path';

const BASE = (process.env.POSTIZ_URL || '').replace(/\/+$/, '');
const KEY = process.env.POSTIZ_API_KEY || '';
const API = BASE ? `${BASE}/public/v1` : '';

function die(msg) { console.error(`✖ ${msg}`); process.exit(1); }
function need() {
  if (!BASE) die('POSTIZ_URL is not set (example: https://social.example.org/api)');
  if (!KEY) die('POSTIZ_API_KEY is not set (Postiz → Settings → Public API)');
}

async function api(path, { method = 'GET', json, form } = {}) {
  need();
  const headers = { Authorization: KEY };
  let body;
  if (json) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(json); }
  if (form) body = form;
  const res = await fetch(`${API}${path}`, { method, headers, body });
  const text = await res.text();
  let data; try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) die(`${method} ${path} → HTTP ${res.status}: ${typeof data === 'string' ? data.slice(0, 500) : JSON.stringify(data).slice(0, 500)}`);
  return data;
}

// ---------- network rules ----------
// key in job.posts  ->  Postiz identifiers it may map to, and default settings.
const NETWORKS = {
  instagram: { ids: ['instagram', 'instagram-standalone'], limit: 2200 },
  facebook:  { ids: ['facebook'], limit: 63206 },
  tiktok:    { ids: ['tiktok'], limit: 2200, needsVideo: true },
  x:         { ids: ['x'], limit: 280 },
  youtube:   { ids: ['youtube'], limit: 5000, needsVideo: true },
  linkedin:  { ids: ['linkedin-page', 'linkedin'], limit: 3000 },
  telegram:  { ids: ['telegram'], limit: 4096 },
};

function settingsFor(net, identifier, p, job) {
  const ai = !!job.made_with_ai;
  switch (net) {
    case 'instagram': return { __type: identifier, post_type: p.post_type || 'post', is_trial_reel: false, collaborators: p.collaborators || [], made_with_ai: ai };
    case 'facebook': {
      const s = { __type: 'facebook', post_type: p.post_type || 'post' };
      if (p.url) s.url = p.url;
      if (p.title) s.title = p.title;
      return s;
    }
    case 'tiktok': return {
      __type: 'tiktok', title: (p.title || '').slice(0, 90),
      privacy_level: p.privacy_level || 'PUBLIC_TO_EVERYONE',
      duet: false, stitch: false, comment: true, autoAddMusic: 'no',
      brand_content_toggle: false, brand_organic_toggle: false,
      video_made_with_ai: ai, content_posting_method: p.content_posting_method || 'DIRECT_POST',
    };
    case 'x': return { __type: 'x', who_can_reply_post: p.who_can_reply_post || 'everyone', community: '', made_with_ai: ai, paid_partnership: false };
    case 'youtube': {
      const title = (p.title || '').trim();
      if (title.length < 2 || title.length > 100) die('youtube.title must be 2–100 characters');
      return { __type: 'youtube', title, type: p.visibility || 'public', selfDeclaredMadeForKids: 'no', tags: (p.tags || []).map(t => ({ value: t, label: t })), made_with_ai: ai };
    }
    case 'linkedin': return { __type: identifier, post_as_images_carousel: false };
    case 'telegram': return { __type: 'telegram' };
  }
}

const isVideo = (p) => /\.(mp4|mov|m4v|webm)$/i.test(p);
const MIME = { '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.m4v': 'video/mp4', '.webm': 'video/webm', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp' };

async function upload(src) {
  if (/^https:\/\//.test(src)) return api('/upload-from-url', { method: 'POST', json: { url: src } });
  const buf = await readFile(src);
  const form = new FormData();
  form.append('file', new Blob([buf], { type: MIME[extname(src).toLowerCase()] || 'application/octet-stream' }), basename(src));
  return api('/upload', { method: 'POST', form });
}

async function channels() {
  const list = await api('/integrations');
  return (Array.isArray(list) ? list : []).filter(c => !c.disabled);
}

async function buildPayload(jobPath, { dry }) {
  const job = JSON.parse(await readFile(jobPath, 'utf8'));
  const dir = dirname(resolve(jobPath));
  const media = (job.media || []).map(m => (/^https:\/\//.test(m) ? m : resolve(dir, m)));
  for (const m of media) if (!/^https:\/\//.test(m)) await stat(m).catch(() => die(`media not found: ${m}`));
  const hasVideo = media.some(isVideo);

  const when = job.when && job.when !== 'now' ? new Date(job.when) : new Date();
  if (isNaN(when)) die(`bad "when": ${job.when}`);

  const chans = await channels();
  const problems = [];
  const plan = [];
  for (const [net, p] of Object.entries(job.posts || {})) {
    const rule = NETWORKS[net];
    if (!rule) { problems.push(`unknown network "${net}" (allowed: ${Object.keys(NETWORKS).join(', ')})`); continue; }
    if (p.skip) continue;
    const text = (p.text || '').trim();
    if (!text && net !== 'tiktok' && net !== 'youtube') problems.push(`${net}: empty text`);
    if ([...text].length > rule.limit) problems.push(`${net}: ${[...text].length} chars, limit ${rule.limit}`);
    if (rule.needsVideo && !hasVideo) problems.push(`${net}: needs a video file`);
    const targets = p.channel_ids?.length
      ? chans.filter(c => p.channel_ids.includes(c.id))
      : chans.filter(c => rule.ids.includes(c.identifier));
    if (!targets.length) { problems.push(`${net}: no connected channel in Postiz`); continue; }
    for (const c of targets) plan.push({ net, c, text, p });
  }
  if (problems.length) { console.error('Problems:\n - ' + problems.join('\n - ')); if (!dry) process.exit(1); }

  let uploaded = media.map(m => ({ id: '(upload on --yes)', path: m }));
  if (!dry) uploaded = [];
  if (!dry) for (const m of media) { const u = await upload(m); uploaded.push({ id: u.id, path: u.path }); }

  const group = `mp-${Date.now().toString(36)}`;
  const payload = {
    type: job.when && job.when !== 'now' ? 'schedule' : 'now',
    date: when.toISOString(), shortLink: false, tags: [],
    posts: plan.map(({ net, c, text, p }) => ({
      integration: { id: c.id }, group,
      value: [{ content: text, image: uploaded }],
      settings: settingsFor(net, c.identifier, p, job),
    })),
  };
  return { payload, plan, job };
}

const [cmd, arg, flag] = process.argv.slice(2);
try {
  if (cmd === 'check') {
    console.log(JSON.stringify(await api('/me'), null, 2));
  } else if (cmd === 'channels') {
    const list = await channels();
    if (!list.length) console.log('No channels connected yet. Connect them in the Postiz web UI.');
    for (const c of list) console.log(`${c.identifier.padEnd(22)} ${c.id}  ${c.name}${c.profile ? ' (@' + c.profile + ')' : ''}`);
  } else if (cmd === 'upload') {
    if (!arg) die('usage: upload <file|https-url>');
    console.log(JSON.stringify(await upload(arg), null, 2));
  } else if (cmd === 'post') {
    if (!arg) die('usage: post <job.json> [--yes]');
    const dry = flag !== '--yes';
    const { payload, plan } = await buildPayload(arg, { dry });
    console.log(`${dry ? 'DRY RUN – nothing sent.' : 'Sending…'} ${payload.type} at ${payload.date}`);
    for (const { net, c, text } of plan) console.log(` • ${net.padEnd(9)} → ${c.name} [${c.identifier}]  ${[...text].length} chars`);
    if (dry) { console.log(JSON.stringify(payload, null, 2)); console.log('\nRun again with --yes to publish.'); }
    else console.log(JSON.stringify(await api('/posts', { method: 'POST', json: payload }), null, 2));
  } else if (cmd === 'status') {
    const days = Number(arg || 2);
    const end = new Date(Date.now() + 864e5 * 7), start = new Date(Date.now() - 864e5 * days);
    const q = new URLSearchParams({ startDate: start.toISOString(), endDate: end.toISOString() });
    const res = await api(`/posts?${q}`);
    for (const p of res.posts || res || []) console.log(`${(p.state || '').padEnd(9)} ${p.integration?.providerIdentifier || ''} ${p.publishDate || ''} ${p.releaseURL || ''} ${p.error ? '⚠ ' + p.error : ''}`);
  } else {
    console.log('commands: check | channels | upload <file> | post <job.json> [--yes] | status [days]');
  }
} catch (e) { die(e.message); }
