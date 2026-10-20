// Fill these in before launch.
const CONFIG = {
  // Peach campaign link, e.g. "https://www.peach-in.com/cmp/AbC123xyz"
  peachCampaign: "",
  // YouTube / Vimeo link or a direct .mp4 path (the video is already in the page)
  video: "",
};

document.documentElement.classList.add("js");

/* Video */
(function mountVideo() {
  const frame = document.getElementById("videoFrame");
  const src = CONFIG.video.trim();
  if (!src) return;
  const yt = src.match(/(?:youtu\.be\/|v=|shorts\/|embed\/)([\w-]{11})/);
  const vimeo = src.match(/vimeo\.com\/(\d+)/);
  let el;
  if (yt || vimeo) {
    el = document.createElement("iframe");
    el.src = yt
      ? `https://www.youtube-nocookie.com/embed/${yt[1]}?rel=0&playsinline=1`
      : `https://player.vimeo.com/video/${vimeo[1]}`;
    el.allow = "autoplay; fullscreen; picture-in-picture; encrypted-media";
    el.allowFullscreen = true;
    el.title = "הסרטון";
    el.loading = "lazy";
  } else {
    el = document.createElement("video");
    el.src = src;
    el.controls = true;
    el.playsInline = true;
    el.preload = "metadata";
    el.poster = "assets/plane.jpg";
  }
  frame.querySelector(".video__soon")?.remove();
  frame.appendChild(el);
})();

/* Peach */
(function mountPeach() {
  const box = document.getElementById("peach");
  const url = CONFIG.peachCampaign.trim();
  const id = (url.match(/\/(?:cmp|org)\/(?:iframe\/)?([\w-]+)/) || [])[1];
  if (!id) return;
  const kind = url.includes("/org/") ? "org" : "cmp";
  document.getElementById("peachLink").href = url;
  const frame = document.createElement("iframe");
  frame.src = `https://www.peach-in.com/${kind}/iframe/${id}`;
  frame.title = "טופס תמיכה – Peach";
  frame.loading = "lazy";
  frame.allow = "payment";
  box.querySelector(".join__fallback").replaceWith(frame);
})();

/* Diagram: scattered voices -> one ribbon of pressure -> the X */
(function drawPlan() {
  const svg = document.getElementById("planDiagram");
  const NS = "http://www.w3.org/2000/svg";
  const phone = matchMedia("(max-width: 900px)");
  let seed = 7;
  const rand = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;

  function build() {
    seed = 7;
    svg.textContent = "";
    const vertical = phone.matches;
    const W = vertical ? 300 : 1200, H = vertical ? 920 : 300, s = 14, p = 20;
    const [z0, z1, z2, spread] = vertical ? [10, 330, 690, 260] : [20, 450, 870, 340];
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    // place(a, b): a runs along the reading axis (right to left, or top to bottom)
    const place = (a, b) => (vertical ? [b, a] : [W - a, b]);
    const cells = [];

    for (let i = 0; i < 54; i++) {
      cells.push({ at: place(z0 + rand() * spread, 10 + rand() * 270), fill: rand() > .5 ? "#3a3a3d" : "#6e6e6c", zone: 0 });
    }
    for (let c = 0; c < 15; c++) for (let r = 0; r < 3; r++) {
      cells.push({ at: place(z1 + c * p, 120 + r * p), fill: "#b9b9b4", zone: 1 });
    }
    // a check mark: short stroke down, long stroke up
    const check = [];
    for (let k = 0; k < 4; k++) check.push([k, 5 + k], [k, 6 + k]);
    for (let k = 0; k < 8; k++) check.push([3 + k, 8 - k], [3 + k, 9 - k]);
    for (const [i, j] of check) {
      cells.push({ at: place(z2 + (vertical ? j : 10 - i) * p, 40 + (vertical ? i : j) * p), fill: "#e3241b", zone: 2 });
    }
    for (const cell of cells) {
      const r = document.createElementNS(NS, "rect");
      r.setAttribute("x", cell.at[0] - (vertical ? 0 : s));
      r.setAttribute("y", cell.at[1]);
      r.setAttribute("width", s);
      r.setAttribute("height", s);
      r.setAttribute("fill", cell.fill);
      r.dataset.zone = cell.zone;
      svg.appendChild(r);
    }
  }
  build();
  phone.addEventListener("change", build);

  if (matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;
  svg.classList.add("is-waiting");
  new IntersectionObserver((entries, io) => {
    if (!entries[0].isIntersecting) return;
    io.disconnect();
    svg.querySelectorAll("rect").forEach((r, n) => {
      r.animate(
        [{ opacity: 0, transform: "translateY(-14px)" }, { opacity: 1, transform: "none" }],
        { duration: 500, delay: Number(r.dataset.zone) * 300 + (n % 60) * 6, easing: "cubic-bezier(.2,.7,.2,1)", fill: "backwards" }
      );
    });
  }, { threshold: .35 }).observe(svg);
})();

/* Entrances, staggered within each section */
(function rise() {
  const items = document.querySelectorAll("[data-rise]");
  if (!("IntersectionObserver" in window)) { items.forEach((el) => el.classList.add("is-in")); return; }
  document.querySelectorAll("section").forEach((sec) => {
    sec.querySelectorAll("[data-rise]").forEach((el, i) => el.style.setProperty("--i", i));
  });
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } });
  }, { rootMargin: "0px 0px -8% 0px" });
  items.forEach((el) => io.observe(el));
})();

/* Phone dock: shown after the hero, hidden once the form is on screen */
(function dock() {
  const dockEl = document.getElementById("dock");
  const hero = document.querySelector(".hero");
  const join = document.getElementById("join");
  if (!("IntersectionObserver" in window)) return;
  let pastHero = false, atJoin = false;
  const update = () => dockEl.classList.toggle("is-on", pastHero && !atJoin);
  new IntersectionObserver(([e]) => { pastHero = !e.isIntersecting; update(); }).observe(hero);
  new IntersectionObserver(([e]) => { atJoin = e.isIntersecting; update(); }).observe(join);
})();
