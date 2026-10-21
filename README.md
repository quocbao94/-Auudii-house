# Nhà ở 2 tầng 17 × 7 m – mô hình 3D

Mô hình 3D dựng từ bản vẽ `docs/MatBang_Tang1_Tang2.pdf` (KT-01, mặt bằng tầng 1 – tầng 2, TL 1:100), chạy trực tiếp trên trình duyệt bằng Three.js.

Chạy `npx serve .` rồi mở địa chỉ hiện ra (cần mạng để tải Three.js từ jsDelivr). Mở thẳng file `index.html` thì vẫn xem được, nhưng trình duyệt chặn tải model nội thất từ ổ đĩa.

## Chức năng
- **Chế độ xem**: Toàn nhà · Bỏ mái · Tầng 2 · Tầng 1 (phím `1`–`4`). Ở chế độ tầng có thể bật/tắt mặt cắt tường ở cao độ sàn + 1,3 m (phím `C`).
- **Ngày – đêm**: thanh trượt giờ 0–24h, mặt trời và bầu trời thay đổi theo giờ; nút nhanh Sáng / Chiều / Hoàng hôn / Đêm (phím `N`).
- **Đèn**: bật/tắt đèn trong nhà (phím `L`) và đèn ngoài trời (dây đèn cafe sân thượng, đèn cổng, sân vườn).
- Nhãn tên phòng + diện tích theo bảng diện tích của bản vẽ; tuỳ chọn đổ bóng tiếp xúc (GTAO).

## Chất lượng hình
- Vật liệu ảnh thật PBR (màu + normal + độ nhám) và model nội thất từ [Poly Haven](https://polyhaven.com) (CC0), nằm trong `assets/`. Texture đã thu về 1k, model nén WebP 512 px.
- Cây, bụi, hàng rào cây dựng bằng lá thẻ (instanced) có bóng đổ; cỏ dạng ngọn rung theo gió.
- Hậu kỳ: khử răng cưa MSAA, đổ bóng tiếp xúc GTAO, bloom cho đèn ban đêm; bóng nắng 4096 px.
- Ban ngày đèn trong phòng đóng vai ánh sáng dội (giả lập GI) để nội thất không bị tối khi xem mặt cắt.

## Giả định khi dựng
- Kích thước lấy theo trục; tường bao 200, tường ngăn 120–200; chiều cao tầng 3,3 m; nền tầng 1 tôn cao 0,45 m.
- Cầu thang chữ L: 4 bậc + 4 bậc xoay + 8 bậc, 17 cổ bậc ≈ 194 mm.
- Ký hiệu zigzag được dựng là cửa xếp (theo ghi chú 5).
- Mái thái trên khối phòng ngủ tầng 2, mái bằng có giếng trời trên ô thang, pergola gỗ trên sân thượng: là đề xuất vì bản vẽ chưa có mặt bằng mái.
- Nội thất, vị trí cửa đi, cửa sổ đúng theo phác thảo; sofa sinh hoạt chung và cây xanh là đề xuất.
