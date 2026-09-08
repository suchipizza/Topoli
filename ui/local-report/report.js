(function () {
  "use strict";
  var D = window.TOPOLI;
  var lang = D.lang;
  var rendered = D.lang;
  function t(key) {
    var dict = D.i18n[lang] || {};
    var v = dict[key];
    if (v === undefined || v === "__TODO__") v = (D.i18n.en || {})[key];
    return v === undefined ? key : v;
  }
  function fill(el, key) {
    var v = t(key);
    var slots = el.getAttribute("data-slots");
    if (slots) {
      var s = JSON.parse(slots);
      Object.keys(s).forEach(function (k) { v = v.split("{" + k + "}").join(s[k]); });
    }
    el.textContent = v;
  }
  function applyLang() {
    if (lang === rendered) { var s0 = document.getElementById("lang"); if (s0) s0.value = lang; return; }
    rendered = lang;
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) { fill(el, el.getAttribute("data-i18n")); });
    document.querySelectorAll("[data-l10n]").forEach(function (el) {
      var obj = JSON.parse(el.getAttribute("data-l10n"));
      el.textContent = obj[lang] || obj.en || "";
    });
    document.querySelectorAll("[data-href-lang]").forEach(function (el) {
      el.setAttribute("href", el.getAttribute("data-href-lang").split("{lang}").join(lang));
    });
    var sel = document.getElementById("lang");
    if (sel && sel.value !== lang) sel.value = lang;
    try { localStorage.setItem("topoli.lang", lang); } catch (e) {}
  }
  var sel = document.getElementById("lang");
  if (sel) sel.addEventListener("change", function () { lang = sel.value; applyLang(); });
  try { var saved = localStorage.getItem("topoli.lang"); if (saved && D.i18n[saved]) lang = saved; } catch (e) {}

  // sections
  document.querySelectorAll("section.sec > h2 > button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var open = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", open ? "false" : "true");
      var body = document.getElementById(btn.getAttribute("aria-controls"));
      if (body) body.classList.toggle("open", !open);
    });
  });

  // map tiles (fetched at view time from swisstopo; offline → static fallback image stays)
  var M = D.map;
  var tilesEl = document.getElementById("tiles");
  if (M && tilesEl && navigator.onLine !== false) {
    var probe = new Image();
    probe.onload = function () {
      var fb = document.getElementById("map-fallback");
      if (fb) fb.style.visibility = "hidden";
      M.tiles.forEach(function (tt) {
        var img = document.createElement("img");
        img.alt = "";
        img.loading = "lazy";
        img.decoding = "async";
        img.src = tt.url;
        img.style.left = tt.x + "px";
        img.style.top = tt.y + "px";
        img.style.width = tt.size + "px";
        img.style.height = tt.size + "px";
        tilesEl.appendChild(img);
      });
      tilesEl.style.display = "block";
    };
    probe.onerror = function () { tilesEl.style.display = "none"; };
    probe.src = M.tiles.length ? M.tiles[0].url : "";
  }

  // share
  var copy = document.getElementById("copy-summary");
  if (copy) copy.addEventListener("click", function () {
    var txt = document.getElementById("summary-text").textContent;
    if (navigator.clipboard) navigator.clipboard.writeText(txt);
    copy.textContent = t("share.copied");
  });
  var star = document.getElementById("star-btn");
  if (star) star.addEventListener("click", function () {
    var img = new Image(); img.src = D.hit_url + "&lang=" + encodeURIComponent(lang);
  });

  // waitlist (posts to the site only when the visitor clicks; no-JS fallback is the link)
  var form = document.getElementById("waitlist-form");
  if (form) form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var votes = [];
    form.querySelectorAll("input[name=vote]:checked").forEach(function (c) { votes.push(c.value); });
    var payload = { votes: votes, email: form.email.value || null, lang: lang, src: "report" };
    var status = document.getElementById("waitlist-status");
    fetch(D.waitlist_url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (r) { status.textContent = r.ok ? t("waitlist.thanks") : t("waitlist.error"); })
      .catch(function () { status.textContent = t("waitlist.error"); });
  });

  applyLang();
})();
