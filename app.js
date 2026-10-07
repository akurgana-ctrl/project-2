(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const initials = (name) => String(name || "").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("");
  const STATUS = { done: "הושלם", active: "בביצוע", planned: "מתוכנן" };
  const ICON = {
    clock: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    edit: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16v4zM14 6l4 4"/></svg>',
    del: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>',
    before: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>',
    after: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>',
    plus: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>'
  };

  // Shared state – editor.js reads and mutates App.data, then calls App.refresh().
  const App = (window.App = { data: { site: {}, directors: [] }, editing: false, esc, ICON, STATUS });

  const photoOf = (d) => d._preview || d.photo;
  function avatar(d) {
    // Initials sit underneath; the photo covers them and removes itself if it fails to load.
    const src = photoOf(d);
    return `<span>${esc(initials(d.name))}</span>` + (src ? `<img src="${esc(src)}" alt="" onerror="this.remove()">` : "");
  }
  // Edit controls rendered on every item; CSS shows them only in edit mode.
  const tools = (kind, i, n) => `
    <span class="edit-tools">
      <button class="edit-tool" data-act="${kind}-edit" data-i="${i}" aria-label="עריכה">${ICON.edit}</button>
      ${i > 0 ? `<button class="edit-tool" data-act="${kind}-before" data-i="${i}" aria-label="הזזה אחורה">${ICON.before}</button>` : ""}
      ${i < n - 1 ? `<button class="edit-tool" data-act="${kind}-after" data-i="${i}" aria-label="הזזה קדימה">${ICON.after}</button>` : ""}
      <button class="edit-tool edit-tool--danger" data-act="${kind}-del" data-i="${i}" aria-label="מחיקה">${ICON.del}</button>
    </span>`;

  /* ---------------- Masthead ---------------- */
  function renderSite() {
    const s = App.data.site || {};
    $("#siteKnesset").textContent = s.knesset || "";
    $("#siteKnesset").hidden = !s.knesset;
    $("#siteTitle").innerHTML = esc(s.title || "").replace("לכנסת", "<em>לכנסת</em>");
    $("#siteSubtitle").textContent = s.subtitle || "";
  }

  /* ---------------- Directors coverflow ---------------- */
  const stage = $("#stage");
  const dotsEl = $("#dots");
  let cards = [];
  let active = 0;

  function renderBoard() {
    const D = App.data.directors;
    let html = D.map((d, i) => {
      const steps = d.goals.reduce((m, g) => m + g.steps.length, 0);
      return `
      <div class="dcard" role="button" tabindex="-1" data-i="${i}" aria-label="${esc(d.name)}, ${esc(d.role)} – לצפייה בתוכנית">
        <span class="dcard__media avatar">${avatar(d)}</span>
        <span class="dcard__shade"></span>
        <span class="dcard__body">
          <span class="dcard__name">${esc(d.name)}</span>
          <span class="dcard__role">${esc(d.role)}</span>
          <span class="dcard__meta">${d.goals.length} מטרות · ${steps} שלבים</span>
          <span><span class="btn btn--gold dcard__cta">לתוכנית המלאה</span></span>
        </span>
        ${tools("dir", i, D.length)}
      </div>`;
    }).join("");
    if (App.editing) {
      html += `
      <div class="dcard dcard--add" role="button" tabindex="-1" data-i="${D.length}" data-act="dir-add" aria-label="הוספת חבר דירקטוריון">
        <span class="add-inner">${ICON.plus}<b>הוספת חבר דירקטוריון</b></span>
      </div>`;
    }
    stage.innerHTML = html;
    cards = [...stage.children];
    $("#boardEmpty").hidden = cards.length > 0;
    dotsEl.innerHTML = cards.map((c, i) =>
      `<button class="dot" role="tab" data-i="${i}" aria-label="${esc(D[i] ? D[i].name : "הוספה")}"></button>`).join("");
    active = Math.max(0, Math.min(active, cards.length - 1));
    layout();
  }

  function layout() {
    const N = cards.length;
    if (!N) return;
    const w = cards[0].offsetWidth || 300;
    const spacing = w * (window.innerWidth < 640 ? 0.72 : 0.62);
    cards.forEach((card, i) => {
      let off = i - active;
      if (off > N / 2) off -= N; // circular – shortest way round
      if (off < -N / 2) off += N;
      const abs = Math.abs(off);
      // RTL: the "next" card sits to the left.
      const scale = 1 - Math.min(abs, 3) * 0.12;
      card.style.transform = `translateX(${-off * spacing}px) translateZ(${-abs * 120}px) rotateY(${off * 28}deg) scale(${scale})`;
      card.style.zIndex = 10 - abs;
      card.style.opacity = abs > 2 ? 0 : abs === 2 ? 0.45 : 1;
      card.style.filter = abs ? `brightness(${1 - abs * 0.22})` : "none";
      card.style.pointerEvents = abs > 2 ? "none" : "auto";
      card.classList.toggle("is-active", off === 0);
      card.tabIndex = off === 0 ? 0 : -1;
      card.setAttribute("aria-hidden", abs > 2 ? "true" : "false");
    });
    [...dotsEl.children].forEach((d, i) => d.setAttribute("aria-selected", i === active));
    $("#prev").hidden = $("#next").hidden = N < 2;
  }
  const go = (i) => { if (!cards.length) return; active = (i + cards.length) % cards.length; layout(); };
  App.goTo = go;

  $("#next").addEventListener("click", () => go(active + 1));
  $("#prev").addEventListener("click", () => go(active - 1));
  dotsEl.addEventListener("click", (e) => { const b = e.target.closest(".dot"); if (b) go(+b.dataset.i); });

  // Swipe / drag
  const cf = $("#coverflow");
  let startX = null, moved = false;
  cf.addEventListener("pointerdown", (e) => { startX = e.clientX; moved = false; });
  cf.addEventListener("pointermove", (e) => { if (startX !== null && Math.abs(e.clientX - startX) > 8) moved = true; });
  cf.addEventListener("pointerup", (e) => {
    if (startX === null) return;
    const dx = e.clientX - startX;
    startX = null;
    if (Math.abs(dx) > 40) go(active + (dx > 0 ? 1 : -1)); // RTL: drag right → next
  });
  cf.addEventListener("pointercancel", () => { startX = null; });

  function activateCard(card) {
    const i = +card.dataset.i;
    if (i !== active) return go(i);
    if (card.dataset.act) return; // "add" card – handled by the editor
    openDirector(i);
  }
  stage.addEventListener("click", (e) => {
    if (moved) { e.stopPropagation(); return; }
    if (e.target.closest(".edit-tool")) return;
    const card = e.target.closest(".dcard");
    if (!card) return;
    if (+card.dataset.i !== active) { e.stopPropagation(); go(+card.dataset.i); return; }
    if (!card.dataset.act) openDirector(+card.dataset.i);
  }, true);
  cf.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") { go(active + 1); cards[active].focus(); }
    if (e.key === "ArrowRight") { go(active - 1); cards[active].focus(); }
    if ((e.key === "Enter" || e.key === " ") && e.target.classList.contains("dcard")) {
      e.preventDefault();
      if (e.target.dataset.act) e.target.click(); else activateCard(e.target);
    }
  });
  window.addEventListener("resize", layout);

  /* ---------------- Plan panel ---------------- */
  const panel = $("#panel");
  const track = $("#goalsTrack");
  const gDots = $("#gDots");
  let current = -1, goalIdx = 0, observer = null, openedByUs = false, lastFocus = null;

  function goalHTML(g, i, total) {
    const done = g.steps.filter((s) => s.status === "done").length;
    const pct = g.steps.length ? Math.round((done / g.steps.length) * 100) : 0;
    const steps = g.steps.map((s) => {
      const st = STATUS[s.status] ? s.status : "planned";
      return `
        <li class="step step--${st}">
          <span class="step__dot" aria-hidden="true"></span>
          <div class="step__row">
            <span class="step__title">${esc(s.title)}</span>
            ${s.when ? `<span class="step__when">${ICON.clock}${esc(s.when)}</span>` : ""}
            <span class="step__status">${STATUS[st]}</span>
          </div>
        </li>`;
    }).join("");
    return `
      <article class="goal" data-i="${i}" aria-label="מטרה ${i + 1} מתוך ${total}">
        <div class="goal__top">
          <span class="badge">${esc(g.type || "מטרה")}</span>
          <span class="badge badge--outline">מטרה ${i + 1}/${total}</span>
        </div>
        ${tools("goal", i, total)}
        <h3>${esc(g.title)}</h3>
        ${g.summary ? `<p class="goal__summary">${esc(g.summary)}</p>` : ""}
        ${g.steps.length ? `
        <div class="progress"><span>התקדמות</span><div class="progress__bar"><i style="width:${pct}%"></i></div><span>${done}/${g.steps.length}</span></div>
        <ol class="timeline">${steps}</ol>` : `<p class="empty-small">עדיין לא הוגדרו שלבים.</p>`}
      </article>`;
  }

  function setGoal(i) {
    goalIdx = i;
    [...track.children].forEach((el, k) => el.classList.toggle("is-current", k === i));
    [...gDots.children].forEach((el, k) => el.setAttribute("aria-selected", k === i));
  }
  function scrollToGoal(i, smooth) {
    const el = track.children[i];
    if (!el) return;
    el.scrollIntoView({ behavior: smooth === false ? "auto" : "smooth", inline: "center", block: "nearest" });
    setGoal(i);
  }

  function renderPanel(i, keepGoal) {
    const d = App.data.directors[i];
    if (!d) return;
    current = i;
    $("#panelName").textContent = d.name;
    $("#panelRole").textContent = d.role;
    $("#panelAvatar").innerHTML = avatar(d);
    let html = d.goals.map((g, k) => goalHTML(g, k, d.goals.length)).join("");
    if (App.editing) {
      html += `<button class="goal goal--add" data-i="${d.goals.length}" data-act="goal-add">${ICON.plus}<b>הוספת מטרה</b></button>`;
    } else if (!d.goals.length) {
      html = `<p class="empty">עדיין לא הוגדרו מטרות.</p>`;
    }
    track.innerHTML = html;
    const items = [...track.children].filter((el) => el.classList.contains("goal"));
    gDots.innerHTML = items.map((el, k) => `<button class="dot" data-i="${k}" aria-label="מטרה ${k + 1}"></button>`).join("");
    const single = items.length < 2;
    $("#gPrev").hidden = $("#gNext").hidden = gDots.hidden = single;

    if (observer) observer.disconnect();
    observer = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) setGoal(+en.target.dataset.i); });
    }, { root: track, threshold: 0.6 });
    items.forEach((el) => observer.observe(el));
    const start = keepGoal == null ? 0 : Math.min(keepGoal, items.length - 1);
    setGoal(start);
    requestAnimationFrame(() => scrollToGoal(start, false));
  }

  function show(i) {
    go(i);
    renderPanel(i);
    if (panel.hidden) {
      lastFocus = document.activeElement;
      panel.hidden = false;
      document.body.classList.add("locked");
      $(".close", panel).focus();
    }
  }
  function hide() {
    if (panel.hidden) return;
    panel.hidden = true;
    current = -1;
    document.body.classList.remove("locked");
    if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }

  function openDirector(i) {
    openedByUs = true;
    location.hash = App.data.directors[i].id; // shareable link, back button closes
  }
  function closeDirector() {
    if (openedByUs) { openedByUs = false; history.back(); }
    else { history.replaceState(null, "", location.pathname + location.search); hide(); }
  }
  App.closeDirector = closeDirector;

  function fromHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    const i = App.data.directors.findIndex((d) => d.id === id);
    if (i >= 0) show(i); else { openedByUs = false; hide(); }
  }
  window.addEventListener("hashchange", fromHash);

  panel.addEventListener("click", (e) => { if (e.target.closest("[data-close]")) closeDirector(); });
  gDots.addEventListener("click", (e) => { const b = e.target.closest(".dot"); if (b) scrollToGoal(+b.dataset.i); });
  $("#gPrev").addEventListener("click", () => scrollToGoal(Math.max(0, goalIdx - 1)));
  $("#gNext").addEventListener("click", () => scrollToGoal(Math.min(track.children.length - 1, goalIdx + 1)));
  track.addEventListener("click", (e) => {
    if (e.target.closest(".edit-tool")) return;
    const g = e.target.closest(".goal");
    if (g && +g.dataset.i !== goalIdx) { e.stopPropagation(); scrollToGoal(+g.dataset.i); }
  }, true);

  document.addEventListener("keydown", (e) => {
    if (panel.hidden || document.querySelector("dialog[open]")) return;
    if (e.target.matches && e.target.matches("input, textarea, select")) return;
    if (e.key === "Escape") closeDirector();
    if (e.key === "ArrowLeft") scrollToGoal(Math.min(track.children.length - 1, goalIdx + 1));
    if (e.key === "ArrowRight") scrollToGoal(Math.max(0, goalIdx - 1));
    if (e.key === "Tab") { // keep focus inside the dialog
      const f = [...panel.querySelectorAll("button:not([hidden]), [href]")].filter((el) => el.offsetParent);
      if (!f.length) return;
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  });

  /* ---------------- Public API for the editor ---------------- */
  App.currentDirector = () => current;
  App.currentGoal = () => goalIdx;
  App.refresh = (opts = {}) => {
    renderSite();
    if (opts.active != null) active = opts.active;
    renderBoard();
    if (current >= 0) {
      if (App.data.directors[current]) renderPanel(current, opts.goal != null ? opts.goal : goalIdx);
      else closeDirector();
    }
  };
  App.setData = (data) => {
    App.data = data;
    App.data.site = App.data.site || {};
    App.data.directors = App.data.directors || [];
    App.refresh();
  };

  async function load() {
    try {
      const res = await fetch("data.json?v=" + Date.now(), { cache: "no-store" });
      if (!res.ok) throw new Error(res.status);
      App.setData(await res.json());
      fromHash();
    } catch (err) {
      $("#boardEmpty").hidden = false;
      $("#boardEmpty").textContent = "לא ניתן לטעון את התוכן כרגע.";
      console.error(err);
    }
  }
  load();
})();
