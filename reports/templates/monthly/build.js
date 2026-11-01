// Monthly one-pager: node reports/templates/monthly/build.js <data.json> <out.pdf>
// data.json: { month, source, kpis: [{value, label}], categories: [{title, items: [{t, d?, pill?}]}] }
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const [dataPath, outPath] = process.argv.slice(2);
if (!dataPath || !outPath) { console.error('usage: build.js <data.json> <out.pdf>'); process.exit(1); }
const esc = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
const kpis = data.kpis.map((k) => `    <div class="kpi"><p class="v">${esc(k.value)}</p><p class="l">${esc(k.label)}</p></div>`).join('\n');
const cats = data.categories.map((c, i) => {
  const items = c.items.map((it) => {
    const pill = it.pill ? ` <span class="pill">${esc(it.pill)}</span>` : '';
    const d = it.d ? `<p class="d">${esc(it.d)}</p>` : '';
    return `        <div class="it"><span class="dot"></span><div class="tx"><p class="t">${esc(it.t)}${pill}</p>${d}</div></div>`;
  }).join('\n');
  const n = String(i + 1).padStart(2, '0');
  return `    <div class="cat">\n      <div class="hd"><span class="n">${n}</span><h3>${esc(c.title)}</h3></div>\n      <div class="items">\n${items}\n      </div>\n    </div>`;
}).join('\n\n');
const html = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8')
  .replaceAll('{{MONTH}}', esc(data.month)).replace('{{SOURCE}}', esc(data.source || ''))
  .replace('{{KPIS}}', kpis).replace('{{CATEGORIES}}', cats);
(async () => {
  const tmp = path.join(path.dirname(path.resolve(outPath)), '.monthly-onepager.html');
  fs.writeFileSync(tmp, html);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + tmp, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const over = await p.evaluate(() => [...document.querySelectorAll('.cat, .side')].some((e) => e.getBoundingClientRect().bottom > 1081));
  await p.pdf({ path: outPath, width: '1920px', height: '1080px', printBackground: true, preferCSSPageSize: true });
  await b.close();
  fs.unlinkSync(tmp);
  console.log(over ? 'WARNING: content runs past the page' : 'ok', outPath);
})();
