// Màn hình xem camera (kiểu Imou): đồng hồ, tạm dừng, toàn màn hình, vùng AI,
// bật/tắt tự động từng chức năng AI và nhấn kiểm tra thủ công ngay dưới camera.
(function () {
  const $ = id => document.getElementById(id);
  const player = $("player"), clock = $("cam-clock"), paused = $("paused"), liveTag = $("live-tag");
  const kq = $("kq"), aiScan = $("ai-scan"), aiScanText = $("ai-scan-text"), aiResult = $("ai-result");
  const camImg = $("cam-img"), btnResetImg = $("btn-reset-img");
  let dung = false;

  const esc = s => String(s ?? "").replace(/[&<>"']/g, c =>
    ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));

  const p2 = n => String(n).padStart(2, "0");
  function tick() {
    if (dung) return;
    const d = new Date();
    clock.textContent = `${p2(d.getHours())}:${p2(d.getMinutes())}:${p2(d.getSeconds())} ${p2(d.getDate())}/${p2(d.getMonth() + 1)}`;
  }
  tick(); setInterval(tick, 1000);

  // Tạm dừng / tiếp tục
  const btnPause = $("btn-pause");
  const ICON_PAUSE = btnPause.innerHTML;
  const ICON_PLAY = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4.5v15a1 1 0 0 0 1.5.86l12-7.5a1 1 0 0 0 0-1.72l-12-7.5A1 1 0 0 0 7 4.5Z"/></svg>';
  btnPause.addEventListener("click", () => {
    dung = !dung;
    player.classList.toggle("is-paused", dung);
    paused.hidden = !dung;
    liveTag.classList.toggle("off", dung);
    btnPause.innerHTML = dung ? ICON_PLAY : ICON_PAUSE;
    btnPause.setAttribute("aria-label", dung ? "Tiếp tục" : "Tạm dừng");
    if (!dung) {
      if (camImg) camImg.src = `/camera/${window.MA_O}.jpg?t=${Date.now()}`;
      if (btnResetImg) btnResetImg.hidden = true;
      tick();
    }
  });

  if (btnResetImg && camImg) {
    btnResetImg.addEventListener("click", () => {
      camImg.src = `/camera/${window.MA_O}.jpg?t=${Date.now()}`;
      btnResetImg.hidden = true;
    });
  }

  // Toàn màn hình
  function fullscreen() {
    if (document.fullscreenElement || document.webkitFullscreenElement) {
      (document.exitFullscreen || document.webkitExitFullscreen).call(document);
    } else {
      const fn = player.requestFullscreen || player.webkitRequestFullscreen;
      if (fn) fn.call(player);
    }
  }
  $("btn-fs").addEventListener("click", fullscreen);
  $("btn-fs2").addEventListener("click", fullscreen);
  player.addEventListener("dblclick", fullscreen);

  // Bật / tắt lớp vùng AI
  const btnZone = $("btn-zone"), zones = $("zones");
  btnZone.addEventListener("click", () => {
    const on = !btnZone.classList.contains("on");
    btnZone.classList.toggle("on", on);
    btnZone.setAttribute("aria-pressed", String(on));
    zones.style.display = on ? "" : "none";
  });

  // Chụp ảnh: khi chưa có hình thì báo
  $("btn-snap").addEventListener("click", e => {
    if (e.currentTarget.getAttribute("aria-disabled") === "true") {
      e.preventDefault();
      kq.className = "kq err"; kq.textContent = "Chưa có hình camera để chụp.";
    }
  });

  // Cập nhật hình camera (ảnh hoặc video -> khung đầu)
  $("file-cam").addEventListener("change", async e => {
    const f = e.target.files[0];
    if (!f) return;
    kq.className = "kq"; kq.textContent = "Đang tải lên…";
    const fd = new FormData(); fd.append("file", f);
    const r = await fetch(`/api/o/${window.MA_O}/anh-camera`, {method: "POST", body: fd});
    let data = {}; try { data = await r.json(); } catch (_) {}
    if (r.ok) { location.reload(); return; }
    kq.className = "kq err"; kq.textContent = (data.loi || ["Lỗi tải lên"]).join("; ");
  });

  // ---------- Bật / Tắt chế độ Tự động ngay trên từng thẻ AI ----------
  document.addEventListener("change", async e => {
    const cb = e.target.closest("[data-toggle-auto]");
    if (!cb) return;
    const key = cb.dataset.toggleAuto;
    const bat = cb.checked;
    const card = cb.closest(".ai-card");
    if (card) {
      card.classList.toggle("is-auto", bat);
      card.classList.toggle("is-manual", !bat);
      const badge = card.querySelector("[data-badge]");
      const lich = card.dataset.lich || "";
      if (badge) {
        badge.textContent = bat ? `Tự động ${lich}` : "Thủ công · Đã tắt tự động";
      }
    }
    const r = await fetch("/api/cai-dat", {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({tu_dong: {[key]: bat}}),
    });
    if (r.ok) {
      kq.className = "kq ok";
      kq.textContent = bat
        ? "✔ Đã bật chế độ tự động theo lịch."
        : "✔ Đã tắt tự động – nhấn nút trên thẻ để kiểm tra thủ công.";
    }
  });

  // ---------- Nhấn kiểm tra AI thủ công ----------
  const NHAN_QUET = {
    dem_lon: "🔢 AI đang đếm số lượng lợn trong ô…",
    phat_trien: "📈 AI đang đo kích thước & tính độ phát triển của đàn…",
    phat_hien_nguoi: "🛡️ AI đang quét người lạ & kiểm tra an ninh…",
    an_uong: "🍽️ AI đang phân tích hoạt động tại máng ăn…",
    lac_chuong: "🐖 AI đang kiểm tra ranh giới & vùng sổng chuồng…",
    suc_khoe: "💓 AI đang phân tích nhịp thở & vận động của đàn…",
  };

  async function lamMoiTinNhan() {
    const r = await fetch(location.href);
    if (!r.ok) return;
    const doc = new DOMParser().parseFromString(await r.text(), "text/html");
    for (const id of ["msgs", "cam-stats"]) {
      const moi = doc.getElementById(id), cu = $(id);
      if (moi && cu) cu.innerHTML = moi.innerHTML;
    }
  }

  async function chayKiemTra(tacVu, canhBao = false, btnEl = null) {
    if (btnEl) btnEl.disabled = true;
    if (aiScan) {
      aiScanText.textContent = NHAN_QUET[tacVu] || "🔍 AI đang phân tích…";
      aiScan.hidden = false;
    }
    try {
      const [r] = await Promise.all([
        fetch(`/api/o/${window.MA_O}/kiem-tra`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({tac_vu: tacVu, canh_bao: canhBao}),
        }),
        new Promise(res => setTimeout(res, 420)),
      ]);
      const d = await r.json();
      if (!r.ok || !d.ok) {
        kq.className = "kq err";
        kq.textContent = (d.loi || ["Không thể thực hiện kiểm tra"]).join("; ");
        return;
      }
      // Cập nhật khung hình camera với ảnh đã khoanh AI
      if (d.anh && camImg) {
        camImg.src = `/${d.anh}?t=${Date.now()}`;
        if (btnResetImg) btnResetImg.hidden = false;
      }
      // Cập nhật số đếm trực tiếp trên camera nếu là tác vụ đếm lợn
      if (typeof d.dem === "number") {
        const pill = $("live-count-pill");
        if (pill) pill.textContent = `🐖 AI đếm: ${d.dem}/${d.dang_ky}`;
        const stDem = $("stat-dem");
        if (stDem) stDem.textContent = String(d.dem);
      }
      hienThiKetQua(d, canhBao);
      if (d.su_kien_id) {
        await lamMoiTinNhan();
      }
    } finally {
      if (aiScan) aiScan.hidden = true;
      if (btnEl) btnEl.disabled = false;
    }
  }

  function hienThiKetQua(d, canhBao) {
    if (!aiResult) return;
    const chipCls = d.trang_thai === "khan_cap" ? "khan_cap" : (d.trang_thai === "canh_bao" ? "canh_bao" : "ok");
    const kvHtml = (d.chi_tiet || []).map(([k, v]) =>
      `<div class="kv"><span>${esc(k)}</span><b>${esc(v)}</b></div>`
    ).join("");

    let ptHtml = "";
    if (d.bao_cao) {
      const bc = d.bao_cao;
      const coiHtml = (bc.con_coi || []).map(c =>
        `<span class="chip canh_bao">🐖 ${esc(c.con_id)}: ${esc(c.kg)} kg (${c.chenh_tb > 0 ? "+" : ""}${esc(c.chenh_tb)} kg)</span>`
      ).join("");
      const lonHtml = (bc.con_lon_nhanh || []).map(c =>
        `<span class="chip ok">🐖 ${esc(c.con_id)}: ${esc(c.kg)} kg (+${esc(c.chenh_tb)} kg)</span>`
      ).join("");
      ptHtml = `
        ${bc.bieu_do ? `<div class="ai-chart">${bc.bieu_do}</div>` : ""}
        ${coiHtml || lonHtml ? `<div class="chips" style="margin-top:8px">${coiHtml}${lonHtml}</div>` : ""}
        <a class="more" href="${esc(bc.link)}" style="margin-top:8px">📊 Xem báo cáo chi tiết đàn ${esc(bc.dan)} →</a>
      `;
    }

    aiResult.className = `ai-result ${chipCls}`;
    aiResult.hidden = false;
    aiResult.innerHTML = `
      <div class="ai-res-head">
        <div>
          <span class="chip ${chipCls}">${esc(d.nhan_trang_thai)}</span>
          <h3>${esc(d.tieu_de)}</h3>
        </div>
        <button type="button" class="b-x ai-res-close" aria-label="Đóng kết quả">✕</button>
      </div>
      <p class="ai-res-summary">${esc(d.tom_tat)}</p>
      <div class="ai-res-kv">${kvHtml}</div>
      ${ptHtml}
      ${d.anh ? `<img class="ev-img" src="/${esc(d.anh)}" alt="Ảnh kết quả phân tích AI">` : ""}
      <div class="ai-res-actions">
        <button type="button" data-rerun="${esc(d.tac_vu)}" data-alert="0">🔄 Kiểm tra lại</button>
        <button type="button" data-rerun="${esc(d.tac_vu)}" data-alert="${canhBao ? "0" : "1"}">
          ${canhBao ? "✅ Xem kết quả bình thường" : "🧪 Thử tình huống cảnh báo"}
        </button>
      </div>
    `;
    aiResult.scrollIntoView({behavior: "smooth", block: "nearest"});
  }

  document.addEventListener("click", e => {
    const runBtn = e.target.closest("[data-run]");
    if (runBtn) {
      chayKiemTra(runBtn.dataset.run, false, runBtn);
      return;
    }
    const rerunBtn = e.target.closest("[data-rerun]");
    if (rerunBtn) {
      chayKiemTra(rerunBtn.dataset.rerun, rerunBtn.dataset.alert === "1", rerunBtn);
      return;
    }
    if (e.target.closest(".ai-res-close") && aiResult) {
      aiResult.hidden = true;
    }
  });

  // Có sự kiện mới từ banner: làm mới tin nhắn và thông số
  document.addEventListener("co-su-kien-moi", lamMoiTinNhan);
})();
