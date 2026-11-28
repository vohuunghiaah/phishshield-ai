# Nguồn và cách áp dụng skill

Đã kiểm danh mục skill trước khi cài. Hai bộ công cụ hiện xuất hiện trong danh mục Codex. Trong lúc triển khai, nhóm đọc trực tiếp README và SKILL.md tại commit khóa. Bản chạy sản phẩm không nạp các công cụ thiết kế.

| Công cụ | Nguồn và phiên bản | Việc đã thực hiện |
|---|---|---|
| Impeccable | Skill 4.11.1, engine 0.1.31, commit `2fc5e1459efbbf06d92c7306517c286bf12490cf`. [Nguồn](https://github.com/pbakaus/impeccable/tree/2fc5e1459efbbf06d92c7306517c286bf12490cf) | Cài thư mục skill chính thức bằng helper Codex. Kiểm tra launcher Windows và checksum binary. Chạy context và detector trên trang render bằng Chromium. Người dùng đã duyệt hai agent đánh giá độc lập. Đánh giá A phát hiện overlay tablet, điều hướng khó đọc và hai lựa chọn chế độ cùng xuất hiện. Đánh giá B đo DOM, focus, contrast và đối chiếu các lần render. |
| UI/UX Pro Max | Commit `11ca2b3bdd555649f278ee348c32a9302b24dcf1`, CLI trong source 2.5.0. [Nguồn](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/11ca2b3bdd555649f278ee348c32a9302b24dcf1) | Cài từ commit qua phương án GitHub CLI trong README, scope user cho Codex. Đã chạy search.py với brief và `--design-system`, rồi tìm riêng focus, nhãn và touch target trong miền UX. Kết quả tự động thiên về landing page tối màu. Giữ khuyến nghị về khả năng đọc, nhãn và bàn phím; chọn bảng màu sáng theo brief. |

Font Be Vietnam Pro lấy từ [Google Fonts tại commit đã dùng](https://github.com/google/fonts/tree/5026800714d07231937d92eb4cceabf06e05d74e/ofl/bevietnampro).
