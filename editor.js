/*
 * In-site editor. Changes are kept in memory and committed to the GitHub
 * repository (data.json + uploaded photos) when "Save" is pressed.
 * Access = a GitHub token with write access to the repo, stored only in this browser.
 */
(function () {
  "use strict";

  const App = window.App;
  const { esc } = App;
  const $ = (sel, root = document) => root.querySelector(sel);
  const CFG_KEY = "kh-editor";
  const DATA_PATH = "data.json";
  const PHOTO_W = 660, PHOTO_H = 990; // 2:3, matches the carousel card

  const GOAL_TYPES = ["הצעת חוק", "שדולה", "תקציב", "פיקוח", "החלטת ממשלה", "כנס / אירוע"];
  const WHEN = ["לפני הבחירות", "לאחר תוצאות הבחירות", "לאחר הקמת הממשלה", "תחילת מושב א׳", "מושב א׳", "מושב ב׳", "דיוני התקציב"];

  /* ---------------- Config ---------------- */
  function defaults() {
    const m = location.hostname.match(/^([^.]+)\.github\.io$/i);
    const seg = location.pathname.split("/").filter(Boolean)[0];
    return {
      owner: m ? m[1] : "akurgana-ctrl",
      repo: m && seg && !seg.includes(".") ? seg : "project-2",
      branch: "main",
      token: ""
    };
  }
  function loadCfg() {
    try { return Object.assign(defaults(), JSON.parse(localStorage.getItem(CFG_KEY) || "{}")); }
    catch { return defaults(); }
  }
  function saveCfg(c) { try { localStorage.setItem(CFG_KEY, JSON.stringify(c)); } catch { /* private mode */ } }
  let cfg = loadCfg();

  /* ---------------- GitHub API ---------------- */
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
        404: "הריפו, הענף או הקובץ לא נמצאו – בדקו את ההגדרות.",
        409: "התוכן השתנה בינתיים במקום אחר. צאו ממצב עריכה, רעננו ונסו שוב.",
        422: "GitHub דחה את השמירה (ייתכן שהתוכן השתנה בינתיים)."
      }[res.status] || `שגיאה מ-GitHub (${res.status}).`;
      const err = new Error(msg); err.status = res.status; throw err;
    }
    return res.json();
  }
  const getFile = (path) => gh(`${path}?ref=${encodeURIComponent(cfg.branch)}`);
  const putFile = (path, contentB64, message, sha) =>
    gh(path, { method: "PUT", body: JSON.stringify({ message, content: contentB64, branch: cfg.branch, ...(sha ? { sha } : {}) }) });

  /* ---------------- State ---------------- */
  let sha = null;        // sha of data.json we loaded – protects against overwriting someone else's change
  let snapshot = null;   // JSON of the last saved state, for "undo changes"
  let dirty = false;
  let busy = false;

  const clean = (data) => JSON.parse(JSON.stringify(data, (k, v) => (k.startsWith("_") ? undefined : v)));
  const D = () => App.data.directors;

  function markDirty() {
    dirty = true;
    updateBar();
  }
  function updateBar() {
    $("#editSave").disabled = !dirty || busy;
    $("#editUndo").disabled = !dirty || busy;
    $("#editSave").textContent = busy ? "שומר…" : dirty ? "שמירה ●" : "נשמר";
  }

  let toastTimer;
  function toast(msg, isError) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.toggle("toast--error", !!isError);
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), isError ? 6000 : 3000);
  }

  /* ---------------- Enter / exit ---------------- */
  async function enter() {
    if (!cfg.token) return openSettings(true);
    busy = true;
    toast("טוען את הגרסה העדכנית…");
    try {
      const file = await getFile(DATA_PATH);
      sha = file.sha;
      const data = JSON.parse(b64decode(file.content));
      App.editing = true;
      document.body.classList.add("editing");
      $("#editBar").hidden = false;
      App.setData(data);
      snapshot = JSON.stringify(clean(App.data));
      dirty = false;
      toast("מצב עריכה פעיל");
    } catch (err) {
      toast(err.message, true);
      if (err.status === 401 || err.status === 403 || err.status === 404) openSettings(true);
    } finally {
      busy = false;
      updateBar();
    }
  }
  function exit() {
    if (dirty && !confirm("יש שינויים שלא נשמרו. לצאת בלי לשמור?")) return;
    if (dirty) App.setData(JSON.parse(snapshot));
    dirty = false;
    App.editing = false;
    document.body.classList.remove("editing");
    $("#editBar").hidden = true;
    App.refresh();
  }

  async function save() {
    if (!dirty || busy) return;
    busy = true; updateBar();
    try {
      // 1. Upload new photos
      for (const d of D()) {
        if (!d._pendingPhoto) continue;
        const path = `assets/directors/${d.id}-${Date.now()}.jpg`;
        await putFile(path, d._pendingPhoto.split(",")[1], `תמונה: ${d.name}`);
        d.photo = path;
        delete d._pendingPhoto; // _preview stays so the image shows until the site rebuilds
      }
      // 2. Commit the content
      const json = JSON.stringify(clean(App.data), null, 2) + "\n";
      const res = await putFile(DATA_PATH, b64encode(json), "עדכון תוכן מהאתר", sha);
      sha = res.content.sha;
      snapshot = JSON.stringify(clean(App.data));
      dirty = false;
      toast("נשמר! האתר יתעדכן לכולם תוך כדקה.");
    } catch (err) {
      toast(err.message, true);
    } finally {
      busy = false; updateBar();
    }
  }

  function undo() {
    if (!dirty || !confirm("לבטל את כל השינויים מאז השמירה האחרונה?")) return;
    App.setData(JSON.parse(snapshot));
    dirty = false; updateBar();
  }

  /* ---------------- Dialog helpers ---------------- */
  const dlg = $("#dlg");
  const form = $("#dlgForm");
  let onSubmit = null;

  function openDialog(title, bodyHTML, submitLabel, handler) {
    form.innerHTML = `
      <header class="dlg__head">
        <h2>${esc(title)}</h2>
        <button type="button" class="close" data-dlg-close aria-label="סגירה">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
      </header>
      <div class="dlg__body">${bodyHTML}</div>
      <footer class="dlg__foot">
        <button type="button" class="btn btn--ghost btn--sm" data-dlg-close>ביטול</button>
        <button type="submit" class="btn btn--gold btn--sm">${esc(submitLabel)}</button>
      </footer>`;
    onSubmit = handler;
    dlg.showModal();
    const first = form.querySelector(".dlg__body input, .dlg__body textarea");
    if (first) first.focus();
  }
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    if (onSubmit && onSubmit(new FormData(form)) === false) return;
    dlg.close();
  });
  form.addEventListener("click", (e) => { if (e.target.closest("[data-dlg-close]")) dlg.close(); });
  dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); }); // backdrop

  const field = (label, name, value, opts = {}) => {
    const attrs = `name="${name}" id="f-${name}" ${opts.required ? "required" : ""} ${opts.list ? `list="${opts.list}"` : ""} ${opts.dir ? `dir="${opts.dir}"` : ""} ${opts.placeholder ? `placeholder="${esc(opts.placeholder)}"` : ""}`;
    const input = opts.textarea
      ? `<textarea ${attrs} rows="${opts.rows || 3}">${esc(value)}</textarea>`
      : `<input type="${opts.type || "text"}" ${attrs} value="${esc(value)}" autocomplete="off">`;
    return `<label class="fld" for="f-${name}"><span>${esc(label)}</span>${input}${opts.hint ? `<small>${opts.hint}</small>` : ""}</label>`;
  };
  const datalist = (id, items) => `<datalist id="${id}">${items.map((v) => `<option value="${esc(v)}">`).join("")}</datalist>`;
  const str = (fd, k) => String(fd.get(k) || "").trim();

  /* ---------------- Settings ---------------- */
  function openSettings(thenEnter) {
    openDialog("הגדרות עריכה", `
      <p class="dlg__note">השמירה נעשית ישירות לריפו ב-GitHub. כדי לשמור צריך מפתח גישה (Token) – פעם אחת בכל מחשב/טלפון. המפתח נשמר רק בדפדפן הזה.</p>
      <details class="dlg__help">
        <summary>איך יוצרים מפתח? (דקה אחת)</summary>
        <ol>
          <li>נכנסים ל-<a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">GitHub → Fine-grained token חדש</a></li>
          <li>שם: "עריכת אתר", תוקף: לבחירתכם</li>
          <li>Repository access: <b>Only select repositories</b> ← בוחרים את <b>${esc(cfg.repo)}</b></li>
          <li>Permissions → Repository permissions → <b>Contents: Read and write</b></li>
          <li>Generate token ← מעתיקים ומדביקים כאן</li>
        </ol>
      </details>
      ${field("מפתח גישה (Token)", "token", cfg.token, { type: "password", required: true, dir: "ltr", placeholder: "github_pat_…" })}
      <div class="fld-row">
        ${field("בעלים (Owner)", "owner", cfg.owner, { required: true, dir: "ltr" })}
        ${field("ריפו", "repo", cfg.repo, { required: true, dir: "ltr" })}
        ${field("ענף", "branch", cfg.branch, { required: true, dir: "ltr" })}
      </div>
      ${cfg.token ? `<button type="button" class="link-btn" id="forgetToken">מחיקת המפתח מהדפדפן הזה</button>` : ""}
    `, thenEnter ? "שמירה וכניסה לעריכה" : "שמירה", (fd) => {
      cfg = { token: str(fd, "token"), owner: str(fd, "owner"), repo: str(fd, "repo"), branch: str(fd, "branch") };
      saveCfg(cfg);
      if (thenEnter) setTimeout(enter);
    });
    const forget = $("#forgetToken");
    if (forget) forget.addEventListener("click", () => {
      cfg.token = ""; saveCfg(cfg); dlg.close(); toast("המפתח נמחק מהדפדפן");
      if (App.editing) { dirty = false; exit(); }
    });
  }

  /* ---------------- Site title ---------------- */
  function editSite() {
    const s = App.data.site;
    openDialog("כותרת העמוד", `
      ${field("שורה עליונה", "knesset", s.knesset, { placeholder: "הכנסת ה-26" })}
      ${field("כותרת", "title", s.title, { required: true })}
      ${field("משפט הסבר", "subtitle", s.subtitle, { textarea: true, rows: 2 })}
    `, "עדכון", (fd) => {
      Object.assign(s, { knesset: str(fd, "knesset"), title: str(fd, "title"), subtitle: str(fd, "subtitle") });
      markDirty(); App.refresh();
    });
  }

  /* ---------------- Directors ---------------- */
  function cropPhoto(file) {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = PHOTO_W; c.height = PHOTO_H;
        const s = Math.max(PHOTO_W / img.width, PHOTO_H / img.height);
        const w = img.width * s, h = img.height * s;
        // Center horizontally, bias slightly upward so faces aren't cut.
        c.getContext("2d").drawImage(img, (PHOTO_W - w) / 2, (PHOTO_H - h) * 0.3, w, h);
        URL.revokeObjectURL(url);
        resolve(c.toDataURL("image/jpeg", 0.86));
      };
      img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("לא ניתן לקרוא את התמונה")); };
      img.src = url;
    });
  }

  function editDirector(i) {
    const isNew = i == null;
    const d = isNew ? { name: "", role: "", bio: "", photo: "", goals: [] } : D()[i];
    let newPhoto = null, removePhoto = false;
    const cur = d._preview || d.photo;
    openDialog(isNew ? "חבר דירקטוריון חדש" : "עריכת חבר דירקטוריון", `
      <div class="photo-pick">
        <div class="photo-pick__img avatar" id="photoPrev">${cur ? `<img src="${esc(cur)}" alt="">` : `<span>${esc((d.name || "?")[0])}</span>`}</div>
        <div class="photo-pick__btns">
          <label class="btn btn--ghost btn--sm">העלאת תמונה<input type="file" accept="image/*" id="photoFile" hidden></label>
          <button type="button" class="link-btn" id="photoRemove" ${cur ? "" : "hidden"}>הסרת תמונה</button>
          <small>התמונה תיחתך אוטומטית לפורמט אנכי</small>
        </div>
      </div>
      ${field("שם מלא", "name", d.name, { required: true })}
      ${field("תפקיד / תחום", "role", d.role, { required: true, placeholder: "ראש תחום …" })}
      ${field("משפט קצר (לא חובה)", "bio", d.bio, { textarea: true, rows: 2 })}
    `, isNew ? "הוספה" : "עדכון", (fd) => {
      Object.assign(d, { name: str(fd, "name"), role: str(fd, "role"), bio: str(fd, "bio") });
      if (isNew) {
        d.id = "d" + Date.now().toString(36);
        D().push(d);
      }
      if (newPhoto) { d._pendingPhoto = newPhoto; d._preview = newPhoto; }
      else if (removePhoto) { d.photo = ""; delete d._pendingPhoto; delete d._preview; }
      markDirty();
      App.refresh({ active: isNew ? D().length - 1 : undefined });
    });
    $("#photoFile").addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        newPhoto = await cropPhoto(file); removePhoto = false;
        $("#photoPrev").innerHTML = `<img src="${newPhoto}" alt="">`;
        $("#photoRemove").hidden = false;
      } catch (err) { toast(err.message, true); }
    });
    $("#photoRemove").addEventListener("click", () => {
      newPhoto = null; removePhoto = true;
      $("#photoPrev").innerHTML = `<span>?</span>`;
      $("#photoRemove").hidden = true;
    });
  }

  /* ---------------- Goals ---------------- */
  const stepRow = (s = {}) => `
    <li class="step-edit">
      <input name="s_title" value="${esc(s.title || "")}" placeholder="מה עושים בשלב הזה" aria-label="תיאור השלב" required>
      <input name="s_when" value="${esc(s.when || "")}" placeholder="מתי" list="dl-when" aria-label="מועד">
      <select name="s_status" aria-label="סטטוס">
        ${Object.entries(App.STATUS).map(([k, v]) => `<option value="${k}" ${(s.status || "planned") === k ? "selected" : ""}>${v}</option>`).join("")}
      </select>
      <span class="step-edit__tools">
        <button type="button" class="edit-tool" data-step="up" aria-label="למעלה">▲</button>
        <button type="button" class="edit-tool" data-step="down" aria-label="למטה">▼</button>
        <button type="button" class="edit-tool edit-tool--danger" data-step="del" aria-label="מחיקת שלב">${App.ICON.del}</button>
      </span>
    </li>`;

  function editGoal(gi) {
    const d = D()[App.currentDirector()];
    if (!d) return;
    const isNew = gi == null;
    const g = isNew ? { type: "הצעת חוק", title: "", summary: "", steps: [] } : d.goals[gi];
    openDialog(isNew ? `מטרה חדשה – ${d.name}` : "עריכת מטרה", `
      <div class="fld-row">
        ${field("סוג", "type", g.type, { list: "dl-types", required: true })}
        ${field("שם המטרה", "title", g.title, { required: true })}
      </div>
      ${field("הסבר קצר", "summary", g.summary, { textarea: true, rows: 2 })}
      <div class="fld"><span>שלבים ולוח זמנים</span>
        <ol class="steps-edit" id="stepsEdit">${(g.steps.length ? g.steps : [{}]).map(stepRow).join("")}</ol>
        <button type="button" class="btn btn--ghost btn--sm" id="addStep">+ הוספת שלב</button>
      </div>
      ${datalist("dl-types", GOAL_TYPES)}${datalist("dl-when", WHEN)}
    `, isNew ? "הוספה" : "עדכון", (fd) => {
      const titles = fd.getAll("s_title"), whens = fd.getAll("s_when"), sts = fd.getAll("s_status");
      Object.assign(g, {
        type: str(fd, "type"), title: str(fd, "title"), summary: str(fd, "summary"),
        steps: titles.map((t, k) => ({ title: String(t).trim(), when: String(whens[k]).trim(), status: sts[k] })).filter((s) => s.title)
      });
      if (isNew) d.goals.push(g);
      markDirty();
      App.refresh({ goal: isNew ? d.goals.length - 1 : gi });
    });
    const list = $("#stepsEdit");
    $("#addStep").addEventListener("click", () => {
      list.insertAdjacentHTML("beforeend", stepRow());
      list.lastElementChild.querySelector("input").focus();
    });
    list.addEventListener("click", (e) => {
      const b = e.target.closest("[data-step]");
      if (!b) return;
      const li = b.closest("li");
      if (b.dataset.step === "up" && li.previousElementSibling) li.parentNode.insertBefore(li, li.previousElementSibling);
      if (b.dataset.step === "down" && li.nextElementSibling) li.parentNode.insertBefore(li.nextElementSibling, li);
      if (b.dataset.step === "del") { if (list.children.length > 1) li.remove(); else li.querySelectorAll("input").forEach((x) => (x.value = "")); }
    });
  }

  /* ---------------- Actions (delegated) ---------------- */
  const move = (arr, i, j) => { const [x] = arr.splice(i, 1); arr.splice(j, 0, x); };

  document.addEventListener("click", (e) => {
    if (!App.editing) return;
    const el = e.target.closest("[data-act]");
    if (!el) return;
    e.preventDefault();
    e.stopPropagation();
    const i = el.dataset.i != null ? +el.dataset.i : null;
    const dirs = D();
    const cd = App.currentDirector();
    switch (el.dataset.act) {
      case "site-edit": return editSite();
      case "dir-add": return editDirector(null);
      case "dir-edit": return editDirector(i);
      case "dir-before": move(dirs, i, i - 1); markDirty(); return App.refresh({ active: i - 1 });
      case "dir-after": move(dirs, i, i + 1); markDirty(); return App.refresh({ active: i + 1 });
      case "dir-del":
        if (!confirm(`למחוק את ${dirs[i].name} וכל המטרות שלו/ה?`)) return;
        dirs.splice(i, 1); markDirty(); return App.refresh({ active: Math.max(0, i - 1) });
      case "goal-add": return editGoal(null);
      case "goal-edit": return editGoal(i);
      case "goal-before": move(dirs[cd].goals, i, i - 1); markDirty(); return App.refresh({ goal: i - 1 });
      case "goal-after": move(dirs[cd].goals, i, i + 1); markDirty(); return App.refresh({ goal: i + 1 });
      case "goal-del":
        if (!confirm(`למחוק את המטרה "${dirs[cd].goals[i].title}"?`)) return;
        dirs[cd].goals.splice(i, 1); markDirty(); return App.refresh({ goal: Math.max(0, i - 1) });
    }
  });

  $("#editFab").addEventListener("click", () => (App.editing ? exit() : enter()));
  $("#editSave").addEventListener("click", save);
  $("#editUndo").addEventListener("click", undo);
  $("#editExit").addEventListener("click", exit);
  $("#editSettings").addEventListener("click", () => openSettings(false));
  window.addEventListener("beforeunload", (e) => { if (dirty) { e.preventDefault(); e.returnValue = ""; } });
  document.addEventListener("keydown", (e) => {
    if (App.editing && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); save(); }
  });
})();
