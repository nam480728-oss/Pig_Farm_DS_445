// Trang chạy video: tải video lên, gọi pipeline, hỏi tiến độ mỗi giây.
(() => {
  const form = document.getElementById("form-video");
  const box = document.getElementById("tien-do"), bar = document.getElementById("bar-in");
  const tt = document.getElementById("tt"), kq = document.getElementById("kq-su-kien");
  const btn = form.querySelector("button");
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  const TEN_LOAI = {
    dem_thieu: "📉 Đếm thiếu", dem_du: "✅ Đếm đủ", nguoi_la: "👤 Người lạ",
    nghi_trom: "🚨 Nghi trộm", lac_chuong: "🐖 Lợn sổng chuồng", nghi_chet: "⚠️ Nghi chết",
    tho_nhanh: "💨 Thở nhanh", bo_an: "🍽️ Bỏ ăn", o_an_kem: "🥣 Ô ăn kém",
  };
  const TEN_MUC = {khan_cap: "Khẩn cấp", canh_bao: "Cảnh báo", thong_tin: "Thông tin"};

  form.addEventListener("submit", async e => {
    e.preventDefault();
    btn.disabled = true; kq.innerHTML = ""; box.hidden = false; bar.style.width = "0";
    tt.textContent = "Đang tải video lên…";
    const r = await fetch("/api/chay-video", {method: "POST", body: new FormData(form)});
    const d = await r.json().catch(() => ({}));
    if (!r.ok) { tt.textContent = (d.loi || ["Lỗi"]).join("; "); btn.disabled = false; return; }
    theoDoi(d.job);
  });

  async function theoDoi(job) {
    const d = await (await fetch(`/api/chay-video/${job}`)).json();
    bar.style.width = Math.round(d.tien_do * 100) + "%";
    tt.textContent = d.trang_thai === "dang_chay" ? `Đang phân tích… ${Math.round(d.tien_do * 100)}%`
      : d.trang_thai === "xong" ? `✔ Hoàn tất: ${d.ds.length} sự kiện${d.che_do === "mock" ? " (MOCK)" : ""}`
      : "Lỗi: " + d.loi;
    kq.innerHTML = d.ds.map(e => `
      <div class="ev ${esc(e.muc)}" data-ev="${esc(e.id)}"><div class="ev-head"><b>${esc(TEN_LOAI[e.loai] || e.loai)}</b>
        <span class="chip ${esc(e.muc)}">${esc(TEN_MUC[e.muc] || e.muc)}</span></div>
        <div class="ev-meta">Ô ${esc(e.o)} · ${esc(e.thoi_gian.slice(11, 16))}</div>
        ${e.anh ? `<img class="ev-img" src="/${esc(e.anh)}" alt="">` : ""}
        <div class="ev-data">${Object.entries(e.du_lieu).map(([k, v]) => esc(k) + ": " + esc(v)).join(" · ")}</div></div>`).join("");
    if (d.trang_thai === "dang_chay") setTimeout(() => theoDoi(job), 1000);
    else btn.disabled = false;
  }
})();
