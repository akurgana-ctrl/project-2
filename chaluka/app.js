/*
 * Task allocation board. Assignments live in memory (plus a per-browser draft)
 * and are committed to the repo as chaluka/assignments.json when "Save" is pressed.
 * Saving uses the same GitHub token and settings as the main site's editor.
 */
(function () {
  "use strict";

  const DOMAINS = [
    { k: "M", name: "ניהול", tasks: ["בניית פורמט משימה", "סנכרון שבועי", "תוכנית עבודה ויעדים", "אישור תוכניות עבודה", "אישור תקציב", "אישור עמדות מדיניות", "רתימת אנשים ושותפים"] },
    { k: "A", name: "מדיניות וכנסת", tasks: ["לו״ז כנסת שבועי", "שיבוץ לדיונים", "הופעה בדיונים", "ניירות עמדה והכנה לדיונים", "מכתבים לכנסת", "קשר עם חברי כנסת", "קשר עם ועדות הכנסת", "קשר עם משרדי ממשלה", "קשר עם ארגונים ושותפים לדרך"] },
    { k: "B", name: "דירקטוריון", tasks: ["קביעת פרקים בהשתתפותם", "רתימה לעניין", "קביעת מפגשים", "תוכניות עבודה בכנסת", "קבלת חומרים: הרצאות, פוסטים, סרטונים"] },
    { k: "C", name: "מתנדבים וצוותים", tasks: ["גיוס מתנדבים למשימה מתוך הצוות", "הורדת משימות, מעקב ופידבקים", "הכשרה וקליטה של מתנדבים חדשים", "הורדת משימות לראשי צוותים, מעקב ופידבקים", "פגישות ושיחות קבועות עם ראשי צוותים"] },
    { k: "D", name: "גיוס משאבים", tasks: ["גיוס תורמים: קרנות ופילנתרופיה", "גיוס שותפים אסטרטגיים", "תקשורת אישית עם תורמים", "הזמנת תורמים לאירועים", "טלפנות", "קמפיין"] },
    { k: "E", name: "תוכן, דיגיטל ושיווק", tasks: ["סושיאל של על המשמעות", "סושיאל של כח התערבות", "עריכת סרטונים", "גרפיקה לאירועים ועוד", "עריכת האתר", "עריכה ועיצוב דפי נחיתה", "ניוזלטר", "טורי דעה", "סרטונים מהוועדות ומההופעות בכנסת", "פרסומות בתוך פרקי על המשמעות", "שיווק הרצאות של חברי דירקטוריון (לא גפן)", "לידים של Peach"] },
    { k: "F", name: "כספים ובקרה", tasks: ["מעקב אחרי תרומות בכל שלב", "ניהול דו״ח הכנסות מתרומות"] },
    { k: "G", name: "כנסים ואירועים", tasks: ["אירועי מתנדבים", "אירועי דירקטוריון", "כנסים"] },
    { k: "H", name: "יוזמות", tasks: ["פעילות שטח", "פעילות ביום הבחירות", "יוזמות נוספות"] }
  ];
  const PEOPLE = [
    { id: "adam", name: "אדם" }, { id: "matan", name: "מתן" }, { id: "ran", name: "רן" },
    { id: "tamir", name: "תמיר" }, { id: "extra", name: "איש צוות נוסף" }
  ];
  const DATA_PATH = "chaluka/assignments.json";
  const DRAFT_KEY = "kh-chaluka-draft";
  const CFG_KEY = "kh-editor"; // shared with the main site's editor

  const TASKS = [];
  DOMAINS.forEach((d) => d.tasks.forEach((text, i) => TASKS.push({ id: d.k + (i + 1), d: d.k, text })));
  const byId = Object.fromEntries(TASKS.map((t) => [t.id, t]));
  const domainOf = Object.fromEntries(DOMAINS.map((d) => [d.k, d]));
  const isPerson = (p) => PEOPLE.some((x) => x.id === p);
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  /* ---------------- Config + GitHub ---------------- */
  function defaults() {
    const m = location.hostname.match(/^([^.]+)\.github\.io$/i);
    const seg = location.pathname.split("/").filter(Boolean)[0];
    return { owner: m ? m[1] : "akurgana-ctrl", repo: m && seg && !seg.includes(".") ? seg : "project-2", branch: "gh-pages", token: "" };
  }
  function loadCfg() { try { return Object.assign(defaults(), JSON.parse(localStorage.getItem(CFG_KEY) || "{}")); } catch { return defaults(); } }
  function saveCfg(c) { try { localStorage.setItem(CFG_KEY, JSON.stringify(c)); } catch { /* private mode */ } }
  let cfg = loadCfg();

  const b64encode = (str) => {
    const bytes = new TextEncoder().encode(str);
    let bin = "";
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(bin);
  };
  const b64decode = (b64) => new TextDecoder().decode(Uint8Array.from(atob(b64.replace(/\s/g, "")), (c) => c.charCodeAt(0)));

  async function gh(path, opts = {}) {
    const res = await fetch(`https://api.github.com/repos/${cfg.owner}/${cfg.repo}/contents/${path}`, {
      ...opts,
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${cfg.token}`,
        "X-GitHub-Api-Version": "2022-11-28",
        ...(opts.body ? { "Content-Type": "application/json" } : {})
      }
    });
    if (!res.ok) {
      const msg = {
        401: "המפתח (Token) לא תקין או שפג תוקפו.",
        403: "למפתח אין הרשאת כתיבה לריפו.",
        404: "הריפו, הענף או הקובץ לא נמצאו.",
        409: "מישהו אחר שמר בינתיים. רעננו את הדף ונסו שוב.",
        422: "GitHub דחה את השמירה. רעננו את הדף ונסו שוב."
      }[res.status] || `שגיאה מ-GitHub (${res.status}).`;
      const err = new Error(msg); err.status = res.status; throw err;
    }
    return res.json();
  }

  /* ---------------- State ---------------- */
  let saved = {};      // last saved allocation
  let assign = {};     // current allocation on screen
  let sha = null;      // sha of assignments.json we loaded
  let savedAt = "";
  let filter = "all";
  let busy = false;
  let resetArmed = false;
  let menuEl = null;
  let dragId = null;
  const root = $("#root");

  const owner = (id) => (isPerson(assign[id]) ? assign[id] : "");
  const cleanMap = (m) => Object.fromEntries(Object.entries(m).filter(([k, v]) => byId[k] && isPerson(v)));
  function isDirty() {
    const a = cleanMap(assign), b = cleanMap(saved);
    const ka = Object.keys(a), kb = Object.keys(b);
    return ka.length !== kb.length || ka.some((k) => a[k] !== b[k]);
  }
  function storeDraft() {
    try { isDirty() ? localStorage.setItem(DRAFT_KEY, JSON.stringify(cleanMap(assign))) : localStorage.removeItem(DRAFT_KEY); } catch { /* private mode */ }
  }

  let toastTimer;
  function toast(msg, isErr) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.toggle("err", !!isErr);
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), isErr ? 6000 : 3000);
  }

  /* ---------------- Board ---------------- */
  const cardHtml = (t) =>
    `<button class="card" draggable="true" data-id="${t.id}" aria-haspopup="menu"><span class="tag">${t.d}</span><span>${esc(t.text)}</span></button>`;

  function render() {
    const done = TASKS.filter((t) => owner(t.id)).length;
    const dirty = isDirty();
    let h = `<header><div><p class="eyebrow">כח התערבות · ישיבת צוות 18.10</p><h1>חלוקת משימות</h1></div>
      <div class="tools">
        <div class="progress"><span>${done} מתוך ${TASKS.length} חולקו</span><span class="bar"><i style="width:${(done / TASKS.length) * 100}%"></i></span></div>
        <button class="btn primary" id="save"${dirty && !busy ? "" : " disabled"}>${busy ? "שומר…" : "שמירת החלוקה"}</button>
        <button class="btn cta" id="makeReport">יצירת דו״ח חלוקת אחריות</button>
        <button class="btn warn" id="reset">${resetArmed ? "לחצו שוב לאיפוס" : "איפוס"}</button>
      </div></header>`;
    const st = dirty ? "יש שינויים שלא נשמרו. הם נשמרים בינתיים בדפדפן הזה." : savedAt ? `החלוקה נשמרה לאחרונה ב-${savedAt}` : "";
    h += `<p class="status${dirty ? " dirty" : ""}">${esc(st)}</p>`;
    h += `<div class="filters" role="group" aria-label="סינון לפי תחום"><button class="chip" data-f="all" aria-pressed="${filter === "all"}">כל התחומים</button>` +
      DOMAINS.map((d) => `<button class="chip" data-f="${d.k}" aria-pressed="${filter === d.k}">${d.k} · ${esc(d.name)}</button>`).join("") + `</div>`;

    h += `<div class="board">`;
    const open = TASKS.filter((t) => !owner(t.id));
    const pool = open.filter((t) => filter === "all" || t.d === filter);
    h += `<section class="col pool" data-drop=""><div class="col-head"><h2>לחלוקה</h2><span class="count">${open.length}</span></div>`;
    if (!pool.length) h += `<p class="empty">${filter === "all" ? "כל המשימות חולקו" : "אין משימות פתוחות בתחום הזה"}</p>`;
    DOMAINS.forEach((d) => {
      const ts = pool.filter((t) => t.d === d.k);
      if (!ts.length) return;
      h += `<div class="group"><span class="g"><span class="tag">${d.k}</span>${esc(d.name)}</span><button class="grp-btn" data-group="${d.k}">חלוקת כל התחום</button></div>` + ts.map(cardHtml).join("");
    });
    h += `</section>`;
    PEOPLE.forEach((p) => {
      const mine = TASKS.filter((t) => owner(t.id) === p.id);
      const shown = mine.filter((t) => filter === "all" || t.d === filter);
      h += `<section class="col" data-drop="${p.id}"><div class="col-head"><h2>${esc(p.name)}</h2><span class="count">${mine.length}</span></div>` +
        (shown.length ? shown.map(cardHtml).join("") : `<p class="empty">גררו לכאן משימות</p>`) + `</section>`;
    });
    h += `</div><p class="note">גוררים משימה לעמודה של אדם, או לוחצים עליה ובוחרים שם. ״חלוקת כל התחום״ מעבירה את כל המשימות הפתוחות בתחום לאדם אחד. בסוף לוחצים על ״שמירת החלוקה״ כדי שכולם יראו אותה.</p>`;
    root.innerHTML = h;
  }

  function move(ids, p) {
    ids.forEach((id) => { if (p) assign[id] = p; else delete assign[id]; });
    resetArmed = false;
    storeDraft();
    render();
  }

  function closeMenu() { if (menuEl) { menuEl.remove(); menuEl = null; } }
  function openMenu(anchor, ids, title, cur) {
    closeMenu();
    const m = document.createElement("div");
    m.className = "menu";
    m.setAttribute("role", "menu");
    m.innerHTML = `<p>${esc(title)}</p>` +
      PEOPLE.map((p) => `<button role="menuitem" data-to="${p.id}" aria-current="${cur === p.id}">${esc(p.name)}</button>`).join("") +
      (cur ? `<button role="menuitem" data-to="">החזרה לרשימת החלוקה</button>` : "");
    document.body.appendChild(m);
    menuEl = m;
    const r = anchor.getBoundingClientRect(), mw = m.offsetWidth, mh = m.offsetHeight;
    let top = r.bottom + 6;
    if (top + mh > innerHeight - 8) top = Math.max(8, r.top - mh - 6);
    m.style.left = Math.min(Math.max(8, r.right - mw), innerWidth - mw - 8) + "px";
    m.style.top = top + "px";
    m.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-to]");
      if (!b) return;
      closeMenu();
      move(ids, b.dataset.to);
    });
    const first = m.querySelector("button");
    if (first) first.focus();
  }

  root.addEventListener("click", (e) => {
    const card = e.target.closest(".card");
    if (card) { e.stopPropagation(); const id = card.dataset.id; openMenu(card, [id], byId[id].text, owner(id)); return; }
    const grp = e.target.closest(".grp-btn");
    if (grp) {
      e.stopPropagation();
      const k = grp.dataset.group;
      const ids = TASKS.filter((t) => t.d === k && !owner(t.id)).map((t) => t.id);
      openMenu(grp, ids, `כל המשימות הפתוחות ב${domainOf[k].name} (${ids.length})`, "");
      return;
    }
    const chip = e.target.closest(".chip");
    if (chip) { filter = chip.dataset.f; render(); return; }
    if (e.target.closest("#reset")) {
      if (!resetArmed) { resetArmed = true; render(); return; }
      assign = {}; resetArmed = false; storeDraft(); render(); return;
    }
    if (e.target.closest("#save")) { save(); return; }
    if (e.target.closest("#makeReport")) showReport();
  });
  document.addEventListener("click", (e) => { if (menuEl && !menuEl.contains(e.target)) closeMenu(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeMenu(); });
  addEventListener("scroll", closeMenu, { passive: true });

  root.addEventListener("dragstart", (e) => {
    const c = e.target.closest(".card");
    if (!c) return;
    dragId = c.dataset.id;
    c.classList.add("dragging");
    closeMenu();
    try { e.dataTransfer.setData("text/plain", dragId); e.dataTransfer.effectAllowed = "move"; } catch { /* old browsers */ }
  });
  root.addEventListener("dragend", () => {
    dragId = null;
    root.querySelectorAll(".dragging,.over").forEach((el) => el.classList.remove("dragging", "over"));
  });
  root.addEventListener("dragover", (e) => {
    const col = e.target.closest("[data-drop]");
    if (!col || !dragId) return;
    e.preventDefault();
    root.querySelectorAll(".over").forEach((el) => { if (el !== col) el.classList.remove("over"); });
    col.classList.add("over");
  });
  root.addEventListener("dragleave", (e) => {
    const col = e.target.closest("[data-drop]");
    if (col && !col.contains(e.relatedTarget)) col.classList.remove("over");
  });
  root.addEventListener("drop", (e) => {
    const col = e.target.closest("[data-drop]");
    if (!col || !dragId) return;
    e.preventDefault();
    const id = dragId;
    dragId = null;
    move([id], col.dataset.drop);
  });

  /* ---------------- Report ---------------- */
  function groupedList(ts) {
    return DOMAINS.map((d) => {
      const items = ts.filter((t) => t.d === d.k);
      return items.length ? `<h3>${d.k} · ${esc(d.name)}</h3><ul>${items.map((t) => `<li>${esc(t.text)}</li>`).join("")}</ul>` : "";
    }).join("");
  }
  function reportText() {
    const date = new Date().toLocaleDateString("he-IL");
    const lines = [`דו״ח חלוקת אחריות – כח התערבות (${date})`, ""];
    PEOPLE.concat([{ id: "", name: "ללא אחראי" }]).forEach((p) => {
      const ts = TASKS.filter((t) => owner(t.id) === p.id);
      if (!p.id && !ts.length) return;
      lines.push(`${p.name} (${ts.length})`);
      DOMAINS.forEach((d) => ts.filter((t) => t.d === d.k).forEach((t) => lines.push(`• ${t.text} [${d.name}]`)));
      if (!ts.length) lines.push("• אין משימות");
      lines.push("");
    });
    return lines.join("\n");
  }
  function showReport() {
    closeMenu();
    const date = new Date().toLocaleDateString("he-IL", { day: "numeric", month: "long", year: "numeric" });
    const open = TASKS.filter((t) => !owner(t.id));
    const rep = $("#report");
    rep.innerHTML = `<div class="report-tools">
        <button class="btn" id="backToBoard">חזרה ללוח</button>
        <button class="btn primary" id="printReport">הדפסה / שמירה כ-PDF</button>
        <button class="btn" id="copyReport">העתקת הדו״ח כטקסט</button>
      </div>
      <p class="eyebrow">כח התערבות</p>
      <h1 id="reportTitle">דו״ח חלוקת אחריות</h1>
      <p class="meta">הופק ב-${esc(date)}${isDirty() ? " · כולל שינויים שעוד לא נשמרו" : ""}</p>
      <div class="summary">${PEOPLE.map((p) => `<div><b>${TASKS.filter((t) => owner(t.id) === p.id).length}</b>${esc(p.name)}</div>`).join("")}
        <div><b>${open.length}</b>ללא אחראי</div></div>` +
      PEOPLE.map((p) => {
        const ts = TASKS.filter((t) => owner(t.id) === p.id);
        return `<section class="person"><h2>${esc(p.name)} <small>${ts.length} משימות</small></h2>${ts.length ? groupedList(ts) : `<p class="note">לא שויכו משימות</p>`}</section>`;
      }).join("") +
      (open.length ? `<section class="person open"><h2>ללא אחראי <small>${open.length} משימות</small></h2>${groupedList(open)}</section>` : "");
    rep.hidden = false;
    root.hidden = true;
    document.body.classList.add("show-report");
    scrollTo(0, 0);
    $("#backToBoard").addEventListener("click", hideReport);
    $("#printReport").addEventListener("click", () => print());
    $("#copyReport").addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(reportText()); toast("הדו״ח הועתק"); }
      catch { toast("ההעתקה לא הצליחה. אפשר לסמן את הטקסט ולהעתיק ידנית.", true); }
    });
  }
  function hideReport() {
    $("#report").hidden = true;
    root.hidden = false;
    document.body.classList.remove("show-report");
  }

  /* ---------------- Save ---------------- */
  function openSettings() {
    const dlg = $("#dlg");
    dlg.innerHTML = `<form method="dialog" id="cfgForm">
      <h2>מפתח שמירה</h2>
      <p class="note">השמירה נעשית לריפו ב-GitHub, עם אותו מפתח של עורך האתר הראשי. צריך להזין אותו פעם אחת בכל מחשב או טלפון, והוא נשמר רק בדפדפן הזה.</p>
      <ol>
        <li><a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">יוצרים Fine-grained token חדש ב-GitHub</a></li>
        <li>Repository access: <b>Only select repositories</b>, ובוחרים את <b>${esc(cfg.repo)}</b></li>
        <li>Permissions, Repository permissions: <b>Contents: Read and write</b></li>
        <li>Generate token, מעתיקים ומדביקים כאן</li>
      </ol>
      <label for="tokenInput">מפתח גישה (Token)</label>
      <input id="tokenInput" type="password" dir="ltr" placeholder="github_pat_…" required value="${esc(cfg.token)}">
      <div class="dlg-actions">
        <button class="btn primary" value="ok">שמירה ושמירת החלוקה</button>
        <button class="btn" value="cancel" formnovalidate>ביטול</button>
      </div></form>`;
    dlg.showModal();
    dlg.addEventListener("close", function onClose() {
      dlg.removeEventListener("close", onClose);
      if (dlg.returnValue !== "ok") return;
      cfg.token = $("#tokenInput").value.trim();
      saveCfg(cfg);
      if (cfg.token) save();
    });
  }

  async function save() {
    if (busy || !isDirty()) return;
    if (!cfg.token) { openSettings(); return; }
    busy = true; render();
    try {
      try { sha = (await gh(`${DATA_PATH}?ref=${encodeURIComponent(cfg.branch)}`)).sha; }
      catch (err) { if (err.status !== 404) throw err; sha = null; }
      const now = new Date();
      const body = { assign: cleanMap(assign), savedAt: now.toISOString() };
      const res = await gh(DATA_PATH, {
        method: "PUT",
        body: JSON.stringify({ message: "עדכון חלוקת משימות", content: b64encode(JSON.stringify(body, null, 2) + "\n"), branch: cfg.branch, ...(sha ? { sha } : {}) })
      });
      sha = res.content && res.content.sha;
      saved = cleanMap(assign);
      savedAt = now.toLocaleString("he-IL", { dateStyle: "short", timeStyle: "short" });
      storeDraft();
      toast("נשמר. כל מי שפותח את האתר יראה את החלוקה תוך כדקה.");
    } catch (err) {
      toast(err.message, true);
      if (err.status === 401 || err.status === 403) openSettings();
    } finally {
      busy = false; render();
    }
  }

  /* ---------------- Presentation ---------------- */
  // The task list as it was originally written, before regrouping into domains.
  const RAW = [
    ["ניהול", ["בניית פורמט משימה", "סנכרון שבועי", "תוכנית עבודה ויעדים", "אישור תוכניות עבודה", "אישור תקציב", "אישור עמדות מדיניות", "רתימת אנשים ושותפים"]],
    ["תקשורת מול חברי דירקטוריון", ["קביעת פרקים בהשתתפותם", "רתימה לעניין", "קביעת מפגשים", "תוכניות עבודה בכנסת", "קבלת חומרים: הרצאות, פוסטים, סרטונים ושיתוף ברשתות"]],
    ["מתנדבים", ["גיוס מתנדבים למשימה מתוך הצוות", "הורדת משימות, מעקב ופידבקים", "הכשרה וקליטה של מתנדבים חדשים", "הורדת משימות לראשי צוותים, מעקב ופידבקים", "פגישות ושיחות קבועות עם ראשי צוותים"]],
    ["כנסת", ["לו״ז כנסת שבועי", "שיבוץ לדיונים", "הופעה בדיונים", "ניירות עמדה והכנה לדיונים", "מכתבים לכנסת", "סרטונים מהוועדות ומההופעות בכנסת"]],
    ["קשרי חוץ", ["חברי כנסת", "ועדות הכנסת", "משרדי ממשלה", "ארגונים ושותפים אחרים לדרך"]],
    ["קשרי תורמים", ["תקשורת אישית", "הזמנה לאירועים"]],
    ["שיווק וכספים", ["מעקב אחרי תרומות בכל שלב", "ניהול דו״ח הכנסות מתרומות", "שיווק הרצאות של חברי דירקטוריון (לא גפן)", "גיוס שותפים אסטרטגיים", "גיוס תורמים: קרנות ופילנתרופיה", "טלפנות", "קמפיין", "ניוזלטר", "טורי דעה", "פרסומות בתוך פרקי על המשמעות", "לידים של Peach"]],
    ["דיגיטל", ["העלאת חומרים ברשתות של על המשמעות", "סושיאל של כח התערבות", "עריכת סרטונים", "גרפיקה לאירועים ועוד", "עריכת האתר", "עריכה ועיצוב דפי נחיתה"]],
    ["כנסים ואירועים", ["אירועי מתנדבים", "אירועי דירקטוריון", "כנסים"]],
    ["יוזמות", ["פעילות שטח", "פעילות ביום הבחירות", "יוזמות נוספות"]]
  ];
  $("#rawList").innerHTML = RAW.map(([name, items]) =>
    `<div class="rawgroup"><h3>${esc(name)}</h3><ul>${items.map((t) => `<li>${esc(t)}</li>`).join("")}</ul></div>`).join("");
  $("#mapTitle").textContent = `אותן ${TASKS.length} משימות, ב-${DOMAINS.length} תחומים`;
  $("#domainCards").innerHTML = DOMAINS.map((d) =>
    `<div class="dcard"><div class="dcard__top"><b>${d.k}</b><span>${d.tasks.length} משימות</span></div><h3>${esc(d.name)}</h3><p>${esc(d.tasks.slice(0, 5).join(", "))}${d.tasks.length > 5 ? "…" : ""}</p></div>`).join("");

  const slides = Array.from(document.querySelectorAll(".slide"));
  let current = 0;
  $("#dots").innerHTML = slides.map((s, i) => `<button class="dot" data-i="${i}" aria-label="${esc(s.dataset.title)}" title="${esc(s.dataset.title)}"></button>`).join("");
  function go(i, push = true) {
    current = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach((s, j) => s.classList.toggle("active", j === current));
    document.querySelectorAll(".dot").forEach((d, j) => d.setAttribute("aria-current", String(j === current)));
    $("#counter").textContent = `${current + 1} / ${slides.length} · ${slides[current].dataset.title}`;
    $("#prevSlide").disabled = current === 0;
    $("#nextSlide").disabled = current === slides.length - 1;
    closeMenu();
    scrollTo(0, 0);
    if (push) history.replaceState(null, "", `#${current + 1}`);
  }
  $("#prevSlide").addEventListener("click", () => go(current - 1));
  $("#nextSlide").addEventListener("click", () => go(current + 1));
  $("#dots").addEventListener("click", (e) => { const d = e.target.closest(".dot"); if (d) go(+d.dataset.i); });
  document.addEventListener("keydown", (e) => {
    if (menuEl || $("#dlg").open || !$("#report").hidden || /INPUT|TEXTAREA/.test(document.activeElement.tagName)) return;
    // Right-to-left: the left arrow moves forward.
    if (e.key === "ArrowLeft" || e.key === "PageDown") { e.preventDefault(); go(current + 1); }
    else if (e.key === "ArrowRight" || e.key === "PageUp") { e.preventDefault(); go(current - 1); }
  });
  let touchX = null;
  document.addEventListener("touchstart", (e) => { touchX = slides[current].classList.contains("slide--board") ? null : e.touches[0].clientX; }, { passive: true });
  document.addEventListener("touchend", (e) => {
    if (touchX === null) return;
    const dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 60) go(current + (dx > 0 ? 1 : -1));
    touchX = null;
  }, { passive: true });
  go((parseInt(location.hash.slice(1), 10) || 1) - 1, false);

  /* ---------------- Load ---------------- */
  async function load() {
    let data = null;
    if (cfg.token) {
      try { const f = await gh(`${DATA_PATH}?ref=${encodeURIComponent(cfg.branch)}`); sha = f.sha; data = JSON.parse(b64decode(f.content)); } catch { /* fall back to the published copy */ }
    }
    if (!data) {
      try { const r = await fetch(`assignments.json?t=${Date.now()}`, { cache: "no-store" }); if (r.ok) data = await r.json(); } catch { /* offline or opened as a file */ }
    }
    saved = cleanMap((data && data.assign) || {});
    if (data && data.savedAt) savedAt = new Date(data.savedAt).toLocaleString("he-IL", { dateStyle: "short", timeStyle: "short" });
    assign = Object.assign({}, saved);
    try { const d = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null"); if (d) assign = cleanMap(d); } catch { /* ignore */ }
    render();
  }
  render();
  load();
})();
