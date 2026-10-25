// Spring motion for the campaign pages. join.js falls back to CSS when this is absent.
(function () {
  if (!window.Motion || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const { animate, inView, press, scroll, stagger } = window.Motion;

  const settle = { type: "spring", bounce: 0, visualDuration: 0.5 };
  document.documentElement.classList.add("motion-on");

  /* Hero: two planes. The plate settles and falls behind; the subject keeps its own path */
  const hero = document.querySelector(".hero");
  const media = hero && hero.querySelector(".hero__media");
  if (media) {
    const plate = media.querySelector(".hero__plate");
    const subject = media.querySelector(".hero__subject");
    const exit = { target: hero, offset: ["start start", "end start"] };
    animate(plate, { scale: [1.08, 1.03] }, { duration: 1.6, ease: [0.22, 1, 0.36, 1] });
    scroll(animate(plate, { y: [0, 110] }, { ease: "linear" }), exit);

    if (media.dataset.depth === "walk") {
      /* he turns toward the plane and goes */
      scroll(animate(subject, { x: ["0%", "-16%"], y: [0, 24], scale: [1, 0.92], opacity: [1, 0.15] }, { ease: "linear" }), exit);
    } else {
      /* the chair comes forward while the hall falls away */
      scroll(animate(subject, { y: [0, -36], scale: [1, 1.05] }, { ease: "linear" }), exit);
      scroll(animate(plate, { filter: ["blur(0px)", "blur(3px)"] }, { ease: "linear" }), exit);
    }

    if (matchMedia("(hover: hover) and (pointer: fine)").matches) {
      hero.addEventListener("pointermove", (e) => {
        const r = hero.getBoundingClientRect();
        const dx = (e.clientX - r.left) / r.width - 0.5;
        const dy = (e.clientY - r.top) / r.height - 0.5;
        animate(plate, { x: dx * -18, rotate: dx * 0.4 }, { type: "spring", bounce: 0, visualDuration: 0.6 });
        animate(media, { rotateX: dy * -2, rotateY: dx * 3 }, { type: "spring", bounce: 0, visualDuration: 0.6 });
      });
    }
  }

  /* Video: the frame comes up to full size as it reaches the middle of the screen */
  const clip = document.querySelector(".video__frame video, .video__frame img");
  if (clip) {
    scroll(animate(clip, { scale: [0.86, 1] }, { ease: "linear" }),
      { target: clip.parentElement, offset: ["start end", "center center"] });
  }

  /* Donation: the red field opens from the middle as it arrives */
  const join = document.getElementById("join");
  if (join) {
    scroll(animate(join, { clipPath: ["inset(0% 12% 0% 12%)", "inset(0% 0% 0% 0%)"] }, { ease: "linear" }),
      { target: join, offset: ["start end", "start 45%"] });
  }

  /* The lock above the donation opens as the section comes up */
  const shackle = document.querySelector(".join__shackle");
  if (shackle) {
    scroll(animate(shackle, { y: [0, -9, -9], rotate: [0, 0, -38] }, { ease: "linear" }),
      { target: join, offset: ["start 85%", "start 25%"] });
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
