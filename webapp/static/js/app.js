// ---------- Giao diện Sáng / Tối ----------
(function initTheme() {
  try {
    const saved = localStorage.getItem("tt_theme");
    if (saved === "dark" || saved === "light") {
      document.documentElement.setAttribute("data-theme", saved);
    }
  } catch (e) {}
})();

const ICON_MOON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>';
const ICON_SUN = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>';
const themeMedia = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

function isDarkTheme() {
  const cur = document.documentElement.getAttribute("data-theme");
  if (cur === "dark") return true;
  if (cur === "light") return false;
  return Boolean(themeMedia && themeMedia.matches);
}

const btnTheme = document.getElementById("btn-theme");
function syncThemeButton() {
  if (!btnTheme) return;
  const dark = isDarkTheme();
  btnTheme.setAttribute("aria-pressed", String(dark));
  btnTheme.innerHTML = dark ? ICON_SUN : ICON_MOON;
}
if (btnTheme) {
  syncThemeButton();
  btnTheme.addEventListener("click", () => {
    const next = isDarkTheme() ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("tt_theme", next); } catch (e) {}
    syncThemeButton();
  });
  if (themeMedia && themeMedia.addEventListener) {
    themeMedia.addEventListener("change", () => {
      if (!document.documentElement.getAttribute("data-theme")) syncThemeButton();
    });
  }
}

// ---------- Lightbox phóng to ảnh sự kiện ----------
const LIGHTBOX_SEL = ".ev-img, .banner img, .card.pig img";
const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightbox-img");
let lightboxTrigger = null;

function enhanceLightboxImages(root = document) {
  if (!root || !root.querySelectorAll) return;
  root.querySelectorAll(LIGHTBOX_SEL).forEach(img => {
    if (!img.hasAttribute("tabindex")) img.setAttribute("tabindex", "0");
    if (!img.hasAttribute("role")) img.setAttribute("role", "button");
  });
}

function openLightbox(img) {
  if (!img || !lightbox || !lightboxImg) return;
  lightboxTrigger = document.activeElement instanceof HTMLElement ? document.activeElement : img;
  lightboxImg.src = img.src;
  lightboxImg.alt = img.alt || "Ảnh phóng to";
  if (!lightbox.hasAttribute("tabindex")) lightbox.setAttribute("tabindex", "-1");
  lightbox.hidden = false;
  const closeBtn = lightbox.querySelector("button");
  if (closeBtn) closeBtn.focus({preventScroll: true});
  else lightbox.focus({preventScroll: true});
}

function closeLightbox() {
  if (!lightbox || lightbox.hidden) return;
  lightbox.hidden = true;
  if (lightboxTrigger && lightboxTrigger.isConnected && typeof lightboxTrigger.focus === "function") {
    lightboxTrigger.focus();
  }
  lightboxTrigger = null;
}

enhanceLightboxImages();
if (document.body && typeof MutationObserver !== "undefined") {
  new MutationObserver(muts => {
    for (const m of muts) {
      for (const n of m.addedNodes) {
        if (n.nodeType !== 1) continue;
        if (n.matches && n.matches(LIGHTBOX_SEL)) enhanceLightboxImages(n.parentElement || document);
        else enhanceLightboxImages(n);
      }
    }
  }).observe(document.body, {childList: true, subtree: true});
}

document.addEventListener("click", e => {
  const img = e.target.closest(LIGHTBOX_SEL);
  if (img && lightbox && lightboxImg) {
    openLightbox(img);
    return;
  }
  if (lightbox && !lightbox.hidden && e.target.closest("#lightbox")) {
    closeLightbox();
  }
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && lightbox && !lightbox.hidden) {
    e.preventDefault();
    closeLightbox();
    return;
  }
  if (e.key === "Enter" || e.key === " ") {
    const img = e.target.closest(LIGHTBOX_SEL);
    if (img && lightbox && lightbox.hidden) {
      e.preventDefault();
      openLightbox(img);
      return;
    }
    if (lightbox && !lightbox.hidden && e.target === lightbox) {
      e.preventDefault();
      closeLightbox();
    }
  }
});

// ---------- Tiện ích ----------
async function api(method, url, body) {
  const r = await fetch(url, {
    method,
    headers: body ? {"Content-Type": "application/json"} : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await r.json(); } catch (e) {}
  return {ok: r.ok, data};
}
const esc = s => String(s ?? "").replace(/[&<>"']/g, c =>
  ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
function store(k, v) {
  try { if (v === undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k, v); } catch (e) {}
  return null;
}

// ---------- Nút "Đúng" / "Báo nhầm" (dùng cho cả banner và danh sách) ----------
async function phanHoi(id, ph) {
  const {ok} = await api("POST", `/api/su-kien/${id}/phan-hoi`, {phan_hoi: ph});
  if (!ok) return false;
  document.querySelectorAll(`[data-ev="${id}"] .ev-actions`).forEach(el => {
    el.outerHTML = `<div class="ev-actions done">${ph === "dung" ? "Đã xác nhận đúng" : "Đã báo nhầm"}</div>`;
  });
  const msgs = document.getElementById("msgs");
  const statSk = document.getElementById("stat-sk");
  if (msgs || statSk) {
    try {
      const r = await fetch(location.href);
      if (r.ok) {
        const doc = new DOMParser().parseFromString(await r.text(), "text/html");
        const newMsgs = doc.getElementById("msgs");
        if (msgs && newMsgs) {
          msgs.innerHTML = newMsgs.innerHTML;
          enhanceLightboxImages(msgs);
        }
        const newStatSk = doc.getElementById("stat-sk");
        if (statSk && newStatSk) {
          statSk.textContent = newStatSk.textContent;
          const wrap = statSk.closest("div");
          const newWrap = newStatSk.closest("div");
          if (wrap && newWrap) wrap.className = newWrap.className;
        }
      }
    } catch (e) {}
  }
  return true;
}
document.addEventListener("click", async e => {
  const b = e.target.closest("[data-ph]");
  if (!b) return;
  const id = b.dataset.id;
  if (await phanHoi(id, b.dataset.ph)) skip(id);   // đã trả lời ở đâu cũng bỏ khỏi banner
});

// ---------- Banner (hỏi /api/thong-bao mỗi 3 giây) ----------
const banner = document.getElementById("banner");
// Hàng đợi và mã sự kiện đã thấy được giữ trong sessionStorage để không mất khi chuyển trang.
let hangDoi = [];   // sự kiện đang chờ hiện
let sau = null;
try {
  hangDoi = JSON.parse(store("hangDoi") || "[]");
  const s0 = store("sau"); sau = s0 === null || s0 === undefined ? null : Number(s0);
} catch (e) { hangDoi = []; sau = null; }

function veBanner() {
  store("hangDoi", JSON.stringify(hangDoi));
  if (!hangDoi.length) { banner.hidden = true; return; }
  const e = hangDoi[0];
  banner.className = "banner " + e.muc;
  banner.dataset.ev = e.id;
  banner.hidden = false;
  banner.innerHTML = `
    <div class="b-head"><b>${esc(e.ten_loai)}</b> · <span class="mono-tag">Ô ${esc(e.o)}</span>
      ${hangDoi.length > 1 ? `<span class="b-n">+${hangDoi.length - 1}</span>` : ""}
      <button type="button" class="b-x" aria-label="Đóng" data-skip="${e.id}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button></div>
    <div class="b-sub mono-num">${esc(e.thoi_gian.slice(11, 16))} · ${esc(e.ten_muc)}</div>
    ${e.anh ? `<img src="/${esc(e.anh)}" alt="Ảnh sự kiện">` : ""}
    <div class="ev-actions">
      <button type="button" data-ph="dung" data-id="${e.id}">Đúng</button>
      <button type="button" data-ph="bao_nham" data-id="${e.id}">Báo nhầm</button>
    </div>`;
  enhanceLightboxImages(banner);
}
function skip(id) {
  hangDoi = hangDoi.filter(e => String(e.id) !== String(id));
  veBanner();
}
banner && banner.addEventListener("click", e => {
  const x = e.target.closest("[data-skip]");
  if (x) skip(x.dataset.skip);
});

async function hoi() {
  const {ok, data} = await api("GET", "/api/thong-bao" + (sau === null ? "" : `?sau=${sau}`));
  if (!ok) return;
  if (sau !== null && data.ds.length) {
    hangDoi.push(...data.ds.filter(e => !hangDoi.some(x => x.id === e.id)));
    veBanner();
    // báo cho trang đang xem để tải lại danh sách nếu cần
    document.dispatchEvent(new CustomEvent("co-su-kien-moi"));
  }
  sau = data.moi_nhat;
  store("sau", String(sau));
}
if (banner) { veBanner(); hoi(); setInterval(hoi, 3000); }
// Trang Sự kiện / Trang chủ tự làm mới nội dung (không tải lại cả trang nên banner không mất)
document.addEventListener("co-su-kien-moi", async () => {
  if (!document.body.dataset.autoreload) return;
  const boxThem = document.getElementById("box-them-o");
  if (boxThem && !boxThem.hidden) return;
  const r = await fetch(location.href);
  if (!r.ok) return;
  const doc = new DOMParser().parseFromString(await r.text(), "text/html");
  const moi = doc.querySelector(".screen"), cu = document.querySelector(".screen");
  const curBox = document.getElementById("box-them-o");
  if (curBox && !curBox.hidden) return;
  if (moi && cu) {
    cu.innerHTML = moi.innerHTML;
    enhanceLightboxImages(cu);
  }
});

// ---------- Trang Cài đặt ----------
const form = document.getElementById("form-cai-dat");
if (form) {
  const syncAutoCards = () => {
    form.querySelectorAll(".auto-card").forEach(card => {
      const cb = card.querySelector('.sw input[type="checkbox"]');
      if (cb) card.classList.toggle("is-manual", !cb.checked);
    });
  };
  form.addEventListener("change", syncAutoCards);
  syncAutoCards();

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const f = new FormData(form), nguong = {};
    form.querySelectorAll("[data-nguong]").forEach(i => nguong[i.name] = i.value);
    const demBat = f.get("dem_bat") === "on";
    const cgBat = f.get("cg_bat") === "on";
    const body = {
      gio_canh_gac: {bat: cgBat, tu: f.get("cg_tu"), den: f.get("cg_den")},
      gio_dem: {
        bat: demBat,
        tu: f.get("dem_tu"),
        den: f.get("dem_den") || undefined,
        phut: f.get("dem_phut") || undefined,
      },
      gio_cho_an: (f.get("cho_an") || "").split(/[,\s]+/).filter(Boolean),
      tu_dong: {
        dem_lon: demBat,
        canh_gac: cgBat,
        phat_trien: f.get("pt_bat") === "on",
        phat_trien_tu: f.get("pt_tu") || "08:00",
        phat_trien_den: f.get("pt_den") || "09:00",
        an_uong: f.get("an_bat") === "on",
        phut_an: Number(f.get("phut_an") || 30),
        lac_chuong: f.get("lc_bat") === "on",
        lac_chuong_tu: f.get("lc_tu") || "00:00",
        lac_chuong_den: f.get("lc_den") || "23:59",
        suc_khoe: f.get("sk_bat") === "on",
        suc_khoe_tu: f.get("sk_tu") || "00:00",
        suc_khoe_den: f.get("sk_den") || "23:59",
      },
      nguong,
    };
    const {ok, data} = await api("PUT", "/api/cai-dat", body);
    const msg = document.getElementById("kq");
    msg.className = "kq " + (ok ? "ok" : "err");
    msg.textContent = ok ? "Đã lưu cài đặt hệ thống" : (data.loi || ["Lỗi"]).join("; ");
  });
}
