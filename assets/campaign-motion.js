// Spring motion for the campaign pages. join.js falls back to CSS when this is absent.
(function () {
  if (!window.Motion || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const { animate, inView, press, scroll, stagger } = window.Motion;

  const settle = { type: "spring", bounce: 0, visualDuration: 0.5 };
  document.documentElement.classList.add("motion-on");

  /* Hero: settles once, then drifts a little slower than the page as it scrolls away */
  const hero = document.querySelector(".hero");
  const heroImg = hero && hero.querySelector(".hero__img");
  if (heroImg) {
    animate(heroImg, { scale: [1.04, 1] }, { duration: 1.6, ease: [0.22, 1, 0.36, 1] });
    scroll(animate(heroImg, { y: [0, 90] }, { ease: "linear" }), { target: hero, offset: ["start start", "end start"] });
  }

  /* Entrances: the parts of each section arrive in order */
  document.querySelectorAll("main section").forEach((section) => {
    const items = section.querySelectorAll("[data-rise]:not(.zero__num)");
    if (!items.length) return;
    inView(section, () => {
      animate(items, { opacity: [0, 1], y: [20, 0] }, { ...settle, delay: stagger(0.07) });
    }, { amount: 0.15 });
  });

  /* The zero lands like a stamp */
  const zero = document.querySelector(".zero__num");
  if (zero) {
    inView(zero, () => {
      animate(zero, { opacity: [0, 1], scale: [1.6, 1] }, { type: "spring", bounce: 0.35, visualDuration: 0.5 });
    }, { amount: 0.6 });
  }

  /* Buttons: pressed down on touch, spring back on release */
  press(".btn", (el) => {
    animate(el, { scale: 0.96 }, { type: "spring", bounce: 0, visualDuration: 0.12 });
    return () => animate(el, { scale: 1 }, { type: "spring", bounce: 0.4, visualDuration: 0.3 });
  });

  const dock = document.getElementById("dock");
  if (dock) animate(dock, { y: "140%" }, { duration: 0 });

  window.campaignMotion = {
    /* Bottom dock on phones: rises in and drops out on the same path, interruptible */
    dock(el, on) {
      animate(el, { y: on ? "0%" : "140%" }, on
        ? { type: "spring", bounce: 0.15, visualDuration: 0.45 }
        : { type: "spring", bounce: 0, visualDuration: 0.3 });
    },

    /* Diagram: loose squares, then the ribbon and the final shape fly in from the crowd */
    diagram(svg) {
      inView(svg, () => {
        const rects = [...svg.querySelectorAll("rect")];
        const crowd = rects.filter((r) => r.dataset.zone === "0");
        const rest = rects.filter((r) => r.dataset.zone !== "0");
        animate(crowd, { opacity: [0, 1], scale: [0.4, 1] }, { ...settle, delay: stagger(0.008) });
        rest.forEach((r, i) => {
          const from = crowd[(i * 7) % crowd.length];
          const dx = from.x.baseVal.value - r.x.baseVal.value;
          const dy = from.y.baseVal.value - r.y.baseVal.value;
          animate(r, { opacity: [0, 1], x: [dx, 0], y: [dy, 0] },
            { type: "spring", bounce: 0.15, visualDuration: 0.7, delay: 0.35 + i * 0.012 });
        });
      }, { amount: 0.35 });
    },
  };
})();
