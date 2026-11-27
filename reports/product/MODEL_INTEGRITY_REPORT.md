# Hai checkpoint chính thức

Đã đối chiếu selection gốc, role selection, tuning lock và checksum trước khi nạp. Cả hai RF dùng sklearn 1.6.1, classes [0,1], 300 cây, nền trung vị Train đóng gói cùng estimator. So toàn bộ hyperparameter được chọn và thứ tự 17/34 cột với release spec. Kiểm probability hai fixture HTTP cũ ở sai số 10⁻¹² và nhãn chính xác.

| Role | Seed / ngưỡng | SHA-256 |
|---|---|---|
| Primary | 43 / 0,20 | 0a78a47a3a46579cabed3da4d68ed926573fd87df3df45afc9d59e24468ef948 |
| Fallback | 44 / 0,15 | 0ce231574e7d61d7fdedb65b85f00c7cc1ecdd5e02859cb48bb4ea955f9a2897 |

Bundle nội bộ dist/phishshield-models-v1.0.0.zip, 7.477.704 byte, SHA-256 0f9251e315af95968b19aa4fb4144e373a15970ddefbcc2a1ba4a8b134daacfc. Tệp ZIP chứa hai joblib, hai selection.json, selection registry, locked_test và ba tài liệu release. Cài đặt đọc đúng sáu payload có SHA pin sẵn trong clone. Chưa phát hành model trên GitHub Release. [Manifest](../../MODEL_MANIFEST.json) · [Model card](../../MODEL_CARD.md).
