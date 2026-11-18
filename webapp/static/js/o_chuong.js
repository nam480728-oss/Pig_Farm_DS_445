// Quản lý ô chuồng: Thêm ô chuồng mới khi mở rộng trang trại và xóa ô chuồng
(function () {
  function setBoxOpen(open) {
    const boxThem = document.getElementById("box-them-o");
    const btnToggle = document.getElementById("btn-toggle-them");
    if (boxThem) boxThem.hidden = !open;
    if (btnToggle) btnToggle.setAttribute("aria-expanded", String(open));
    return boxThem;
  }

  document.addEventListener("click", async (e) => {
    const btnToggle = e.target.closest("#btn-toggle-them");
    if (btnToggle) {
      const boxThem = document.getElementById("box-them-o");
      if (!boxThem) return;
      const open = boxThem.hidden;
      setBoxOpen(open);
      if (open) {
        boxThem.scrollIntoView({ behavior: "smooth", block: "nearest" });
        const inpMa = document.getElementById("inp-ma");
        if (inpMa) inpMa.focus();
      }
      return;
    }

    if (e.target.closest("#btn-dong-them")) {
      setBoxOpen(false);
      return;
    }

    if (e.target.closest("#btn-huy-them")) {
      setBoxOpen(false);
      const formThem = document.getElementById("form-them-o");
      const kqThem = document.getElementById("kq-them-o");
      if (formThem) formThem.reset();
      if (kqThem) kqThem.textContent = "";
      return;
    }

    // Xóa ô chuồng
    const btnDel = e.target.closest("[data-xoa-o]");
    if (!btnDel) return;

    const ma = btnDel.dataset.xoaO;
    const ten = btnDel.dataset.ten || `Ô ${ma}`;

    if (!confirm(`Bạn có chắc chắn muốn xóa ${ten} (Ô ${ma}) khỏi hệ thống trang trại?`)) {
      return;
    }

    btnDel.disabled = true;
    try {
      const r = await fetch(`/api/o-chuong/${encodeURIComponent(ma)}`, {
        method: "DELETE",
      });
      const d = await r.json().catch(() => ({}));

      if (!r.ok || !d.ok) {
        alert((d.loi || ["Không thể xóa ô chuồng này"]).join("\n"));
        btnDel.disabled = false;
        return;
      }

      const card = btnDel.closest("[data-pen-card]");
      if (card) {
        card.style.opacity = "0.3";
        card.style.transform = "scale(0.95)";
        setTimeout(() => {
          location.reload();
        }, 300);
      } else {
        location.reload();
      }
    } catch (err) {
      alert("Lỗi kết nối máy chủ");
      btnDel.disabled = false;
    }
  });

  document.addEventListener("submit", async (e) => {
    const formThem = e.target.closest("#form-them-o");
    if (!formThem) return;
    e.preventDefault();

    const btnSubmitThem = document.getElementById("btn-submit-them");
    const kqThem = document.getElementById("kq-them-o");
    if (btnSubmitThem) btnSubmitThem.disabled = true;
    if (kqThem) {
      kqThem.className = "kq";
      kqThem.textContent = "Đang khởi tạo ô chuồng mới…";
    }

    try {
      const fd = new FormData(formThem);
      const r = await fetch("/api/o-chuong", {
        method: "POST",
        body: fd,
      });
      const d = await r.json().catch(() => ({}));

      if (!r.ok || !d.ok) {
        if (kqThem) {
          kqThem.className = "kq err";
          kqThem.textContent = (d.loi || ["Lỗi khi tạo ô chuồng"]).join("; ");
        }
        return;
      }

      if (kqThem) {
        kqThem.className = "kq ok";
        kqThem.textContent = `Đã thêm Ô ${d.ma} (${d.ten})`;
      }
      formThem.reset();
      setTimeout(() => {
        location.reload();
      }, 600);
    } catch (err) {
      if (kqThem) {
        kqThem.className = "kq err";
        kqThem.textContent = "Lỗi kết nối máy chủ";
      }
    } finally {
      if (btnSubmitThem) btnSubmitThem.disabled = false;
    }
  });
})();
