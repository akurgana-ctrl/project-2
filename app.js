(function () {
  "use strict";

  const SITE = window.SITE || {};
  const DIRECTORS = window.DIRECTORS || [];
  const $ = (sel, root = document) => root.querySelector(sel);

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const initials = (name) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("");
  const STATUS = { done: "הושלם", active: "בביצוע", planned: "מתוכנן" };
  const CLOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';

  function avatar(d) {
    const fallback = `<span>${esc(initials(d.name))}</span>`;
    if (!d.photo) return fallback;
    // If the image fails to load, fall back to initials.
    return `<img src="${esc(d.photo)}" alt="" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement('span'),{textContent:'${esc(initials(d.name))}'}))">`;
  }

  /* ---------------- Header / hero ---------------- */
  const burger = $("#burger");
  const nav = $("#nav");
  burger.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    burger.setAttribute("aria-expanded", open);
  });
  nav.addEventListener("click", (e) => {
    if (e.target.closest("a")) { nav.classList.remove("open"); burger.setAttribute("aria-expanded", "false"); }
  });

  $("#heroEyebrow").textContent = SITE.knesset || "";
  $("#heroTitle").innerHTML = esc(SITE.heroTitle || "").replace("לכנסת", "<em>לכנסת</em>");
  $("#heroText").textContent = SITE.heroText || "";
  const goalCount = DIRECTORS.reduce((n, d) => n + d.goals.length, 0);
  const stepCount = DIRECTORS.reduce((n, d) => n + d.goals.reduce((m, g) => m + g.steps.length, 0), 0);
  $("#heroStats").innerHTML = [
    [DIRECTORS.length, "חברי דירקטוריון"],
    [goalCount, "מטרות"],
    [stepCount, "שלבי ביצוע"]
  ].map(([n, l]) => `<div class="stat"><b>${n}</b><span>${l}</span></div>`).join("");
  $("#year").textContent = new Date().getFullYear();
  if (SITE.contactEmail) $("#contactLink").href = "mailto:" + SITE.contactEmail;

  /* ---------------- Directors coverflow ---------------- */
  const stage = $("#stage");
  const dotsEl = $("#dots");
  const N = DIRECTORS.length;
  let active = 0;

  stage.innerHTML = DIRECTORS.map((d, i) => `
    <button class="dcard" data-i="${i}" aria-label="${esc(d.name)}, ${esc(d.role)} – לצפייה בתוכנית">
      <span class="dcard__media avatar">${avatar(d)}</span>
      <span class="dcard__shade"></span>
      <span class="dcard__body">
        <span class="dcard__name">${esc(d.name)}</span>
        <span class="dcard__role">${esc(d.role)}</span>
        <span class="dcard__meta">${d.goals.length} מטרות · ${d.goals.reduce((m, g) => m + g.steps.length, 0)} שלבים</span>
        <span><span class="btn btn--gold dcard__cta">לתוכנית המלאה</span></span>
      </span>
    </button>`).join("");
  dotsEl.innerHTML = DIRECTORS.map((d, i) =>
    `<button class="dot" role="tab" data-i="${i}" aria-label="${esc(d.name)}"></button>`).join("");

  const cards = [...stage.children];
  const dots = [...dotsEl.children];

  function layout() {
    const w = cards[0] ? cards[0].offsetWidth : 300;
    const narrow = window.innerWidth < 640;
    const spacing = w * (narrow ? 0.72 : 0.62);
    cards.forEach((card, i) => {
      let off = i - active;
      if (off > N / 2) off -= N;      // circular – shortest way round
      if (off < -N / 2) off += N;
      const abs = Math.abs(off);
      // RTL: the "next" card sits to the left.
      const x = -off * spacing;
      const rot = off * 28;
      const scale = 1 - Math.min(abs, 3) * 0.12;
      card.style.transform = `translateX(${x}px) translateZ(${-abs * 120}px) rotateY(${rot}deg) scale(${scale})`;
      card.style.zIndex = 10 - abs;
      card.style.opacity = abs > 2 ? 0 : abs === 2 ? 0.45 : 1;
      card.style.filter = abs ? `brightness(${1 - abs * 0.22})` : "none";
      card.style.pointerEvents = abs > 2 ? "none" : "auto";
      card.classList.toggle("is-active", off === 0);
      card.tabIndex = off === 0 ? 0 : -1;
      card.setAttribute("aria-hidden", abs > 2 ? "true" : "false");
    });
    dots.forEach((d, i) => d.setAttribute("aria-selected", i === active));
  }
  const go = (i) => { active = (i + N) % N; layout(); };

  $("#next").addEventListener("click", () => go(active + 1));
  $("#prev").addEventListener("click", () => go(active - 1));
  dotsEl.addEventListener("click", (e) => { const b = e.target.closest(".dot"); if (b) go(+b.dataset.i); });

  // Swipe / drag
  const cf = $("#coverflow");
  let startX = null, moved = false;
  cf.addEventListener("pointerdown", (e) => { startX = e.clientX; moved = false; });
  cf.addEventListener("pointermove", (e) => { if (startX !== null && Math.abs(e.clientX - startX) > 8) moved = true; });
  const endDrag = (e) => {
    if (startX === null) return;
    const dx = e.clientX - startX;
    startX = null;
    if (Math.abs(dx) > 40) go(active + (dx > 0 ? 1 : -1)); // RTL: drag right → next
  };
  cf.addEventListener("pointerup", endDrag);
  cf.addEventListener("pointercancel", () => { startX = null; });

  stage.addEventListener("click", (e) => {
    const card = e.target.closest(".dcard");
    if (!card || moved) return;
    const i = +card.dataset.i;
    if (i === active) openDirector(i); else go(i);
  });
  cf.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") { go(active + 1); cards[active].focus(); }
    if (e.key === "ArrowRight") { go(active - 1); cards[active].focus(); }
  });
  window.addEventListener("resize", layout);
  layout();

  /* ---------------- Plan panel ---------------- */
  const panel = $("#panel");
  const track = $("#goalsTrack");
  const gDots = $("#gDots");
  let goalIdx = 0, observer = null, openedByUs = false, lastFocus = null;

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
            <span class="step__when">${CLOCK}${esc(s.when)}</span>
            <span class="step__status">${STATUS[st]}</span>
          </div>
        </li>`;
    }).join("");
    return `
      <article class="goal" data-i="${i}" aria-label="מטרה ${i + 1} מתוך ${total}">
        <div class="goal__top">
          <span class="badge">${esc(g.type)}</span>
          <span class="badge badge--outline">מטרה ${i + 1}/${total}</span>
        </div>
        <h3>${esc(g.title)}</h3>
        ${g.summary ? `<p class="goal__summary">${esc(g.summary)}</p>` : ""}
        <div class="progress"><span>התקדמות</span><div class="progress__bar"><i style="width:${pct}%"></i></div><span>${done}/${g.steps.length}</span></div>
        <ol class="timeline">${steps}</ol>
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

  function render(i) {
    const d = DIRECTORS[i];
    $("#panelName").textContent = d.name;
    $("#panelRole").textContent = d.role;
    $("#panelAvatar").innerHTML = avatar(d);
    track.innerHTML = d.goals.map((g, k) => goalHTML(g, k, d.goals.length)).join("");
    gDots.innerHTML = d.goals.map((g, k) => `<button class="dot" data-i="${k}" aria-label="${esc(g.title)}"></button>`).join("");
    const single = d.goals.length < 2;
    $("#gPrev").hidden = $("#gNext").hidden = gDots.hidden = single;

    if (observer) observer.disconnect();
    observer = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) setGoal(+en.target.dataset.i); });
    }, { root: track, threshold: 0.6 });
    [...track.children].forEach((el) => observer.observe(el));
    setGoal(0);
    requestAnimationFrame(() => scrollToGoal(0, false));
  }

  function show(i) {
    go(i);
    render(i);
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
    document.body.classList.remove("locked");
    if (lastFocus) lastFocus.focus();
  }

  function openDirector(i) {
    openedByUs = true;
    location.hash = DIRECTORS[i].id; // shareable link, back button closes
  }
  function closeDirector() {
    if (openedByUs) { openedByUs = false; history.back(); }
    else { history.replaceState(null, "", location.pathname + location.search + "#board"); hide(); }
  }

  function fromHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    const i = DIRECTORS.findIndex((d) => d.id === id);
    if (i >= 0) show(i); else { openedByUs = false; hide(); }
  }
  window.addEventListener("hashchange", fromHash);

  panel.addEventListener("click", (e) => { if (e.target.closest("[data-close]")) closeDirector(); });
  gDots.addEventListener("click", (e) => { const b = e.target.closest(".dot"); if (b) scrollToGoal(+b.dataset.i); });
  $("#gPrev").addEventListener("click", () => scrollToGoal(Math.max(0, goalIdx - 1)));
  $("#gNext").addEventListener("click", () => scrollToGoal(Math.min(track.children.length - 1, goalIdx + 1)));
  track.addEventListener("click", (e) => {
    const g = e.target.closest(".goal");
    if (g && +g.dataset.i !== goalIdx) scrollToGoal(+g.dataset.i);
  });

  document.addEventListener("keydown", (e) => {
    if (panel.hidden) return;
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

  fromHash();
})();
