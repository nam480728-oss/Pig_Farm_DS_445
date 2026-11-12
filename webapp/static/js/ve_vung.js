// Công cụ vẽ vùng trên ảnh camera. Toạ độ lưu theo tỉ lệ 0–1 (xem vung.py).
(() => {
  const MA = window.MA_O;
  const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
  const huongDan = document.getElementById("huong-dan");
  const dongCm = document.getElementById("dong-cm"), cmIn = document.getElementById("cm");
  const kq = document.getElementById("kq");

  const MAU = {o: "#10b981", mang_an: "#f59e0b", lc_vung: "#ef4444", lc_vach: "#ef4444", vt: "#3b82f6"};
  const HD = {
    o: "Chạm lần lượt các góc của ô chuồng, rồi bấm “Xong hình”.",
    mang_an: "Chạm các góc của một máng ăn, bấm “Xong hình”. Vẽ thêm máng khác nếu có.",
    lc_vung: "Chạm các góc của vùng NGOÀI ô (nơi lợn bị coi là sổng chuồng), bấm “Xong hình”.",
    lc_vach: "Chạm 2 đầu của vạch mức, rồi chạm 1 điểm ở PHÍA NGOÀI vạch.",
    vt: "Chạm 2 đầu của vật có độ dài đã biết (vd thanh sắt), rồi nhập độ dài cm bên dưới.",
  };

  let anh = new Image(), anhOk = false;
  let tool = "o", cur = [];
  const S = {o: null, mang_an: [], lc: null, vt: null};   // hình đã hoàn thành

  // ----- kích thước canvas theo ảnh -----
  function datKichThuoc() {
    const w = cv.parentElement.clientWidth || 360;
    const ti = anhOk ? anh.naturalHeight / anh.naturalWidth : 9 / 16;
    cv.width = w; cv.height = Math.round(w * ti);
    ve();
  }
  function taiAnh() {
    anhOk = false;
    anh = new Image();
    anh.onload = () => { anhOk = true; document.querySelector(".no-img")?.remove(); datKichThuoc(); };
    anh.src = `/camera/${MA}.jpg?t=${Date.now()}`;
  }

  // ----- vẽ -----
  const px = p => [p[0] * cv.width, p[1] * cv.height];
  function nhanVung(pts, chu, mau) {
    if (!pts || !pts.length) return;
    const [x, y] = px(pts[0]);
    ctx.font = "600 11px Inter, system-ui, sans-serif";
    const padX = 6, h = 18;
    const w = ctx.measureText(chu).width + padX * 2;
    const rx = Math.min(Math.max(4, x - w / 2), cv.width - w - 4);
    const ry = Math.min(Math.max(4, y - h - 6), cv.height - h - 4);
    ctx.fillStyle = mau;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(rx, ry, w, h, 5);
    else ctx.rect(rx, ry, w, h);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.fillText(chu, rx + padX, ry + 13);
  }
  function duongKhep(pts, mau, dong, to) {
    if (!pts.length) return;
    ctx.beginPath();
    pts.map(px).forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    if (dong) ctx.closePath();
    if (to) { ctx.fillStyle = mau + "33"; ctx.fill(); }
    ctx.strokeStyle = mau; ctx.lineWidth = 2.5;
    ctx.setLineDash(dong ? [] : [6, 4]); ctx.stroke(); ctx.setLineDash([]);
  }
  function diem(pts, mau) {
    pts.map(px).forEach(([x, y]) => {
      ctx.beginPath(); ctx.arc(x, y, 5, 0, 7); ctx.fillStyle = mau; ctx.fill();
      ctx.strokeStyle = "#fff"; ctx.lineWidth = 1.75; ctx.stroke();
    });
  }
  function ve() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    if (anhOk) ctx.drawImage(anh, 0, 0, cv.width, cv.height);
    else { ctx.fillStyle = "#26312a"; ctx.fillRect(0, 0, cv.width, cv.height); }
    if (S.o) { duongKhep(S.o, MAU.o, true, true); diem(S.o, MAU.o); nhanVung(S.o, "Ô chuồng", MAU.o); }
    S.mang_an.forEach((d, idx) => {
      duongKhep(d, MAU.mang_an, true, true); diem(d, MAU.mang_an);
      nhanVung(d, `Máng ${idx + 1}`, MAU.mang_an);
    });
    if (S.lc) {
      if (S.lc.kieu === "vung") {
        duongKhep(S.lc.diem, MAU.lc_vung, true, true); diem(S.lc.diem, MAU.lc_vung);
        nhanVung(S.lc.diem, "Vùng lạc chuồng", MAU.lc_vung);
      } else {
        duongKhep(S.lc.diem, MAU.lc_vach, false); diem(S.lc.diem, MAU.lc_vach);
        const [x, y] = px(S.lc.diem_ngoai);
        nhanVung([S.lc.diem_ngoai], "Phía ngoài", MAU.lc_vach);
        diem([S.lc.diem_ngoai], "#fff");
      }
    }
    if (S.vt) {
      duongKhep(S.vt.diem, MAU.vt, false); diem(S.vt.diem, MAU.vt);
      nhanVung(S.vt.diem, `${cmIn.value || 50} cm`, MAU.vt);
    }
    if (cur.length) { duongKhep(cur, MAU[tool], false); diem(cur, MAU[tool]); }
  }

  // ----- thao tác -----
  function chonTool(t) {
    tool = t; cur = [];
    document.querySelectorAll("#tools button").forEach(b => b.classList.toggle("on", b.dataset.tool === t));
    huongDan.textContent = HD[t];
    dongCm.hidden = t !== "vt";
    document.getElementById("btn-xong").hidden = t === "lc_vach" || t === "vt";
    ve();
  }
  document.getElementById("tools").addEventListener("click", e => {
    const b = e.target.closest("button"); if (b) chonTool(b.dataset.tool);
  });

  cv.addEventListener("pointerdown", e => {
    const r = cv.getBoundingClientRect();
    const p = [Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)),
               Math.min(1, Math.max(0, (e.clientY - r.top) / r.height))];
    cur.push(p);
    if (tool === "lc_vach" && cur.length === 3) {
      S.lc = {kieu: "vach", diem: cur.slice(0, 2), diem_ngoai: cur[2]}; cur = [];
    } else if (tool === "vt" && cur.length === 2) {
      S.vt = {diem: cur.slice()}; cur = [];
    }
    ve();
  });

  function xongHinh() {
    if (cur.length < 3) { thongBao("Cần ít nhất 3 điểm", false); return; }
    if (tool === "o") S.o = cur;
    else if (tool === "mang_an") S.mang_an.push(cur);
    else if (tool === "lc_vung") S.lc = {kieu: "vung", diem: cur};
    cur = []; thongBao("", true); ve();
  }
  document.getElementById("btn-xong").onclick = xongHinh;
  document.getElementById("btn-hoan").onclick = () => {
    if (cur.length) cur.pop();
    else if (tool === "mang_an") S.mang_an.pop();
    ve();
  };
  document.getElementById("btn-xoa").onclick = () => {
    cur = [];
    if (tool === "o") S.o = null;
    else if (tool === "mang_an") S.mang_an = [];
    else if (tool.startsWith("lc")) S.lc = null;
    else if (tool === "vt") S.vt = null;
    ve();
  };
  cmIn && cmIn.addEventListener("input", ve);

  function thongBao(msg, ok) { kq.className = "kq " + (ok ? "ok" : "err"); kq.textContent = msg; }

  // ----- lưu / tải -----
  document.getElementById("btn-luu").onclick = async () => {
    if (cur.length) { thongBao("Còn hình đang vẽ dở: bấm “Xong hình” hoặc “Xoá hình này”", false); return; }
    const body = {};
    if (S.o) body.o = S.o;
    if (S.mang_an.length) body.mang_an = S.mang_an;
    if (S.lc) body.lac_chuong = S.lc;
    if (S.vt) body.vat_tham_chieu = {diem: S.vt.diem, cm: parseFloat(cmIn.value)};
    const r = await fetch(`/api/o/${MA}/vung`, {method: "PUT",
      headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
    const d = await r.json().catch(() => ({}));
    thongBao(r.ok ? "✔ Đã lưu cấu hình vùng." : (d.loi || ["Lỗi"]).join("; "), r.ok);
  };
  async function taiVung() {
    const d = await (await fetch(`/api/o/${MA}/vung`)).json();
    S.o = d.o || null; S.mang_an = d.mang_an || []; S.lc = d.lac_chuong || null;
    S.vt = d.vat_tham_chieu ? {diem: d.vat_tham_chieu.diem} : null;
    if (d.vat_tham_chieu) cmIn.value = d.vat_tham_chieu.cm;
    ve();
  }

  document.getElementById("file-anh").addEventListener("change", async e => {
    const f = e.target.files[0]; if (!f) return;
    const fd = new FormData(); fd.append("file", f);
    thongBao("Đang tải…", true);
    const r = await fetch(`/api/o/${MA}/anh-camera`, {method: "POST", body: fd});
    const d = await r.json().catch(() => ({}));
    if (r.ok) { thongBao("✔ Đã đổi ảnh nền.", true); taiAnh(); }
    else thongBao((d.loi || ["Lỗi"]).join("; "), false);
  });

  window.addEventListener("resize", datKichThuoc);
  chonTool("o"); taiVung();
  if (window.CO_ANH) taiAnh(); else datKichThuoc();
})();
