// Trang chạy video: tải video lên, gọi pipeline, hỏi tiến độ mỗi giây.
(() => {
  const form = document.getElementById("form-video");
  const box = document.getElementById("tien-do"), bar = document.getElementById("bar-in");
  const tt = document.getElementById("tt"), kq = document.getElementById("kq-su-kien");
  const btn = form.querySelector("button");
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  const TEN_LOAI = {
    dem_thieu: "Đếm thiếu", dem_du: "Đếm đủ", nguoi_la: "Người lạ",
    nghi_trom: "Nghi trộm", lac_chuong: "Lợn sổng chuồng", nghi_chet: "Nghi chết",
    tho_nhanh: "Thở nhanh", bo_an: "Bỏ ăn", o_an_kem: "Ô ăn kém",
  };
  const TEN_MUC = {khan_cap: "Khẩn cấp", canh_bao: "Cảnh báo", thong_tin: "Thông tin"};
  const NHAN_DU_LIEU = {
    nhip: "Nhịp thở (lần/phút)",
    gio_nam: "Đã nằm (giờ)",
    diem_nghi_van: "Điểm nghi vấn bỏ ăn",
    ty_le_an: "Tỉ lệ ăn",
    dem: "Đếm được",
    dang_ky: "Đăng ký",
    so_nguoi: "Số người",
    khung: "Số khung",
    id_theo_doi: "ID con",
    giay_ngoai: "Ngoài (giây)",
    mock: "Dữ liệu mẫu",
  };

  const SVG_PATHS = {
    alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    trending_down: '<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/>',
    utensils: '<path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    circle_check: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
  };
  const EVENT_ICON = {
    nghi_trom: "alert",
    lac_chuong: "alert",
    nghi_chet: "activity",
    dem_thieu: "trending_down",
    tho_nhanh: "activity",
    bo_an: "utensils",
    o_an_kem: "utensils",
    nguoi_la: "users",
    dem_du: "circle_check",
  };
  function renderEventIcon(loai) {
    const paths = SVG_PATHS[EVENT_ICON[loai] || "bell"] || SVG_PATHS.bell;
    return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
  }
  function fmtGio(s) {
    const str = String(s ?? "");
    if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(str)) {
      return `${str.slice(11, 16)} ${str.slice(8, 10)}/${str.slice(5, 7)}`;
    }
    return str;
  }
  function fmtGiaTri(v) {
    if (v === null || v === undefined) return "—";
    if (v === true) return "có";
    return String(v);
  }

  form.addEventListener("submit", async e => {
    e.preventDefault();
    btn.disabled = true; kq.innerHTML = ""; box.hidden = false; bar.style.width = "0";
    tt.textContent = "Đang tải video lên…";
    try {
      const r = await fetch("/api/chay-video", {method: "POST", body: new FormData(form)});
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { tt.textContent = (d.loi || ["Lỗi tải video"]).join("; "); btn.disabled = false; return; }
      theoDoi(d.job);
    } catch (err) {
      tt.textContent = "Lỗi kết nối máy chủ khi tải video";
      btn.disabled = false;
    }
  });

  async function theoDoi(job) {
    let r, d;
    try {
      r = await fetch(`/api/chay-video/${encodeURIComponent(job)}`);
      d = await r.json().catch(() => ({}));
    } catch (err) {
      tt.textContent = "Lỗi kết nối máy chủ khi kiểm tra tiến độ";
      btn.disabled = false;
      return;
    }
    if (!r.ok) {
      tt.textContent = (d.loi || [`Lỗi máy chủ (${r.status})`]).join("; ");
      btn.disabled = false;
      return;
    }

    const tienDo = Number(d.tien_do || 0);
    const ds = Array.isArray(d.ds) ? d.ds : [];
    bar.style.width = Math.round(tienDo * 100) + "%";
    tt.textContent = d.trang_thai === "dang_chay" ? `Đang phân tích ${Math.round(tienDo * 100)}%`
      : d.trang_thai === "xong" ? `Hoàn tất: ${ds.length} sự kiện${d.che_do === "mock" ? " (MOCK)" : ""}`
      : "Lỗi: " + (d.loi || "Không xác định");
    kq.innerHTML = ds.map(e => {
      const tenLoai = TEN_LOAI[e.loai] || e.loai;
      const entries = e.du_lieu ? Object.entries(e.du_lieu) : [];
      const dataHtml = entries.length
        ? `<div class="ev-data">${entries.map(([k, v]) => `${esc(NHAN_DU_LIEU[k] || k)}: <span class="mono-num">${esc(fmtGiaTri(v))}</span>`).join(" · ")}</div>`
        : "";
      return `
      <div class="ev ${esc(e.muc)}" data-ev="${esc(e.id)}">
        <div class="ev-head">
          <b><span class="ev-ic">${renderEventIcon(e.loai)}</span><span>${esc(tenLoai)}</span></b>
          <span class="chip ${esc(e.muc)}">${esc(TEN_MUC[e.muc] || e.muc)}</span>
        </div>
        <div class="ev-meta"><span class="mono-tag">Ô ${esc(e.o)}</span> · <span class="mono-num">${esc(fmtGio(e.thoi_gian))}</span></div>
        ${e.anh ? `<img class="ev-img" src="/${esc(e.anh)}" alt="Ảnh sự kiện ${esc(tenLoai)}" loading="lazy">` : ""}
        ${dataHtml}
      </div>`;
    }).join("");
    if (d.trang_thai === "dang_chay") setTimeout(() => theoDoi(job), 1000);
    else btn.disabled = false;
  }
})();
