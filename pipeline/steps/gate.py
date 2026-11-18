"""BƯỚC 4 — Cửa chặn: quyết định Release / Hold / Rework.   ★

Test:  pytest tests/test_gate.py -q

Cây quyết định Day 07 (slide Day 09: "Lỗi bắt buộc chặn pipeline; lỗi cảnh báo chuyển người xem"):

  còn ≥ 1 lỗi bắt buộc (severity ERROR)                          -> "Rework"
  không còn lỗi bắt buộc, nhưng tỉ lệ ẢNH còn cảnh báo
      >= cfg["gate"]["warn_ratio_hold"]                          -> "Hold"
  còn lại                                                        -> "Release"

Tỉ lệ cảnh báo = (số ẢNH khác nhau có ≥ 1 cảnh báo) / (tổng số ảnh).  Chú ý:
- chỉ đếm issue có `image` nằm trong `image_stems` (bỏ "<dataset>", "data.yaml");
- bỏ qua ảnh nằm trong `reviewed` (người đã xem, cảnh báo của ảnh đó coi như đã xử lý) — nhưng LỖI BẮT BUỘC thì không bao giờ được bỏ qua;
- mẫu số là số ảnh, không phải số issue.

Trả về dict: decision, n_errors, n_warn_images, n_images, warn_ratio (làm tròn 4 chữ số), reasons (list[str], giải thích bằng tiếng Việt, có số liệu).
"""
from ..common import ERROR, WARN  # noqa: F401

def decide(issues, image_stems, cfg, reviewed=frozenset()):
    # 1. Chuẩn bị tập ảnh trong lô.
    stems = set(image_stems)
    n_images = len(stems)

    # 2. Đếm lỗi bắt buộc.
    n_errors = sum(issue.severity == ERROR for issue in issues)

    # 3. Mỗi ảnh có cảnh báo chỉ được đếm một lần.
    warned_images = {
        issue.image
        for issue in issues
        if issue.severity == WARN
        and issue.image in stems
        and issue.image not in reviewed
    }
    n_warn_images = len(warned_images)

    # 4. Tính tỷ lệ và lấy ngưỡng.
    warn_ratio = n_warn_images / n_images if n_images else 0
    threshold = cfg["gate"]["warn_ratio_hold"]

    # 5. Chọn quyết định theo mức ưu tiên.
    if n_errors > 0:
        decision = "Rework"
        reasons = [f"Còn {n_errors} lỗi bắt buộc."]
    elif n_images > 0 and warn_ratio >= threshold:
        decision = "Hold"
        reasons = [
            f"Còn cảnh báo trên {n_warn_images}/{n_images} ảnh, "
            f"tỷ lệ {warn_ratio:.2%} đạt hoặc vượt ngưỡng {threshold:.2%}."
        ]
    else:
        decision = "Release"
        reasons = [
            f"Không còn lỗi bắt buộc; "
            f"{n_warn_images}/{n_images} ảnh còn cảnh báo."
        ]

    return {
        "decision": decision,
        "n_errors": n_errors,
        "n_warn_images": n_warn_images,
        "n_images": n_images,
        "warn_ratio": round(warn_ratio, 4),
        "reasons": reasons,
    }
